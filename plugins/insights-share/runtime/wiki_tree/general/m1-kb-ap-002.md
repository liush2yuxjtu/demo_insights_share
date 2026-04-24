---
{
  "id": "m1-kb-ap-002",
  "title": "1. Technical Findings & Patterns",
  "author": "m1",
  "confidence": 0.85,
  "tags": [
    "knowledge-extraction",
    "session-analysis",
    "group_ap"
  ],
  "status": "active",
  "topic_id": "m1-kb-ap",
  "label": "good",
  "label_note": "\n### 1.1 Hook System Patterns\n\n**Hook types observed:**\n- `SessionStart:startup` — injects caveman mode, superpowers skill context\n- `UserPromptSubmit` — caveman mode enforcement\n- `hook_additional_context` — context injection from hookify rules\n- `hook_success` — hook execution confirmation\n\n**Key pattern: Hook chaining**\n```\nSessionStart → hookify rules → additional_context injection → caveman/superpowers mode activation\n```\n\n**Hook behavior observation:**\n- Hooks can inject `CAVEMAN MODE ACTI",
  "applies_when": [],
  "do_not_apply_when": []
}
---

# 1. Technical Findings & Patterns

> author: m1 · confidence: 0.85


### 1.1 Hook System Patterns

**Hook types observed:**
- `SessionStart:startup` — injects caveman mode, superpowers skill context
- `UserPromptSubmit` — caveman mode enforcement
- `hook_additional_context` — context injection from hookify rules
- `hook_success` — hook execution confirmation

**Key pattern: Hook chaining**
```
SessionStart → hookify rules → additional_context injection → caveman/superpowers mode activation
```

**Hook behavior observation:**
- Hooks can inject `CAVEMAN MODE ACTI
