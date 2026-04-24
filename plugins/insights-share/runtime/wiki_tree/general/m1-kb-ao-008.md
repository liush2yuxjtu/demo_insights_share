---
{
  "id": "m1-kb-ao-008",
  "title": "7. Model / LLM 相关",
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
  "label_note": "\n### 关键观察\n- 使用 `grep` 关键词验证规则会\"腐烂\"（随措辞演进失效）\n- 替代方案：LLM-as-judge 双探针循环\n- `claudefast -p` 用于探针验证\n\n### ccfast-opt 模式\n```\nprobe = claudefast -p \"<hypothetical question about the rule>\"\njudge = claudefast -p \"<evaluation prompt>\"\n```\n\n---",
  "applies_when": [],
  "do_not_apply_when": []
}
---

# 7. Model / LLM 相关

> author: m1 · confidence: 0.85


### 关键观察
- 使用 `grep` 关键词验证规则会"腐烂"（随措辞演进失效）
- 替代方案：LLM-as-judge 双探针循环
- `claudefast -p` 用于探针验证

### ccfast-opt 模式
```
probe = claudefast -p "<hypothetical question about the rule>"
judge = claudefast -p "<evaluation prompt>"
```

---
