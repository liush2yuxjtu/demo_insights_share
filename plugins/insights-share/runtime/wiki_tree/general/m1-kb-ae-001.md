---
{
  "id": "m1-kb-ae-001",
  "title": "Technical Findings",
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
  "label_note": "\n### 工具可用性与 SDK 差异\n- `Glob` 工具在 sdk-py 入口点（offline wiki search agent）不可用，只能用 `Bash ls` 替代\n- `sdk-cli` 和 `sdk-py` 入口点支持的工具集不同\n- `entrypoint` 类型：`cli`（裸 Claude Code）、`sdk-cli`（CLI SDK）、`sdk-py`（Python SDK）\n\n### Session 管理模式\n- Claude Code 使用 `/loop N m {task}` 做定期后台任务（如每 10 分钟确认状态）\n- Session 通过 `status.md` / `report.md` / `plan.md` / `next.md` 做持久化状态维护\n- 每次 loop 迭代追加确认时间戳到 status.md，避免重复执行\n- 背景：codex_run_claude 项目用此模式维护 100+ skills 目录\n\n### Wiki Search Agent 模式（offline wiki）\n- 4 层结构：wiki_types.json ",
  "applies_when": [],
  "do_not_apply_when": []
}
---

# Technical Findings

> author: m1 · confidence: 0.85


### 工具可用性与 SDK 差异
- `Glob` 工具在 sdk-py 入口点（offline wiki search agent）不可用，只能用 `Bash ls` 替代
- `sdk-cli` 和 `sdk-py` 入口点支持的工具集不同
- `entrypoint` 类型：`cli`（裸 Claude Code）、`sdk-cli`（CLI SDK）、`sdk-py`（Python SDK）

### Session 管理模式
- Claude Code 使用 `/loop N m {task}` 做定期后台任务（如每 10 分钟确认状态）
- Session 通过 `status.md` / `report.md` / `plan.md` / `next.md` 做持久化状态维护
- 每次 loop 迭代追加确认时间戳到 status.md，避免重复执行
- 背景：codex_run_claude 项目用此模式维护 100+ skills 目录

### Wiki Search Agent 模式（offline wiki）
- 4 层结构：wiki_types.json
