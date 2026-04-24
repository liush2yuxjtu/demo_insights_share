---
{
  "id": "m1-kb-ah-014",
  "title": "Technical Findings & Patterns",
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
  "label_note": "\n### Orchestrator Agent Workflow (Meta + Coding Pattern)\n- **Control loop**: 7-step main loop + 1 post-loop final release\n- **Meta agent**: designs spec (sensor + evidence), arbitrates WORKDONE, cleans temp files\n- **Coding agent**: implements features, runs self-tests, produces evidence\n- **Version iteration**: v1 → v2 → v3... until WORKDONE: true\n- **Timestamp convention**: `{YYYYMMDD}_{HHMMSS}`\n- **Tool split**: Coding has Edit/Write/Bash/Glob/Grep; Meta has only Read/Bash/Write/Glob/Grep (no",
  "applies_when": [],
  "do_not_apply_when": []
}
---

# Technical Findings & Patterns

> author: m1 · confidence: 0.85


### Orchestrator Agent Workflow (Meta + Coding Pattern)
- **Control loop**: 7-step main loop + 1 post-loop final release
- **Meta agent**: designs spec (sensor + evidence), arbitrates WORKDONE, cleans temp files
- **Coding agent**: implements features, runs self-tests, produces evidence
- **Version iteration**: v1 → v2 → v3... until WORKDONE: true
- **Timestamp convention**: `{YYYYMMDD}_{HHMMSS}`
- **Tool split**: Coding has Edit/Write/Bash/Glob/Grep; Meta has only Read/Bash/Write/Glob/Grep (no
