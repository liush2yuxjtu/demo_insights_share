---
{
  "id": "m1-worktree_分离开发-2026-04-18",
  "title": "worktree 分离开发",
  "author": "m1",
  "tags": [
    "context-mgmt",
    "parallelism",
    "worktree"
  ],
  "status": "active",
  "applies_when": [
    "处理多分支并行工作时"
  ],
  "do_not_apply_when": [],
  "raw_log": "./raw/m1-worktree_分离开发-2026-04-18.jsonl",
  "topic_id": "m1-worktree_分离开发",
  "label": "good",
  "label_note": "使用 worktree 而非频繁 checkout，隔离分支状态和 context",
  "label_override": null,
  "label_override_by": null,
  "label_override_at": null,
  "raw_log_type": "jsonl"
}
---

# worktree 分离开发

> author: m1 · label: **good**

## Description

使用 worktree 而非频繁 checkout，隔离分支状态和 context

## Bad example

（本卡记录采纳决策；参见 raw log 中实际踩坑对照）

## Good example

使用 worktree 而非频繁 checkout，隔离分支状态和 context

## Applies when

- 处理多分支并行工作时

## Do NOT apply when

(none)

## Raw log

[./raw/m1-worktree_分离开发-2026-04-18.jsonl](./raw/m1-worktree_分离开发-2026-04-18.jsonl)

> 原始 session：`/Users/m1/.claude/projects/-Users-m1-projects-claude-sdk--claude-worktrees-dev-preview-html-userquestion/20660f4c-930a-4f0b-953c-cbfc491da74f.jsonl`
