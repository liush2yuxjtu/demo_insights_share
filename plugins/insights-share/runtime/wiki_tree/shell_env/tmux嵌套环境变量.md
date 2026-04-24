---
{
  "id": "m1-tmux嵌套环境变量-2026-04-18",
  "title": "tmux嵌套环境变量",
  "author": "m1",
  "tags": [
    "demo-project",
    "nested",
    "tmux"
  ],
  "status": "active",
  "applies_when": [
    "在已注册 tmux 里再启 tmux 时"
  ],
  "do_not_apply_when": [],
  "raw_log": "./raw/m1-tmux嵌套环境变量-2026-04-18.jsonl",
  "topic_id": "m1-tmux嵌套环境变量",
  "label": "bad",
  "label_note": "仅加 -L 独立 socket 不够，必须 TMUX= tmux 或 unset TMUX",
  "label_override": null,
  "label_override_by": null,
  "label_override_at": null,
  "raw_log_type": "jsonl"
}
---

# tmux嵌套环境变量

> author: m1 · label: **bad**

## Description

仅加 -L 独立 socket 不够，必须 TMUX= tmux 或 unset TMUX

## Bad example

仅加 -L 独立 socket 不够，必须 TMUX= tmux 或 unset TMUX

## Good example

（本卡记录拒绝此方案的决策；参见 raw log 中实际场景）

## Applies when

- 在已注册 tmux 里再启 tmux 时

## Do NOT apply when

(none)

## Raw log

[./raw/m1-tmux嵌套环境变量-2026-04-18.jsonl](./raw/m1-tmux嵌套环境变量-2026-04-18.jsonl)

> 原始 session：`/Users/m1/.claude/projects/-Users-m1-projects-shandong--shengli/5d0de7ab-ebb2-45e2-a9af-aaf108238c56.jsonl`
