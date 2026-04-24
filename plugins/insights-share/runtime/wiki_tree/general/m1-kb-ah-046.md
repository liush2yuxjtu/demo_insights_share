---
{
  "id": "m1-kb-ah-046",
  "title": "1. Technical Findings & Patterns",
  "author": "m1",
  "confidence": 0.85,
  "tags": [
    "knowledge-extraction",
    "session-analysis",
    "group_ah"
  ],
  "status": "active",
  "topic_id": "m1-kb-ah",
  "label": "good",
  "label_note": "\n### OpenClaw Plugin Architecture\n- **Plugin Manifest**: `openclaw.plugin.json` 必须包含 `id` 和 `configSchema` 字段\n- **入口函数**: `definePluginEntry` 来自 `openclaw/plugin-sdk/core`\n- **核心注册 API**:\n  - `registerService(name, definition)` — 后台定时循环\n  - `registerTool(name, definition)` — 暴露工具\n  - `registerHook(name, handler)` — 生命周期钩子（`before_tool_call`、`message_sending`、`llm_input`）\n  - `registerContextEngine(name, definition)` — 上下文引擎（v7 新增）\n- **TypeScript + Python 桥接**: NDJSON over stdin/stdout，Python 作为持",
  "applies_when": [],
  "do_not_apply_when": []
}
---

# 1. Technical Findings & Patterns

> author: m1 · confidence: 0.85


### OpenClaw Plugin Architecture
- **Plugin Manifest**: `openclaw.plugin.json` 必须包含 `id` 和 `configSchema` 字段
- **入口函数**: `definePluginEntry` 来自 `openclaw/plugin-sdk/core`
- **核心注册 API**:
  - `registerService(name, definition)` — 后台定时循环
  - `registerTool(name, definition)` — 暴露工具
  - `registerHook(name, handler)` — 生命周期钩子（`before_tool_call`、`message_sending`、`llm_input`）
  - `registerContextEngine(name, definition)` — 上下文引擎（v7 新增）
- **TypeScript + Python 桥接**: NDJSON over stdin/stdout，Python 作为持
