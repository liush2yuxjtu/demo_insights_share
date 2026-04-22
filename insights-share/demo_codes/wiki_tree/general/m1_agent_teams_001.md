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
  "raw_log_type": "jsonl",
  "raw_log_sha256": "e811985027d901634a240c267e87bbc6ac0c017c7c0a67c6279f4f40aa18c6f8",
  "signature_algorithm": "ed25519",
  "signature_schema": 1,
  "signature_key_id": "51e8985cd0e6105e",
  "signature": "ODchmtMK5DAUriDagHrIHVzSsw3gcXM3tPNP0DbGfaOipGR5H8pwYlT7tBm191GfxF+hMxZYk4AYKeO5anJfDw==",
  "signature_signed_at": "2026-04-22T08:22:23.510864+00:00"
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
