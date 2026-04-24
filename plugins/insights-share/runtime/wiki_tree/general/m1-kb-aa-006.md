---
{
  "id": "m1-kb-aa-006",
  "title": "6. Queue Operation 协议",
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
  "label_note": "\n```json\n{\"type\": \"queue-operation\", \"operation\": \"enqueue\", \"content\": \"...\"}\n{\"type\": \"queue-operation\", \"operation\": \"dequeue\"}\n```\n- 与 `/daily-report`、`/export`、`/exit` 等 slash 命令配合使用\n\n---",
  "applies_when": [],
  "do_not_apply_when": []
}
---

# 6. Queue Operation 协议

> author: m1 · confidence: 0.85


```json
{"type": "queue-operation", "operation": "enqueue", "content": "..."}
{"type": "queue-operation", "operation": "dequeue"}
```
- 与 `/daily-report`、`/export`、`/exit` 等 slash 命令配合使用

---
