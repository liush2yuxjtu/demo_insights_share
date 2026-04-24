---
{
  "id": "m1-kb-aa-003",
  "title": "3. Postgres 高并发下 Lock Timeout 排查",
  "author": "m1",
  "confidence": 0.85,
  "tags": [
    "knowledge-extraction",
    "session-analysis",
    "group_aa"
  ],
  "status": "active",
  "topic_id": "m1-kb-aa",
  "label": "good",
  "label_note": "\n### 诊断 SQL\n```sql\n-- 当前连接状态\nSELECT state, count(*) FROM pg_stat_activity WHERE datname = 'your_db' GROUP BY state;\n\n-- 连接等待锁\nSELECT pid, wait_event_type, wait_event, query FROM pg_stat_activity WHERE wait_event IS NOT NULL;\n\n-- 超过30秒的活跃查询\nSELECT pid, now() - query_start AS duration, query, state\nFROM pg_stat_activity WHERE state != 'idle' AND (now() - query_start) > interval '30 seconds'\nORDER BY duration DESC;\n\n-- 锁等待（阻塞来源）\nSELECT bl.pid AS blocked_pid, a.query AS blocked_query, al.pid AS bloc",
  "applies_when": [],
  "do_not_apply_when": []
}
---

# 3. Postgres 高并发下 Lock Timeout 排查

> author: m1 · confidence: 0.85


### 诊断 SQL
```sql
-- 当前连接状态
SELECT state, count(*) FROM pg_stat_activity WHERE datname = 'your_db' GROUP BY state;

-- 连接等待锁
SELECT pid, wait_event_type, wait_event, query FROM pg_stat_activity WHERE wait_event IS NOT NULL;

-- 超过30秒的活跃查询
SELECT pid, now() - query_start AS duration, query, state
FROM pg_stat_activity WHERE state != 'idle' AND (now() - query_start) > interval '30 seconds'
ORDER BY duration DESC;

-- 锁等待（阻塞来源）
SELECT bl.pid AS blocked_pid, a.query AS blocked_query, al.pid AS bloc
