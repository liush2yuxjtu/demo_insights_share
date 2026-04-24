---
{
  "id": "m1-kb-aa-002",
  "title": "2. Insights-share Wiki 格式约定",
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
  "label_note": "\n### Wiki 卡片元数据（INSIGHTS_SHARE_META 前端注释）\n```markdown\n<!-- INSIGHTS_SHARE_META\n{\n  \"wiki_type\": \"database\",\n  \"slug\": \"postgres-concurrency\",\n  \"title\": \"Postgres 并发等待排查\",\n  \"problem\": \"事务阻塞导致 lock timeout、吞吐下降和请求排队。\",\n  \"triggers\": [\"lock timeout\", \"事务阻塞\", \"高并发排队\", \"pg_locks\"],\n  \"positive_examples\": [\"先看阻塞链，再确认锁类型与热点事务。\"],\n  \"negative_examples\": [\"直接扩大连接池。\"],\n  \"raw_logs\": [\"postgres/postgres-concurrency-session.jsonl\"],\n  \"status\": \"reviewed\"\n}\n-->\n```\n\n### 约定输出格式\n- `first-setup-guide` — 新用户引",
  "applies_when": [],
  "do_not_apply_when": []
}
---

# 2. Insights-share Wiki 格式约定

> author: m1 · confidence: 0.85


### Wiki 卡片元数据（INSIGHTS_SHARE_META 前端注释）
```markdown
<!-- INSIGHTS_SHARE_META
{
  "wiki_type": "database",
  "slug": "postgres-concurrency",
  "title": "Postgres 并发等待排查",
  "problem": "事务阻塞导致 lock timeout、吞吐下降和请求排队。",
  "triggers": ["lock timeout", "事务阻塞", "高并发排队", "pg_locks"],
  "positive_examples": ["先看阻塞链，再确认锁类型与热点事务。"],
  "negative_examples": ["直接扩大连接池。"],
  "raw_logs": ["postgres/postgres-concurrency-session.jsonl"],
  "status": "reviewed"
}
-->
```

### 约定输出格式
- `first-setup-guide` — 新用户引
