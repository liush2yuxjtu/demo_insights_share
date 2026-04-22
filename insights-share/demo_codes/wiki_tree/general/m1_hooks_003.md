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
  "raw_log_type": "jsonl",
  "raw_log_sha256": "6cf0a7e291dcfce63b092c174271cf60f7041d6dafaf9b8d11d00911114867b3",
  "signature_algorithm": "ed25519",
  "signature_schema": 1,
  "signature_key_id": "51e8985cd0e6105e",
  "signature": "Dw83FJo2g28ml4ATjuqc1bI4eQgkg7LiKuSA/bB1we5z4PsmA1Q4OdoXCIFT8TBM2NAJhy6+u+Cy7J3RIt88AQ==",
  "signature_signed_at": "2026-04-22T08:22:38.928827+00:00"
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
