---
{
  "id": "alice-pgpool-2026-04-10",
  "title": "PostgreSQL pool exhaustion under burst traffic",
  "author": "alice",
  "team": null,
  "confidence": 0.99,
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
  "label_note": "admin summary revision",
  "label_override": "bad",
  "label_override_by": "admin_team6",
  "label_override_at": "2026-04-22T09:25:27.843281+00:00",
  "raw_log_type": "jsonl",
  "raw_log_sha256": "6eade75c2b07501714a27503529ac66b244d2e0654b215db4e2b55f278b35ecd",
  "signature_algorithm": "ed25519",
  "signature_schema": 1,
  "signature_key_id": "51e8985cd0e6105e",
  "signature": "RP6F4iCn0TNl0z8klYzblV0KKQYi1wip+3XCpnq7vhVq2RN+k5fyMNVsqCb2pptRW59RPiRn0EcyEsZjhDxSCQ==",
  "signature_signed_at": "2026-04-22T09:25:27.995306+00:00"
}
---

# PostgreSQL pool exhaustion under burst traffic

> author: alice · team: shared · confidence: 0.99

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
