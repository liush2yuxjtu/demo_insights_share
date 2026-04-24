---
{
  "id": "m1-kb-ah-021",
  "title": "Error Patterns & Fixes",
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
  "label_note": "\n| 错误 | 原因 | 修复 |\n|------|------|------|\n| Zotero MCP 全线失败 | 本地 API 未运行 | 降级为手动 BibTeX 生成 + NBIB 导出 |\n| codex 进程 4×90% CPU | 老 session 残留子进程 | `pkill -9 -f \"codex-darwin-arm64\"` |\n| Paperclip 启动缺包 | `@embedded-postgres/darwin-arm64` 缺失 | 后台启动或重装依赖 |\n| 重复任务消息 | 消息队列重试机制 | 忽略，已完成任务标记在 TaskList |",
  "applies_when": [],
  "do_not_apply_when": []
}
---

# Error Patterns & Fixes

> author: m1 · confidence: 0.85


| 错误 | 原因 | 修复 |
|------|------|------|
| Zotero MCP 全线失败 | 本地 API 未运行 | 降级为手动 BibTeX 生成 + NBIB 导出 |
| codex 进程 4×90% CPU | 老 session 残留子进程 | `pkill -9 -f "codex-darwin-arm64"` |
| Paperclip 启动缺包 | `@embedded-postgres/darwin-arm64` 缺失 | 后台启动或重装依赖 |
| 重复任务消息 | 消息队列重试机制 | 忽略，已完成任务标记在 TaskList |
