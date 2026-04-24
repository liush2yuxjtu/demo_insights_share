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
  "raw_log_type": "jsonl"
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
