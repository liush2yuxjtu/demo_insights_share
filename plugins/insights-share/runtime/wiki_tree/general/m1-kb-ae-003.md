---
{
  "id": "m1-kb-ae-003",
  "title": "CLI Commands & Tools",
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
  "label_note": "\n### 工具使用频率（去重）\n核心工具：Read、Write、Edit、Bash、Glob、Grep、Agent、TaskCreate、TaskUpdate、TaskGet、TaskList、SendMessage、Skill、TeamCreate、TodoWrite、ExitPlanMode、Monitor\n\nMCP 工具：mcp__MiniMax__web_search、mcp__MiniMax__understand_image\n\n其他：AskUserQuestion、claim-finish、demo-redo-publisher、pytest-runner、server-preview、tmp-cleaner、WebSearch\n\n### 入口点分布\n- `sdk-cli`：主要 CLI 会话\n- `sdk-py`：Python SDK 调用（如 offline wiki search agent）\n- `cli`：裸 Claude Code\n\n### Git 分支\n- `main`：主要分支\n- `worktree-minimax0416_dev`：隔离开发 worktr",
  "applies_when": [],
  "do_not_apply_when": []
}
---

# CLI Commands & Tools

> author: m1 · confidence: 0.85


### 工具使用频率（去重）
核心工具：Read、Write、Edit、Bash、Glob、Grep、Agent、TaskCreate、TaskUpdate、TaskGet、TaskList、SendMessage、Skill、TeamCreate、TodoWrite、ExitPlanMode、Monitor

MCP 工具：mcp__MiniMax__web_search、mcp__MiniMax__understand_image

其他：AskUserQuestion、claim-finish、demo-redo-publisher、pytest-runner、server-preview、tmp-cleaner、WebSearch

### 入口点分布
- `sdk-cli`：主要 CLI 会话
- `sdk-py`：Python SDK 调用（如 offline wiki search agent）
- `cli`：裸 Claude Code

### Git 分支
- `main`：主要分支
- `worktree-minimax0416_dev`：隔离开发 worktr
