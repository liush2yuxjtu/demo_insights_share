---
{
  "id": "m1-kb-ah-027",
  "title": "Error Patterns & Fixes",
  "author": "m1",
  "confidence": 0.85,
  "tags": [
    "knowledge-extraction",
    "session-analysis",
    "group_ah"
  ],
  "status": "active",
  "topic_id": "m1-kb-ah",
  "label": "good",
  "label_note": "\n| Error | Cause | Fix |\n|-------|-------|-----|\n| `InvalidAccount` | SLURM waiting for resources, not actual error | Normal behavior, job will start when resources available |\n| `charm_simple.py` import error | Python module path issue | Use binary: `/data/home/syliu/.conda/envs/simnibs/bin/charm` |\n| `%30` throttle syntax causes `InvalidAccount` | Array throttle syntax interpreted incorrectly | Remove throttle, submit directly |\n| Shell interpretation during script transfer | Special character",
  "applies_when": [],
  "do_not_apply_when": []
}
---

# Error Patterns & Fixes

> author: m1 · confidence: 0.85


| Error | Cause | Fix |
|-------|-------|-----|
| `InvalidAccount` | SLURM waiting for resources, not actual error | Normal behavior, job will start when resources available |
| `charm_simple.py` import error | Python module path issue | Use binary: `/data/home/syliu/.conda/envs/simnibs/bin/charm` |
| `%30` throttle syntax causes `InvalidAccount` | Array throttle syntax interpreted incorrectly | Remove throttle, submit directly |
| Shell interpretation during script transfer | Special character
