---
{
  "id": "bob-pgpool-bad-2026-04-12",
  "title": "盲目增大连接池反而拖垮系统",
  "author": "bob",
  "confidence": 0.5,
  "tags": [
    "postgres",
    "pgbouncer",
    "pool-size",
    "bad-practice"
  ],
  "status": "active",
  "applies_when": [],
  "do_not_apply_when": [],
  "raw_log": "./raw/bob-pgpool-bad-2026-04-12.txt",
  "topic_id": "postgres-pool-exhaustion",
  "label": "bad",
  "label_note": "直接把 pool size ×5 在我们 32 核机器上反而拖垮 IO",
  "label_override": "good",
  "label_override_by": "admin",
  "label_override_at": "2026-04-15T10:47:36.023042+00:00",
  "raw_log_type": "export"
}
---

# 盲目增大连接池反而拖垮系统

> author: bob · confidence: 0.5

## Description

Bob 在排查 PostgreSQL 连接池耗尽问题时，看到活跃连接数接近 pool_size 上限，就直接把 pool_size 从 10 改成了 50。

Bob 在排查 PostgreSQL 连接池耗尽问题时，看到活跃连接数接近 pool_size 上限，就直接把 pool_size 从 10 改成了 50。

PgBouncer transaction mode 下，增大 pool_size 到 50 但机器只有 32 核，每个连接耗 CPU，连接越多上下文切换越频繁，反而拖垮 IO。

## Bad example

修改后系统反而更慢，事务延迟从 5ms 飙升到 200ms+，数据库 CPU 使用率从 30% 涨到 90%。

## Good example

保持 pool_size=10 不变，通过减少单查询耗时（加索引、优化慢查询）来降低并发连接需求。

## Applies when

(none)

## Do NOT apply when

(none)

## Raw log

[./raw/bob-pgpool-bad-2026-04-12.txt](./raw/bob-pgpool-bad-2026-04-12.txt)
