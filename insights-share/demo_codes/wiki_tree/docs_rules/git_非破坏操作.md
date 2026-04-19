---
{
  "id": "m1-git_非破坏操作-2026-04-18",
  "title": "Git 非破坏操作",
  "author": "m1",
  "tags": [
    "execution-strategy",
    "git"
  ],
  "status": "active",
  "applies_when": [
    "需要 git reset --hard 或 push --force 时"
  ],
  "do_not_apply_when": [],
  "raw_log": "./raw/m1-git_非破坏操作-2026-04-18.jsonl",
  "topic_id": "m1-git_非破坏操作",
  "label": "bad",
  "label_note": "避免破坏操作，寻找安全替代方案，非用户显式请求不执行",
  "label_override": null,
  "label_override_by": null,
  "label_override_at": null,
  "raw_log_type": "jsonl"
}
---

# Git 非破坏操作

> author: m1 · label: **bad**

## Description

避免破坏操作，寻找安全替代方案，非用户显式请求不执行

## Bad example

避免破坏操作，寻找安全替代方案，非用户显式请求不执行

## Good example

（本卡记录拒绝此方案的决策；参见 raw log 中实际场景）

## Applies when

- 需要 git reset --hard 或 push --force 时

## Do NOT apply when

(none)

## Raw log

[./raw/m1-git_非破坏操作-2026-04-18.jsonl](./raw/m1-git_非破坏操作-2026-04-18.jsonl)

> 原始 session：`/Users/m1/.claude/projects/-Users-m1/69602ae1-7e70-49b5-85d7-9062abeed748/subagents/agent-abe8b70.jsonl`
