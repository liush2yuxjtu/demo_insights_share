---
{
  "id": "m1-error-005",
  "title": "No such tool available: Glob — SDK-py Restriction",
  "author": "m1",
  "team": null,
  "confidence": 0.82,
  "tags": [
    "sdk-py",
    "Glob",
    "tool-unavailable",
    "Claude Code"
  ],
  "status": "active",
  "applies_when": [
    "sdk-py environment detection",
    "tool availability checks"
  ],
  "do_not_apply_when": [
    "full Claude Code environment"
  ],
  "raw_log": "./raw/m1-error-005.jsonl",
  "topic_id": "error-patterns",
  "label": "bad",
  "label_note": "Glob not available in sdk-py; use Bash ls instead",
  "label_override": null,
  "label_override_by": null,
  "label_override_at": null,
  "raw_log_type": "jsonl"
}
---

# No such tool available: Glob — SDK-py Restriction

> author: m1 · team: shared · confidence: 0.82

## Description



## Bad example



## Good example



## Applies when

- sdk-py environment detection
- tool availability checks

## Do NOT apply when

- full Claude Code environment

## Raw log

[./raw/m1-error-005.jsonl](./raw/m1-error-005.jsonl)
