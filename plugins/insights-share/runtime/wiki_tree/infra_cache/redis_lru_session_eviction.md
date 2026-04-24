---
{
  "id": "carol-redis-eviction-2026-03-27",
  "title": "Redis allkeys-lru silently evicting hot session data",
  "author": "carol",
  "confidence": 0.9,
  "tags": [
    "redis",
    "eviction",
    "session-store",
    "maxmemory",
    "prod-incident"
  ],
  "status": "active",
  "applies_when": [
    "single Redis instance shared across session-store and cache workloads",
    "maxmemory-policy is allkeys-* (lru/lfu/random)",
    "session keys are written without TTL or with very long TTL"
  ],
  "do_not_apply_when": [
    "sessions are already stored in a separate datastore (e.g., dedicated Redis or Postgres)",
    "all keys carry TTL and application explicitly tolerates session loss",
    "Redis is used purely as a volatile cache with no durability expectations"
  ],
  "raw_log": "./raw/carol-redis-eviction-2026-03-27.jsonl"
}
---

# Redis allkeys-lru silently evicting hot session data

> author: carol · confidence: 0.9

## Description

Single Redis 7.x instance shared by session store, cache layer, and rate-limiter counters; maxmemory=4gb with maxmemory-policy=allkeys-lru

allkeys-lru treats session keys and disposable cache entries equally, so a burst of cache writes evicts live sessions that happen to be less recently touched

## Bad example

Users randomly logged out mid-session; auth service reports 'session not found' for keys that were written minutes ago; eviction metric spikes during cache warm-up jobs

## Good example

Move sessions to a dedicated Redis instance (or a separate logical DB with its own memory budget); on the shared instance switch policy to volatile-lru and set TTL only on cache keys so sessions (untagged) are never eligible for eviction

## Applies when

- single Redis instance shared across session-store and cache workloads
- maxmemory-policy is allkeys-* (lru/lfu/random)
- session keys are written without TTL or with very long TTL

## Do NOT apply when

- sessions are already stored in a separate datastore (e.g., dedicated Redis or Postgres)
- all keys carry TTL and application explicitly tolerates session loss
- Redis is used purely as a volatile cache with no durability expectations

## Raw log

[./raw/carol-redis-eviction-2026-03-27.jsonl](./raw/carol-redis-eviction-2026-03-27.jsonl)
