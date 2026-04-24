---
{
  "id": "m1-agent-teams-005",
  "title": "RESET Triggers: Exception+Drift+Missing Features",
  "author": "m1",
  "team": null,
  "confidence": 0.89,
  "tags": [
    "agent-teams",
    "RESET",
    "error",
    "drift"
  ],
  "status": "active",
  "applies_when": [
    "detecting builder output failures",
    "triggering rebuild"
  ],
  "do_not_apply_when": [
    "partial success acceptable"
  ],
  "raw_log": "./raw/m1-agent-teams-005.jsonl",
  "topic_id": "agent-teams",
  "label": "bad",
  "label_note": "Uncaught JS exception, spec-implementation drift, missing required features",
  "label_override": null,
  "label_override_by": null,
  "label_override_at": null,
  "raw_log_type": "jsonl"
}
---

# RESET Triggers: Exception+Drift+Missing Features

> author: m1 · team: shared · confidence: 0.89

## Description



## Bad example



## Good example



## Applies when

- detecting builder output failures
- triggering rebuild

## Do NOT apply when

- partial success acceptable

## Raw log

[./raw/m1-agent-teams-005.jsonl](./raw/m1-agent-teams-005.jsonl)
