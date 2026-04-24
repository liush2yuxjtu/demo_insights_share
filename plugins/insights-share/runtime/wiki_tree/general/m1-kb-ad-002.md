---
{
  "id": "m1-kb-ad-002",
  "title": "项目架构 / Project Architecture",
  "author": "m1",
  "confidence": 0.85,
  "tags": [
    "knowledge-extraction",
    "session-analysis",
    "group_ad"
  ],
  "status": "active",
  "topic_id": "m1-kb-ad",
  "label": "good",
  "label_note": "\n### 核心文件结构\n| 文件路径 | 用途 |\n|---------|------|\n| `state/current_task.md` | 当前唯一任务文件 |\n| `state/memory/status.md` | 任务状态标记 (completed/blocked) |\n| `state/memory/plan.md` | 计划文档 |\n| `state/memory/report.md` | 报告文档 |\n| `state/memory/next.md` | 下一步文档 |\n| `scripts/claude_background.py` | 后台运行脚本 |\n| `AGENTS.md` | 项目级 Agent 指令 |\n| `CLAUDE.md` | 项目级规则配置 |\n\n### Memory 目录契约\n- 所有任务只在 `state/memory/*.md` 中执行，**不要修改其他文件**\n- 4 个固定文件: status.md / plan.md / report.md / next.md\n- 阻塞时在 status.md 标记 `blocked` 并写明原因",
  "applies_when": [],
  "do_not_apply_when": []
}
---

# 项目架构 / Project Architecture

> author: m1 · confidence: 0.85


### 核心文件结构
| 文件路径 | 用途 |
|---------|------|
| `state/current_task.md` | 当前唯一任务文件 |
| `state/memory/status.md` | 任务状态标记 (completed/blocked) |
| `state/memory/plan.md` | 计划文档 |
| `state/memory/report.md` | 报告文档 |
| `state/memory/next.md` | 下一步文档 |
| `scripts/claude_background.py` | 后台运行脚本 |
| `AGENTS.md` | 项目级 Agent 指令 |
| `CLAUDE.md` | 项目级规则配置 |

### Memory 目录契约
- 所有任务只在 `state/memory/*.md` 中执行，**不要修改其他文件**
- 4 个固定文件: status.md / plan.md / report.md / next.md
- 阻塞时在 status.md 标记 `blocked` 并写明原因
