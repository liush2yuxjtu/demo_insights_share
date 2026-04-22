---
{
  "id": "m1-error-002",
  "title": "localStorage Quota Exceeded: try/catch Guard Required",
  "author": "m1",
  "team": null,
  "confidence": 0.87,
  "tags": [
    "localStorage",
    "quota",
    "error",
    "browser",
    "try-catch"
  ],
  "status": "active",
  "applies_when": [
    "writing to localStorage in browser",
    "caching large datasets"
  ],
  "do_not_apply_when": [
    "server-side storage",
    "small data only"
  ],
  "raw_log": "./raw/m1-error-002.jsonl",
  "topic_id": "error-patterns",
  "label": "bad",
  "label_note": "Always wrap localStorage writes in try/catch; check quota",
  "label_override": null,
  "label_override_by": null,
  "label_override_at": null,
  "raw_log_type": "jsonl",
  "raw_log_sha256": "ca735a02d1d22fd5c45520982caeb4c924f2f9626153f46cf269c64cae9929bb",
  "signature_algorithm": "ed25519",
  "signature_schema": 1,
  "signature_key_id": "51e8985cd0e6105e",
  "signature": "Fjf1MGIwJfjkr7QHPPl0R3qrlZ5di++F/p0Z70eWk/xksrW6KDmWJdX7rDEbLkKAY0tPWlp4UKmAEpe8mOF8Cg==",
  "signature_signed_at": "2026-04-22T08:22:19.468451+00:00"
}
---

# localStorage Quota Exceeded: try/catch Guard Required

> author: m1 · team: shared · confidence: 0.87

## Description



## Bad example



## Good example



## Applies when

- writing to localStorage in browser
- caching large datasets

## Do NOT apply when

- server-side storage
- small data only

## Raw log

[./raw/m1-error-002.jsonl](./raw/m1-error-002.jsonl)
