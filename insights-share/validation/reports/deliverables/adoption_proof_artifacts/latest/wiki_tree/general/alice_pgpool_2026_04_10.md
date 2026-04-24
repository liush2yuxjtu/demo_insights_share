---
{
  "id": "alice-pgpool-2026-04-10",
  "title": "PostgreSQL pool exhaustion under burst traffic",
  "author": "alice",
  "team": null,
  "confidence": 0.82,
  "tags": [
    "postgres",
    "connection-pool",
    "latency",
    "prod-incident"
  ],
  "status": "active",
  "applies_when": [
    "postgres>=13",
    "pgbouncer transaction mode"
  ],
  "do_not_apply_when": [
    "session pooling mode",
    "single-tenant DB"
  ],
  "raw_log": "./raw/alice-pgpool-2026-04-10.jsonl",
  "topic_id": "postgres-pool-exhaustion",
  "label": "good",
  "label_note": "在 PgBouncer transaction mode 下彻底解决",
  "label_override": null,
  "label_override_by": null,
  "label_override_at": null,
  "raw_log_type": "jsonl",
  "raw_log_sha256": "ae811fe679e8072aadcc7b660bf6fed0a20ed4b079f49eaf8f1519607ddc8691",
  "signature_algorithm": "ed25519",
  "signature_schema": 1,
  "signature_key_id": "0a04b381e86417e8",
  "signature": "LE6xit7J6R8IuaUtn/IjOJ73iCSxsg4BtlJLHGd5c+2CG9SWq7Qw1Qp7fceNPoscQ8OFciZBS42uKm0kzngMDA==",
  "signature_signed_at": "2026-04-24T05:20:43.788415+00:00"
}
---

# PostgreSQL pool exhaustion under burst traffic

> author: alice · team: shared · confidence: 0.82

## Description

API tier behind PgBouncer, transaction pooling mode

Long-lived idle txns held by a misbehaving worker

## Bad example

p99 latency spikes; 'remaining connection slots reserved'

## Good example

Set idle_in_transaction_session_timeout=30s and bump pool size to 2x worker count

## Applies when

- postgres>=13
- pgbouncer transaction mode

## Do NOT apply when

- session pooling mode
- single-tenant DB

## Raw log

[./raw/alice-pgpool-2026-04-10.jsonl](./raw/alice-pgpool-2026-04-10.jsonl)
