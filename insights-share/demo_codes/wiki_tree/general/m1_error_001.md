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
  "raw_log_type": "jsonl",
  "raw_log_sha256": "af1605dbf4de7f28d05e55b16fa939b6bb0f6a75f3bbb0c886ba47dbe1d84e5e",
  "signature_algorithm": "ed25519",
  "signature_schema": 1,
  "signature_key_id": "51e8985cd0e6105e",
  "signature": "c68XaIbn7/0wC4Y8/Zz6JRuggSoxv8hsJ/Ni+yYC5oUfQ1BEMi5QUhIy/udTLKASpMSXt7kotNp7xyWBO2ujDA==",
  "signature_signed_at": "2026-04-22T08:22:19.454817+00:00"
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
