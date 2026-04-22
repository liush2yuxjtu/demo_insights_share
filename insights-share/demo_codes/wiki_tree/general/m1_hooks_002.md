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
  "raw_log_type": "jsonl",
  "raw_log_sha256": "9b5fec0b25dd0846d0079bfb1b2fb00acf941da7da6fb14974dbe9581a4d5305",
  "signature_algorithm": "ed25519",
  "signature_schema": 1,
  "signature_key_id": "51e8985cd0e6105e",
  "signature": "lsTWTszUA/XFrURMcgU9ZzsBwIJhdc7TYMoJTltttU08gWYT5CDKv8i245MUzWO9W1OTLZaAu8F3oqbtbPONAw==",
  "signature_signed_at": "2026-04-22T08:22:38.914044+00:00"
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
