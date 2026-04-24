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
  "raw_log_type": "jsonl"
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
