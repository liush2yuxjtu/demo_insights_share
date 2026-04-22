---
{
  "id": "m1-agent-teams-003",
  "title": "TIMEOUT_LOG: Graceful Agent Shutdown Protocol",
  "author": "m1",
  "team": null,
  "confidence": 0.88,
  "tags": [
    "agent-teams",
    "timeout",
    "shutdown",
    "TIMEOUT_LOG"
  ],
  "status": "active",
  "applies_when": [
    "agent timeout during long tasks",
    "graceful degradation"
  ],
  "do_not_apply_when": [
    "fast tasks unlikely to timeout"
  ],
  "raw_log": "./raw/m1-agent-teams-003.jsonl",
  "topic_id": "agent-teams",
  "label": "good",
  "label_note": "Write TIMEOUT_LOG -> send shutdown_request -> team lead resets",
  "label_override": null,
  "label_override_by": null,
  "label_override_at": null,
  "raw_log_type": "jsonl",
  "raw_log_sha256": "e97b23d4245f2a2973a680bf2eaca37359ebf0d1d57a7b1a4b92aae705b5ce4c",
  "signature_algorithm": "ed25519",
  "signature_schema": 1,
  "signature_key_id": "51e8985cd0e6105e",
  "signature": "VdsEbDpKRn8m72GeojrTgZVEhQR6GsFaDpEyzOJPMxMbJafupPib4vAXVl8ErmGPCk8hIBRhPQPxMqdy8wFdAA==",
  "signature_signed_at": "2026-04-22T08:22:23.539733+00:00"
}
---

# TIMEOUT_LOG: Graceful Agent Shutdown Protocol

> author: m1 · team: shared · confidence: 0.88

## Description



## Bad example



## Good example



## Applies when

- agent timeout during long tasks
- graceful degradation

## Do NOT apply when

- fast tasks unlikely to timeout

## Raw log

[./raw/m1-agent-teams-003.jsonl](./raw/m1-agent-teams-003.jsonl)
