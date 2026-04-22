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
  "raw_log_type": "jsonl",
  "raw_log_sha256": "13a9af34ede864f9ccc008a4280b7218d2ee2ead7331193ca45ed151110fcf89",
  "signature_algorithm": "ed25519",
  "signature_schema": 1,
  "signature_key_id": "51e8985cd0e6105e",
  "signature": "eufupKkBnZbjMg1Srx6HaGCjBVsZ3XN353lBhzOI3q0sgK4fgv/YB+DZS271dcXbWIMSpWRAlSNMS1cKbt8mDA==",
  "signature_signed_at": "2026-04-22T08:22:23.565472+00:00"
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
