---
{
  "id": "m1-agent-teams-001",
  "title": "Agent Teams KEEP/RESET Verifier Logic",
  "author": "m1",
  "team": null,
  "confidence": 0.92,
  "tags": [
    "agent-teams",
    "verifier",
    "KEEP-RESET",
    "quality-gate"
  ],
  "status": "active",
  "applies_when": [
    "evaluating builder output with agent teams",
    "quality gate in harness"
  ],
  "do_not_apply_when": [
    "simple single-shot tasks",
    "research-only prompts"
  ],
  "raw_log": "./raw/m1-agent-teams-001.jsonl",
  "topic_id": "agent-teams",
  "label": "good",
  "label_note": "KEEP=all conditions met, RESET=any failed+exception+drift",
  "label_override": null,
  "label_override_by": null,
  "label_override_at": null,
  "raw_log_type": "jsonl"
}
---

# Agent Teams KEEP/RESET Verifier Logic

> author: m1 · team: shared · confidence: 0.92

## Description



## Bad example



## Good example



## Applies when

- evaluating builder output with agent teams
- quality gate in harness

## Do NOT apply when

- simple single-shot tasks
- research-only prompts

## Raw log

[./raw/m1-agent-teams-001.jsonl](./raw/m1-agent-teams-001.jsonl)
