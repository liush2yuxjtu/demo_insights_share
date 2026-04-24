---
{
  "id": "m1-kb-aa-007",
  "title": "7. 错误模式与修复",
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
  "label_note": "\n### 错误：sessions should be nested with care\n- **原因**：在已注册 tmux session 里再起 tmux 时未 unset `$TMUX`\n- **修复**：`TMUX= tmux ...` 或 `unset TMUX`\n\n### 错误：too many connections\n- **原因**：达到 `max_connections` 上限，午高峰并发堆积\n- **修复**：PgBouncer 连接池 + 应用层连接限制 + 慢查询优化\n\n---",
  "applies_when": [],
  "do_not_apply_when": []
}
---

# 7. 错误模式与修复

> author: m1 · confidence: 0.85


### 错误：sessions should be nested with care
- **原因**：在已注册 tmux session 里再起 tmux 时未 unset `$TMUX`
- **修复**：`TMUX= tmux ...` 或 `unset TMUX`

### 错误：too many connections
- **原因**：达到 `max_connections` 上限，午高峰并发堆积
- **修复**：PgBouncer 连接池 + 应用层连接限制 + 慢查询优化

---
