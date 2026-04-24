---
{
  "id": "m1-kb-ah-020",
  "title": "Technical Findings & Patterns",
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
  "label_note": "\n### Zotero MCP Integration\n- Zotero API 端口 23119，本地不可用时 `mcp__zotero__` 工具全失效\n- DOI 导入优先于 URL 导入（metadata 更完整）\n- NBIB 文件可作为 Zotero 手动导入格式\n- Zotero REST API `?format=bibtex` 仅导出直接子项，子收藏需逐个迭代\n- CrossRef API (`api.crossref.org/works/{DOI}`) 可作 DOI 元数据回退\n\n### 多 Agent 任务编排\n- Team 工作流：team-lead 发任务 → implementer-X 逐个执行 → 用 TaskUpdate 标记 in_progress/completed\n- 任务间有依赖关系时（如 Task #7 需等其他任务完成），轮询 TaskList 等待\n- Worktree 隔离：`git worktree add` 创建独立工作目录，避免并行任务相互覆盖\n- 重复任务消息属正常（队列重试），已完成的实现可忽略\n\n### GPU/ML 管线 (",
  "applies_when": [],
  "do_not_apply_when": []
}
---

# Technical Findings & Patterns

> author: m1 · confidence: 0.85


### Zotero MCP Integration
- Zotero API 端口 23119，本地不可用时 `mcp__zotero__` 工具全失效
- DOI 导入优先于 URL 导入（metadata 更完整）
- NBIB 文件可作为 Zotero 手动导入格式
- Zotero REST API `?format=bibtex` 仅导出直接子项，子收藏需逐个迭代
- CrossRef API (`api.crossref.org/works/{DOI}`) 可作 DOI 元数据回退

### 多 Agent 任务编排
- Team 工作流：team-lead 发任务 → implementer-X 逐个执行 → 用 TaskUpdate 标记 in_progress/completed
- 任务间有依赖关系时（如 Task #7 需等其他任务完成），轮询 TaskList 等待
- Worktree 隔离：`git worktree add` 创建独立工作目录，避免并行任务相互覆盖
- 重复任务消息属正常（队列重试），已完成的实现可忽略

### GPU/ML 管线 (
