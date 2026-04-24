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
  "raw_log_type": "jsonl"
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
