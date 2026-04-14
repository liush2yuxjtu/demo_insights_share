# Claude Code Session Export

**Source:** claude -p (non-interactive)  
**Mode:** A / WITHOUT insights-wiki skill  
**Time:** 2026-04-14 15:19  
**Skills installed:** (none — ~/.claude/skills/insights-wiki removed)  

---

## User

请严格按顺序执行三步。第一步：运行 !pwd 打印当前工作目录。第二步：运行 !ls -la ~/.claude/skills/ 展示已安装的 skill 列表（若目录不存在也要显示该事实）。第三步：回答 — 我们的 checkout API 正在超时，postgres 在午餐高峰拒绝新连接，应该如何诊断与修复？请给出可执行的 SQL 与代码片段。

---

## Assistant

## 第一步：当前工作目录

```
/Users/m1/projects/demo_insights_share
```

## 第二步：已安装 skill 列表

目录 `~/.claude/skills/` **存在**，共 64 个条目，包含 `algorithmic-art`、`daily-report`、`insights-wiki.bak.23559`、`playwright-browser-automation`（symlink）等，详见上方输出。

---

## 第三步：Checkout API 超时 / Postgres 午高峰拒绝连接 — 诊断与修复

### 一、快速诊断

**1. 查当前连接状态（立即执行）**

```sql
-- 总连接数 vs 上限
SELECT count(*) AS total,
       max_conn,
       max_conn - count(*) AS available
FROM pg_stat_activity,
     (SELECT setting::int AS max_conn FROM pg_settings WHERE name = 'max_connections') s
GROUP BY max_conn;

-- 按状态分组，找出哪类连接占满了池
SELECT state,
       wait_event_type,
       wait_event,
       count(*) AS cnt,
       max(now() - state_change) AS max_age
FROM pg_stat_activity
WHERE datname = 'your_db_name'   -- 换成实际库名
GROUP BY state, wait_event_type, wait_event
ORDER BY cnt DESC;
```

**2. 找出长时间 idle-in-transaction（最危险）**

```sql
SELECT pid, usename, application_name, client_addr,
       state, wait_event,
       now() - query_start AS query_age,
       now() - state_change AS state_age,
       left(query, 120) AS query_snippet
FROM pg_stat_activity
WHERE state IN ('idle in transaction', 'active')
  AND now() - state_change > interval '30 seconds'
ORDER BY state_age DESC;
```

**3. 找锁等待链**

```sql
SELECT blocked.pid         AS blocked_pid,
       blocked.query       AS blocked_query,
       blocking.pid        AS blocking_pid,
       blocking.query      AS blocking_query,
       now() - blocked.query_start AS wait_duration
FROM pg_stat_activity AS blocked
JOIN pg_stat_activity AS blocking
  ON blocking.pid = ANY(pg_blocking_pids(blocked.pid))
ORDER BY wait_duration DESC;
```

---

### 二、紧急止血（高峰期立刻做）

**终止 idle-in-transaction 超过 60s 的连接**

```sql
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = 'your_db_name'
  AND state = 'idle in transaction'
  AND now() - state_change > interval '60 seconds';
```

**终止指定 pid（谨慎）**

```sql
SELECT pg_terminate_backend(12345);
```

---

### 三、根因修复

#### 3.1 连接池上限太低 / 没有连接池

```ini
# postgresql.conf（需要 reload，不需要重启）
max_connections = 200          # 根据内存调整，建议 RAM/4MB
```

```bash
psql -c "SELECT pg_reload_conf();"
```

**强烈建议前置 PgBouncer（transaction 模式）：**

```ini
# pgbouncer.ini 关键参数
[databases]
your_db = host=127.0.0.1 port=5432 dbname=your_db

[pgbouncer]
pool_mode = transaction          # checkout API 用 transaction 模式最合适
max_client_conn = 2000           # 允许 API 侧建多少连接
default_pool_size = 30           # 实际打到 PG 的连接数
min_pool_size = 5
reserve_pool_size = 10
reserve_pool_timeout = 3
server_idle_timeout = 600
```

#### 3.2 应用层连接池配置（Python/SQLAlchemy 示例）

```python
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    "postgresql+psycopg2://user:pass@localhost/your_db",
    poolclass=QueuePool,
    pool_size=10,          # 常驻连接数（与 pgbouncer pool_size 对齐）
    max_overflow=20,       # 峰值最多额外开 20 个
    pool_timeout=5,        # 等不到连接 5s 后抛出异常而非无限等
    pool_pre_ping=True,    # 每次取连接先 ping，避免僵尸连接
    pool_recycle=1800,     # 30min 强制回收，防止 idle 超时断开
)
```

#### 3.3 设置 idle-in-transaction 超时（防止事务泄漏）

```sql
-- 全局（需要 reload）
ALTER SYSTEM SET idle_in_transaction_session_timeout = '30s';
SELECT pg_reload_conf();

-- 或者只对 checkout 账号生效
ALTER ROLE checkout_user SET idle_in_transaction_session_timeout = '15s';

-- 同时设置语句超时，防止慢查询堆积
ALTER ROLE checkout_user SET statement_timeout = '10s';
```

#### 3.4 checkout 核心查询加索引（常见慢查询点）

```sql
-- 查高频慢查询
SELECT query,
       calls,
       round(total_exec_time::numeric / calls, 2) AS avg_ms,
       round(total_exec_time::numeric, 2)          AS total_ms,
       rows
FROM pg_stat_statements
WHERE calls > 100
ORDER BY avg_ms DESC
LIMIT 20;

-- 典型：订单库存锁行
CREATE INDEX CONCURRENTLY idx_orders_status_created
    ON orders(status, created_at)
    WHERE status IN ('pending', 'processing');

-- 确认是否走到索引
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT * FROM orders WHERE status = 'pending' AND created_at > now() - interval '1h';
```

---

### 四、监控告警（预防下次）

```sql
-- 创建视图方便 Grafana 拉取
CREATE OR REPLACE VIEW v_pg_conn_stats AS
SELECT now()                                          AS ts,
       count(*)                                       AS total_conn,
       count(*) FILTER (WHERE state = 'active')       AS active,
       count(*) FILTER (WHERE state LIKE 'idle%')     AS idle,
       count(*) FILTER (WHERE wait_event_type = 'Lock') AS lock_waiting,
       (SELECT setting::int FROM pg_settings WHERE name = 'max_connections') AS max_conn
FROM pg_stat_activity
WHERE datname = current_database();
```

**告警阈值建议：**

| 指标 | 警告 | 严重 |
|------|------|------|
| `total_conn / max_conn` | > 70% | > 85% |
| `idle in transaction` 数量 | > 20 | > 50 |
| `lock_waiting` 数量 | > 10 | > 30 |
| 平均查询延迟 | > 500ms | > 2s |

---

### 五、排查顺序总结

```
午高峰超时
  └─ 步骤1: 查 pg_stat_activity → 连接耗尽? idle-in-transaction?
      ├─ 是"连接耗尽" → 立即加 PgBouncer + 调 max_connections
      ├─ 是"idle-in-transaction" → pg_terminate_backend + 设 timeout
      └─ 是"锁等待" → 找 blocking_pid → 终止或优化事务顺序
```
