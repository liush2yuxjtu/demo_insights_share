---
{
  "id": "m1-hooks-002",
  "title": "Self-Verify Loop: Agent-Judge Double Probe Pattern",
  "author": "m1",
  "team": null,
  "confidence": 0.87,
  "tags": [
    "self-verify-loop",
    "agent-judge",
    "probe",
    "quality-gate"
  ],
  "status": "active",
  "applies_when": [
    "CLAUDE.md changes",
    "significant code changes",
    "proposal updates"
  ],
  "do_not_apply_when": [
    "trivial one-line fixes"
  ],
  "raw_log": "./raw/m1-hooks-002.jsonl",
  "topic_id": "self-verify",
  "label": "good",
  "label_note": "claudefast -p probe + claudefast -p judge -> PASS/REFINE/FAIL",
  "label_override": null,
  "label_override_by": null,
  "label_override_at": null,
  "raw_log_type": "jsonl"
}
---

# Self-Verify Loop: Agent-Judge Double Probe Pattern

> author: m1 · team: shared · confidence: 0.87

## Description



## Bad example



## Good example



## Applies when

- CLAUDE.md changes
- significant code changes
- proposal updates

## Do NOT apply when

- trivial one-line fixes

## Raw log

[./raw/m1-hooks-002.jsonl](./raw/m1-hooks-002.jsonl)
