---
{
  "id": "m1-kb-ao-013",
  "title": "10. Shutdown 协议",
  "author": "m1",
  "confidence": 0.85,
  "tags": [
    "knowledge-extraction",
    "session-analysis",
    "group_ao"
  ],
  "status": "active",
  "topic_id": "m1-kb-ao",
  "label": "good",
  "label_note": "\n### 标准格式\n```json\n{\n  \"type\": \"shutdown_request\",\n  \"requestId\": \"shutdown-XXX@agent-name\",\n  \"from\": \"team-lead\",\n  \"reason\": \"Task complete. Shutting down the team.\",\n  \"timestamp\": \"...\"\n}\n```\n\n### Agent 响应\n```json\n{\n  \"type\": \"shutdown_response\",\n  \"request_id\": \"shutdown-XXX@agent-name\",\n  \"approve\": true\n}\n```\n\n---",
  "applies_when": [],
  "do_not_apply_when": []
}
---

# 10. Shutdown 协议

> author: m1 · confidence: 0.85


### 标准格式
```json
{
  "type": "shutdown_request",
  "requestId": "shutdown-XXX@agent-name",
  "from": "team-lead",
  "reason": "Task complete. Shutting down the team.",
  "timestamp": "..."
}
```

### Agent 响应
```json
{
  "type": "shutdown_response",
  "request_id": "shutdown-XXX@agent-name",
  "approve": true
}
```

---
