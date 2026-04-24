---
{
  "id": "m1-kb-ah-043",
  "title": "Deduplication Notes",
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
  "label_note": "\n- `http://127.0.0.1:18789/` 在多个项目中重复出现 → 本质是 OpenClaw gateway 调试地址\n- `openclaw gateway status` 命令在多 session 出现 → 通用诊断命令\n- token_missing 错误在 screen-monitor 相关 session 重复 → 常见初始化问题\n- NDJSON bridge 模式在 openclaw-plugin 项目中标准化\n\n\n================================================================================",
  "applies_when": [],
  "do_not_apply_when": []
}
---

# Deduplication Notes

> author: m1 · confidence: 0.85


- `http://127.0.0.1:18789/` 在多个项目中重复出现 → 本质是 OpenClaw gateway 调试地址
- `openclaw gateway status` 命令在多 session 出现 → 通用诊断命令
- token_missing 错误在 screen-monitor 相关 session 重复 → 常见初始化问题
- NDJSON bridge 模式在 openclaw-plugin 项目中标准化


================================================================================
