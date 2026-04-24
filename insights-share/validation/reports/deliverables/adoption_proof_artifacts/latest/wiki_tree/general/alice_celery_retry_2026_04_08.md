---
{
  "id": "alice-celery-retry-2026-04-08",
  "title": "Celery retry storm overwhelming Redis broker",
  "author": "alice",
  "team": null,
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
  "raw_log": "./raw/alice-celery-retry-2026-04-08.jsonl",
  "topic_id": "celery-retry-storm",
  "label": "good",
  "label_note": "",
  "label_override": null,
  "label_override_by": null,
  "label_override_at": null,
  "raw_log_type": "jsonl",
  "raw_log_sha256": "e05d2b8bafcb04b294a70dea5339fb40f1d45c6a8ec0f6258049422a2748b86b",
  "signature_algorithm": "ed25519",
  "signature_schema": 1,
  "signature_key_id": "3afab5a263e4b883",
  "signature": "X5kVkuyIMAnNJsxEh/CMT3RQ1QUbjVAj1TW0NieRbp1gk2yJ96HEwqUDfNkoG3hoP6HFF+tXaC2LmhQ0j9LTDA==",
  "signature_signed_at": "2026-04-24T05:23:22.944074+00:00"
}
---

# Celery retry storm overwhelming Redis broker

> author: alice · team: shared · confidence: 0.88

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
