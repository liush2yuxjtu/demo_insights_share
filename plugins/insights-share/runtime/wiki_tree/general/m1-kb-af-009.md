---
{
  "id": "m1-kb-af-009",
  "title": "自动触发条件(hooks 判定)",
  "author": "m1",
  "confidence": 0.85,
  "tags": [
    "knowledge-extraction",
    "session-analysis",
    "group_af"
  ],
  "status": "active",
  "topic_id": "m1-kb-af",
  "label": "good",
  "label_note": "\n| 条件 | 示例 |\n|------|------|\n| 生产事故/线上 bug | \"pgbouncer 连接池炸了\" |\n|\n\n- 两种方式：\n\n**临时方案**：每次提示时选 `2) Yes, and always allow access to learned/ from this project`——以后同类操作不再弹窗。\n\n**永久方案**：在 `~/.claude/settings.json`（或项目级 `.claude/settings.json`）里加一条规则，示例：\n\n```json\n{\n  \"allow\": \n\n- # Update Config Skill\n\nModify Claude Code configuration by updating settings.json files.",
  "applies_when": [],
  "do_not_apply_when": []
}
---

# 自动触发条件(hooks 判定)

> author: m1 · confidence: 0.85


| 条件 | 示例 |
|------|------|
| 生产事故/线上 bug | "pgbouncer 连接池炸了" |
|

- 两种方式：

**临时方案**：每次提示时选 `2) Yes, and always allow access to learned/ from this project`——以后同类操作不再弹窗。

**永久方案**：在 `~/.claude/settings.json`（或项目级 `.claude/settings.json`）里加一条规则，示例：

```json
{
  "allow":

- # Update Config Skill

Modify Claude Code configuration by updating settings.json files.
