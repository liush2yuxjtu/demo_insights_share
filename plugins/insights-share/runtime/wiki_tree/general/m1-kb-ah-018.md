---
{
  "id": "m1-kb-ah-018",
  "title": "Actionable Insights",
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
  "label_note": "\n### Orchestrator Design\n1. **Tool separation matters**: Meta agent without Edit prevents accidental spec modifications\n2. **Directory isolation via .claudeignore**: Critical for clean agent 视野\n3. **Prompt外置**: All Step prompts in `prompt/*.md` with `${VAR}` template substitution\n4. **Version + timestamp**: Both needed for disambiguation across iterations\n\n### claim-finish Checkpoint Strategy\n1. **Hard blocks first**: CP1/CP2/CP3/CP5/CP6/CP7 must all PASS before overall PASS\n2. **MANIFEST.txt fo",
  "applies_when": [],
  "do_not_apply_when": []
}
---

# Actionable Insights

> author: m1 · confidence: 0.85


### Orchestrator Design
1. **Tool separation matters**: Meta agent without Edit prevents accidental spec modifications
2. **Directory isolation via .claudeignore**: Critical for clean agent 视野
3. **Prompt外置**: All Step prompts in `prompt/*.md` with `${VAR}` template substitution
4. **Version + timestamp**: Both needed for disambiguation across iterations

### claim-finish Checkpoint Strategy
1. **Hard blocks first**: CP1/CP2/CP3/CP5/CP6/CP7 must all PASS before overall PASS
2. **MANIFEST.txt fo
