---
{
  "id": "m1-error-003",
  "title": "Flood Fill Stack Overflow: Use BFS Instead",
  "author": "m1",
  "team": null,
  "confidence": 0.89,
  "tags": [
    "flood-fill",
    "stack-overflow",
    "BFS",
    "canvas",
    "algorithm"
  ],
  "status": "active",
  "applies_when": [
    "canvas flood fill implementation",
    "large grid traversal"
  ],
  "do_not_apply_when": [
    "small grids where stack depth safe"
  ],
  "raw_log": "./raw/m1-error-003.jsonl",
  "topic_id": "error-patterns",
  "label": "bad",
  "label_note": "Replace recursive flood fill with iterative BFS queue",
  "label_override": null,
  "label_override_by": null,
  "label_override_at": null,
  "raw_log_type": "jsonl",
  "raw_log_sha256": "14af65d5377be7712a56049965b60c002aed26280cfa87f335fa263a33ad9d01",
  "signature_algorithm": "ed25519",
  "signature_schema": 1,
  "signature_key_id": "51e8985cd0e6105e",
  "signature": "qJhxKq6T2TaeLeGjxVFvZq6wX+ojxdtEjJPWlaFLSqUorYDO8B5/0yAemWDYEUHgbFlrGXKNkjGELy394u/VAA==",
  "signature_signed_at": "2026-04-22T08:22:19.480389+00:00"
}
---

# Flood Fill Stack Overflow: Use BFS Instead

> author: m1 · team: shared · confidence: 0.89

## Description



## Bad example



## Good example



## Applies when

- canvas flood fill implementation
- large grid traversal

## Do NOT apply when

- small grids where stack depth safe

## Raw log

[./raw/m1-error-003.jsonl](./raw/m1-error-003.jsonl)
