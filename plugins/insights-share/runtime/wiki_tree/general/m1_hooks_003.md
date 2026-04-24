---
{
  "id": "m1-hooks-003",
  "title": "Hook Chaining: UserPromptSubmit->Stop->SessionStart",
  "author": "m1",
  "team": null,
  "confidence": 0.85,
  "tags": [
    "hooks",
    "UserPromptSubmit",
    "Stop",
    "SessionStart",
    "chain"
  ],
  "status": "active",
  "applies_when": [
    "multi-phase insight workflows",
    "cascading hook triggers"
  ],
  "do_not_apply_when": [
    "simple single-hook tasks"
  ],
  "raw_log": "./raw/m1-hooks-003.jsonl",
  "topic_id": "hooks",
  "label": "good",
  "label_note": "Hooks fire sequentially; Stop hook requires transcript content",
  "label_override": null,
  "label_override_by": null,
  "label_override_at": null,
  "raw_log_type": "jsonl"
}
---

# Hook Chaining: UserPromptSubmit->Stop->SessionStart

> author: m1 · team: shared · confidence: 0.85

## Description



## Bad example



## Good example



## Applies when

- multi-phase insight workflows
- cascading hook triggers

## Do NOT apply when

- simple single-hook tasks

## Raw log

[./raw/m1-hooks-003.jsonl](./raw/m1-hooks-003.jsonl)
