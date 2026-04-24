---
{
  "id": "m1-kb-ae-002",
  "title": "Error Patterns & Fixes",
  "author": "m1",
  "confidence": 0.85,
  "tags": [
    "knowledge-extraction",
    "session-analysis",
    "group_ae"
  ],
  "status": "active",
  "topic_id": "m1-kb-ae",
  "label": "good",
  "label_note": "\n### \"No such tool available: Glob\"\n- **原因**：sdk-py 入口点的 offline wiki search agent 不暴露 Glob tool\n- **修复**：降级到 `Bash ls` 做目录列表\n\n### Tool availability 差异\n- 同一个 tool 在不同 entrypoint（cli vs sdk-py）可用性不同\n- 编写跨入口 agent 时需做工具降级预案\n\n### Hook bridge unavailable\n- `OpenIslandHooks` bridge 在部分环境不可用，报 `[OpenIslandHooks] bridge unavailable for claude hook (SessionStart)`\n- 不影响核心功能，agent 继续正常执行\n\n---",
  "applies_when": [],
  "do_not_apply_when": []
}
---

# Error Patterns & Fixes

> author: m1 · confidence: 0.85


### "No such tool available: Glob"
- **原因**：sdk-py 入口点的 offline wiki search agent 不暴露 Glob tool
- **修复**：降级到 `Bash ls` 做目录列表

### Tool availability 差异
- 同一个 tool 在不同 entrypoint（cli vs sdk-py）可用性不同
- 编写跨入口 agent 时需做工具降级预案

### Hook bridge unavailable
- `OpenIslandHooks` bridge 在部分环境不可用，报 `[OpenIslandHooks] bridge unavailable for claude hook (SessionStart)`
- 不影响核心功能，agent 继续正常执行

---
