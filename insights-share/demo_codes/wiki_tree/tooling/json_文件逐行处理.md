---
{
  "id": "m1-json_文件逐行处理-2026-04-18",
  "title": "JSON 文件逐行处理",
  "author": "m1",
  "tags": [
    "json"
  ],
  "status": "active",
  "applies_when": [
    "处理 jsonl 或大 JSON 文件时"
  ],
  "do_not_apply_when": [],
  "raw_log": "./raw/m1-json_文件逐行处理-2026-04-18.jsonl",
  "topic_id": "m1-json_文件逐行处理",
  "label": "good",
  "label_note": "使用 jq 逐行或流式处理，不要一次性 json.loads 整文件",
  "label_override": null,
  "label_override_by": null,
  "label_override_at": null,
  "raw_log_type": "jsonl"
}
---

# JSON 文件逐行处理

> author: m1 · label: **good**

## Description

使用 jq 逐行或流式处理，不要一次性 json.loads 整文件

## Bad example

（本卡记录采纳决策；参见 raw log 中实际踩坑对照）

## Good example

使用 jq 逐行或流式处理，不要一次性 json.loads 整文件

## Applies when

- 处理 jsonl 或大 JSON 文件时

## Do NOT apply when

(none)

## Raw log

[./raw/m1-json_文件逐行处理-2026-04-18.jsonl](./raw/m1-json_文件逐行处理-2026-04-18.jsonl)

> 原始 session：`/Users/m1/.claude/projects/-Users-m1-projects-sdk-claude-agent/758e6e54-308d-41e1-a876-857aad198267.jsonl`
