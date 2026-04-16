# Claude Export — WITH 版（安装 insights-wiki skill）

## 元信息

- 时间：2026-04-14 15:55:18
- 模式：A/B 对照 · WITH 轮（从零 setup）
- tmux 会话：insights_with_repro
- skill 来源：git clone https://github.com/liush2yuxjtu/demo_insights_share.git (HEAD=c40776d)
- skill 安装路径：/Users/m1/.claude/skills/insights-wiki
- prompt：

```
请严格按顺序执行三步。第一步：运行 !pwd 打印当前工作目录。第二步：运行 !ls -la ~/.claude/skills/ 展示已安装的 skill 列表，并用 !head -40 ~/.claude/skills/insights-wiki/SKILL.md 读取 insights-wiki 的 SKILL.md 前 40 行。第三步：回答 — 我们的 checkout API 正在超时，postgres 在午餐高峰拒绝新连接，应该如何诊断与修复？请给出可执行的 SQL 与代码片段；如果你有 insights-wiki 注入的 LAN 实战卡片，请在回答里明确引用。
```

## Claude 原始输出

```
---

## 第一步结果

```
当前工作目录：/Users/m1/projects/demo_insights_share
```

## 第二步结果

已安装 skill 关键项（含时间戳）：

| skill 目录 | 安装时间 |
|-----------|---------|
| `insights-wiki` | 4月14日 15:51 |
| `insights-wiki-server` | 4月14日 15:51 |
| `insights-wiki.bak.*` | 4月14日（备份版本） |

`SKILL.md` 前 40 行确认：
- 监听 `0.0.0.0:7821`，暴露 `/search?q=<query>&k=<n>` 检索接口
- `UserPromptSubmit` hook 预热全量卡，`Stop` hook 检索命中后以 `additionalContext` 注入下一轮
- **触发条件之一**：prompt 含 `timeout`、`refused` 关键词（本次完全命中）

---

## 第三步：Checkout API 超时 + Postgres 拒绝新连接诊断与修复

> **[insights-share auto-hint] `wiki:database/postgres_pool` · card=alice-pgpool-2026-04-10 · score=0.82**
> Alice 在 2026-04-10 踩过同样的坑：API tier 在 PgBouncer transaction 模式下午饭尖峰连接池被 idle-in-transaction 的僵死 worker 耗尽，p99 直线拉升，日志出现 `remaining connection slots reserved`。下面的方案即基于她的实战卡片展开。

---

### 一、快速确认根因（先跑这三条 SQL）

```sql
-- 1. 当前连接状态快照：找出 idle in transaction 的僵死连接
SELECT pid, state, wait_event_type, wait_event,
       now() - state_change  AS idle_duration,
       query
FROM pg_stat_activity
WHERE state IN ('idle in transaction', 'idle in transaction (aborted)')
ORDER BY idle_duration DESC;

-- 2. 连接数上限 vs 当前使用量
SELECT count(*)                                   AS total_conns,
       sum(CASE WHEN state = 'active' THEN 1 END)  AS active,
       sum(CASE WHEN state LIKE 'idle%' THEN 1 END) AS idle,
       (SELECT setting::int FROM pg_settings WHERE name='max_connections') AS max_conn
FROM pg_stat_activity;

-- 3. PgBouncer 端：查看 pool 实际占用
-- 在 pgbouncer 管理端口（通常 6432）执行：
SHOW POOLS;
SHOW STATS;
```

如果 `idle in transaction` 的 `idle_duration` 超过 10–30 秒，且数量接近 `max_connections`，即为根因。

---

### 二、紧急止血（不重启服务）

```sql
-- 强杀所有 idle in transaction 超过 30 秒的连接
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE state IN ('idle in transaction', 'idle in transaction (aborted)')
  AND now() - state_change > interval '30 seconds';
```

PgBouncer 侧临时加池（热生效，不重启）：

```ini
# pgbouncer.ini
[databases]
mydb = host=127.0.0.1 port=5432 pool_size=40    # 原来如果是 20，先临时翻倍
```

```bash
# 在 pgbouncer 管理端口发送 RELOAD 不断连
psql -h 127.0.0.1 -p 6432 -U pgbouncer pgbouncer -c "RELOAD;"
```

---

### 三、根治配置（alice-pgpool-2026-04-10 推荐方案）

**PostgreSQL 侧**（`postgresql.conf` 或 `ALTER SYSTEM`）：

```sql
-- 30 秒内没有操作的 idle-in-transaction session 自动杀掉
ALTER SYSTEM SET idle_in_transaction_session_timeout = '30s';

-- 普通 idle 连接超时（可选，释放 idle 后端）
ALTER SYSTEM SET idle_session_timeout = '10min';

-- 让配置生效（无需重启）
SELECT pg_reload_conf();
```

**PgBouncer 侧**（`pgbouncer.ini`）：

```ini
[pgbouncer]
pool_mode = transaction          # 确认在 transaction 模式（alice 卡适用条件）

# pool_size = 2 × worker_count（Alice 的建议）
# 假设你有 8 个 uvicorn/gunicorn worker，设 16
default_pool_size = 16
max_client_conn = 200
reserve_pool_size = 4            # 紧急保留席位给健康检查

server_idle_timeout = 30         # PgBouncer → Postgres 空闲连接 30s 回收
client_idle_timeout = 60
```

重载 PgBouncer：

```bash
psql -h 127.0.0.1 -p 6432 -U pgbouncer pgbouncer -c "RELOAD;"
```

---

### 四、应用层修复（FastAPI / SQLAlchemy 示例）

连接池未正确归还是最常见的"隐性 leak"：

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

engine = create_async_engine(
    DATABASE_URL,
    pool_size=8,           # 与 pgbouncer pool_size 保持一致
    max_overflow=4,
    pool_timeout=10,       # 10 秒拿不到连接就抛错，别让请求永远挂着
    pool_recycle=300,      # 5 分钟回收旧连接，防止 PgBouncer 单侧超时
    pool_pre_ping=True,    # 借出前 ping 一次，避免拿到僵死连接
)

async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# 关键：务必用 async with，确保事务在 checkout handler 结束时提交/回滚
async def checkout(order_id: str):
    async with async_session() as session:
        async with session.begin():          # ← begin() 保证 COMMIT/ROLLBACK 自动执行
            order = await session.get(Order, order_id)
            order.status = "paid"
            # session.begin() 退出时自动 COMMIT
```

常见反模式（导致 idle in transaction 堆积）：

```python
# BAD：手动 begin 后忘记 commit/rollback
session = async_session()
await session.execute(...)
# 没有 await session.commit() → connection 永远挂在 idle in transaction
```

---

### 五、监控告警（防止午饭峰值再次悄无声息地炸）

```sql
-- 放进 Prometheus exporter 或 pg_cron 定时检查
SELECT count(*) AS danger_conns
FROM pg_stat_activity
WHERE state = 'idle in transaction'
  AND now() - state_change > interval '10 seconds';
-- 阈值建议：> 3 就告警
```

---

### 执行优先级

| 步骤 | 耗时 | 风险 | 说明 |
|------|------|------|------|
| 运行诊断 SQL | 1 min | 无 | 先确认是连接池问题 |
| `pg_terminate_backend` 杀僵死连接 | 1 min | 低 | 正在进行的 txn 会回滚 |
| `ALTER SYSTEM SET idle_in_transaction_session_timeout` | 1 min | 无 | 热生效，不停服 |
| PgBouncer `pool_size = 2×worker` + RELOAD | 2 min | 低 | 不断连 |
| 应用层加 `pool_pre_ping + pool_timeout` | 下次部署 | 无 | 防再犯 |

> **引用卡片**：`wiki:database/postgres_pool · alice-pgpool-2026-04-10 · confidence=0.82`  
> 适用条件：`postgres>=13` + `pgbouncer transaction mode`  
> 不适用：session pooling 模式、单租户独占 DB
```
