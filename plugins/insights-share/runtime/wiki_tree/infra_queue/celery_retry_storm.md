---
{
  "id": "alice-celery-retry-2026-04-08",
  "title": "Celery retry storm overwhelming Redis broker",
  "author": "alice",
  "confidence": 0.88,
  "tags": [
    "celery",
    "retry",
    "redis",
    "backpressure",
    "prod-incident"
  ],
  "status": "active",
  "applies_when": [
    "celery>=5.0 with Redis broker",
    "task calls external API with transient failure modes",
    "workers share a single Redis instance with other services"
  ],
  "do_not_apply_when": [
    "tasks are strictly idempotent and must complete ASAP regardless of cost",
    "broker is RabbitMQ with native dead-letter exchange already configured",
    "downstream provides its own backpressure via 429 + Retry-After header that client already honors"
  ],
  "raw_log": "./raw/alice-celery-retry-2026-04-08.jsonl"
}
---

# Celery retry storm overwhelming Redis broker

> author: alice · confidence: 0.88

## Description

Celery 5.x workers with Redis as broker, default retry policy on a flaky downstream HTTP API

Default immediate retry without backoff caused thousands of failed tasks to re-enqueue instantly, amplifying load while the downstream was already degraded

## Bad example

Redis memory climbs to maxmemory within minutes; broker OOM-kills; queue backlog explodes; workers stuck in retry loop

## Good example

Enable retry_backoff=True with retry_backoff_max=600 and retry_jitter=True; cap max_retries=5; route exhausted tasks to a dead-letter queue; add a task_annotations rate_limit='20/s' on the hot task

## Applies when

- celery>=5.0 with Redis broker
- task calls external API with transient failure modes
- workers share a single Redis instance with other services

## Do NOT apply when

- tasks are strictly idempotent and must complete ASAP regardless of cost
- broker is RabbitMQ with native dead-letter exchange already configured
- downstream provides its own backpressure via 429 + Retry-After header that client already honors

## Raw log

[./raw/alice-celery-retry-2026-04-08.jsonl](./raw/alice-celery-retry-2026-04-08.jsonl)
