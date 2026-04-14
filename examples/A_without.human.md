 ▐▛███▜▌   Claude Code v2.1.104
▝▜█████▛▘  Opus 4.6 (1M context) · Claude Max
  ▘▘ ▝▝    ~/projects/demo_insights_share/insights-share/demo_codes

  /remote-control is active · Code in CLI or at 
  https://claude.ai/code/session_01MhbFNrch3Wtf1VRwZYdoPx

❯ 我们的 checkout API 正在超时，postgres                                        
  在午餐高峰拒绝新连接，应该如何诊断与修复？请给出可执行的 SQL 与代码片段。若有 
   insights-wiki 注入的 LAN 实战卡片请明确引用。                                

⏺ Skill(insights-wiki)
  ⎿  Successfully loaded skill · 3 tools allowed
  ⎿  Allowed by PermissionRequest hook

  Listed 1 directory (ctrl+o to expand)

⏺ Bash(curl -s http://localhost:7821/search?q=postgres+connection+pool+exhaustio
      n+checkout+timeout\&k=3 2>/dev/null || curl -s
      http://127.0.0.1:7821/search?q=postgres+…)
  ⎿  (eval):1: no matches found: http://localhost:7821/search?q=postgres+co
     nnection+pool+exhaustion+checkout+timeout&k=3
     (eval):1: no matches found: http://127.0.0.1:7821/search?q=postgres+co
     … +2 lines (ctrl+o to expand)

  Read 1 file (ctrl+o to expand)

⏺ 命中 LAN 实战卡片。直接基于这条线索给出诊断方案。

  ---
  引用 LAN wiki 卡片

  ▎ wiki:alice-pgpool-2026-04-10 · postgres / connection-pool / prod-incident
  ▎ Alice 在 4 月 10 日爆出同类场景：突发流量下连接池耗尽，checkout 开始超时 → 
  ▎ 被 Postgres 拒绝新连接。

  ---
  第一步：确认症状（直接 SQL）

  -- 1. 当前连接总数 vs max_connections
  SELECT
    count(*)                        AS current_connections,
    max_conn.setting::int           AS max_connections,
    round(count(*) * 100.0 / max_conn.setting::int, 1) AS usage_pct
  FROM pg_stat_activity, (SELECT setting FROM pg_settings WHERE
  name='max_connections') max_conn
  GROUP BY max_conn.setting;

  -- 2. 按状态/应用拆分，找占坑的是谁
  SELECT
    application_name,
    state,
    count(*)                                       AS cnt,
    max(now() - state_change)                      AS max_age,
    max(now() - query_start)                       AS max_query_age
  FROM pg_stat_activity
  WHERE pid <> pg_backend_pid()
  GROUP BY 1, 2
  ORDER BY cnt DESC;

  -- 3. 找超过 30s 的慢查询（高峰期常见卡点）
  SELECT
    pid, application_name, state,
    now() - query_start AS duration,
    left(query, 120)    AS query_snippet
  FROM pg_stat_activity
  WHERE state != 'idle'
    AND query_start < now() - interval '30 seconds'
  ORDER BY duration DESC;

  ---
  第二步：判断是「PgBouncer 池满」还是「Postgres 直连溢出」

  # 看 PgBouncer 状态（若有）
  psql -p 6432 pgbouncer -c "SHOW POOLS;" | grep -E
  "checkout|cl_active|cl_waiting|sv_active|sv_idle|sv_used"
  psql -p 6432 pgbouncer -c "SHOW STATS_TOTALS;"

  # 直连情况看 pg_hba.conf 拒绝日志
  grep "FATAL.*remaining connection slots" /var/log/postgresql/*.log | tail -20
  grep "too many connections"              /var/log/postgresql/*.log | tail -20

  ---
  第三步：即时止血（不重启）

  3-A：杀掉 idle 长连接（慎选，只动 idle）

  -- 先 dry-run
  SELECT pid, application_name, state, now() - state_change AS idle_for
  FROM pg_stat_activity
  WHERE state = 'idle'
    AND now() - state_change > interval '5 minutes'
    AND pid <> pg_backend_pid();

  -- 确认无误后执行
  SELECT pg_terminate_backend(pid)
  FROM pg_stat_activity
  WHERE state = 'idle'
    AND now() - state_change > interval '5 minutes'
    AND pid <> pg_backend_pid();

  3-B：临时扩 max_connections（需 superuser，重启生效 → 先做软上限）

  -- 超级用户立即生效（不重启）
  ALTER SYSTEM SET max_connections = 300;   -- 视内存调整，每条约 10 MB
  SELECT pg_reload_conf();                  -- 注意：max_connections 
  需重启；但下面两项不需要
  ALTER SYSTEM SET work_mem = '4MB';        -- 减少大查询内存占用
  ALTER SYSTEM SET idle_in_transaction_session_timeout = '30s';  -- 
  立即生效，防止事务长挂
  SELECT pg_reload_conf();

  3-C：PgBouncer 动态调池（推荐，零停机）

  # /etc/pgbouncer/pgbouncer.ini — 调整后 RELOAD 即生效
  [pgbouncer]
  pool_mode = transaction          # checkout 服务必须用 transaction mode
  default_pool_size = 25           # 按核心数 × 2~4 设置
  max_client_conn = 2000           # 客户端上限
  reserve_pool_size = 5            # 紧急预留
  reserve_pool_timeout = 3         # 秒
  server_idle_timeout = 60         # 断开空闲后端连接

  psql -p 6432 pgbouncer -c "RELOAD;"
  psql -p 6432 pgbouncer -c "SHOW POOLS;"   # 验证生效

  ---
  第四步：应用层修复（连接池配置）

  Python (SQLAlchemy / asyncpg)

  from sqlalchemy.ext.asyncio import create_async_engine

  engine = create_async_engine(
      DATABASE_URL,
      pool_size=10,          # 每个 worker 持有的最大连接
      max_overflow=5,        # 允许临时超出
      pool_timeout=5,        # 等待可用连接的超时（秒）—— 别设太大，快速 fail > 
  排队等死
      pool_recycle=1800,     # 30 分钟回收，防止 PostgreSQL 服务端强踢
      pool_pre_ping=True,    # 每次取出时 ping 一下，避免拿到死连接
  )

  超时熔断（FastAPI 示例）

  import asyncio
  from fastapi import HTTPException

  async def checkout(order_id: str, db):
      try:
          async with asyncio.timeout(3.0):          # 3s 内必须拿到连接
              async with db.begin():
                  ...
      except TimeoutError:
          raise HTTPException(503, detail="checkout 暂时不可用，请稍后重试")
  ⎿  Interrupted · What should Claude do instead?