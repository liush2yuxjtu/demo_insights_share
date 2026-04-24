---
{
  "id": "m1-kb-ab-002",
  "title": "验证逻辑 (Verifier判断点)",
  "author": "m1",
  "confidence": 0.85,
  "tags": [
    "knowledge-extraction",
    "session-analysis",
    "group_ab"
  ],
  "status": "active",
  "topic_id": "m1-kb-ab",
  "label": "good",
  "label_note": "- 1. **文件存在性**：两个输出文件均已生成于 `/tmp/workspace/demo2_overnight/` 目录。\\n    52→2. **结构完整性**：`demo2_program.h\n- 5. **第 5 轮新增**：写入顺序必须是 design 后 html。\\n  6. （第 6 条，若有，以 `demo2_program.md` 中实际数量为准）\\n- 外部资源约束用 `<cod\n- 5. **第 5 轮新增**：写入顺序必须是 design 后 html。\\n    88→  6. （第 6 条，若有，以 `demo2_program.md` 中实际数量为准）\\n    89→-\n- 1. **语法检查**：将 HTML 内容写入临时 `.html` 文件，用 `node -e \\\"require('fs').readFileSync(...,'utf8')\\\"` 或等价方式验证无\n- 1. **follow 行为**：`dist < 8` 时 vx/vy 归零，消除抖动\\n2. **bounce 行为**：落地后 vy 重置为 `-(4 + Math.r",
  "applies_when": [],
  "do_not_apply_when": []
}
---

# 验证逻辑 (Verifier判断点)

> author: m1 · confidence: 0.85

- 1. **文件存在性**：两个输出文件均已生成于 `/tmp/workspace/demo2_overnight/` 目录。\n    52→2. **结构完整性**：`demo2_program.h
- 5. **第 5 轮新增**：写入顺序必须是 design 后 html。\n  6. （第 6 条，若有，以 `demo2_program.md` 中实际数量为准）\n- 外部资源约束用 `<cod
- 5. **第 5 轮新增**：写入顺序必须是 design 后 html。\n    88→  6. （第 6 条，若有，以 `demo2_program.md` 中实际数量为准）\n    89→-
- 1. **语法检查**：将 HTML 内容写入临时 `.html` 文件，用 `node -e \"require('fs').readFileSync(...,'utf8')\"` 或等价方式验证无
- 1. **follow 行为**：`dist < 8` 时 vx/vy 归零，消除抖动\n2. **bounce 行为**：落地后 vy 重置为 `-(4 + Math.r
