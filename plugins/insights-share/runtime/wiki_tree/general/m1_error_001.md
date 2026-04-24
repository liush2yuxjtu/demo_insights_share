---
{
  "id": "m1-error-001",
  "title": "Glob Tool Unavailable in sdk-py: Bash ls Fallback",
  "author": "m1",
  "team": null,
  "confidence": 0.85,
  "tags": [
    "error-pattern",
    "sdk-py",
    "Glob",
    "fallback",
    "tool-availability"
  ],
  "status": "active",
  "applies_when": [
    "running inside sdk-py environment",
    "restricted toolset"
  ],
  "do_not_apply_when": [
    "standard Claude Code session",
    "full tool access"
  ],
  "raw_log": "./raw/m1-error-001.jsonl",
  "topic_id": "error-patterns",
  "label": "bad",
  "label_note": "降级到 Bash ls -la 实现同类功能",
  "label_override": null,
  "label_override_by": null,
  "label_override_at": null,
  "raw_log_type": "jsonl"
}
---

# Glob Tool Unavailable in sdk-py: Bash ls Fallback

> author: m1 · team: shared · confidence: 0.85

## Description



## Bad example



## Good example



## Applies when

- running inside sdk-py environment
- restricted toolset

## Do NOT apply when

- standard Claude Code session
- full tool access

## Raw log

[./raw/m1-error-001.jsonl](./raw/m1-error-001.jsonl)
