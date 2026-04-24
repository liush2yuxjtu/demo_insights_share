---
{
  "id": "m1-kb-ah-030",
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
  "label_note": "\n1. **Documentation centralization**: Consolidate hardcoded IPs/paths into `docs/config.md` — 48+ duplicate occurrences across project\n\n2. **HPC script transfer**: Always use base64 encoding for script transfer to avoid shell interpretation issues\n\n3. **CHARM workflow**: Remember tissue converter step (SimNIBS → MCX) required after CHARM segmentation completes\n\n4. **Job monitoring**: Use dual monitoring — `squeue` for job state + `find` for output file count\n\n5. **OpenSpec execute-real-ixi-wavea",
  "applies_when": [],
  "do_not_apply_when": []
}
---

# Actionable Insights

> author: m1 · confidence: 0.85


1. **Documentation centralization**: Consolidate hardcoded IPs/paths into `docs/config.md` — 48+ duplicate occurrences across project

2. **HPC script transfer**: Always use base64 encoding for script transfer to avoid shell interpretation issues

3. **CHARM workflow**: Remember tissue converter step (SimNIBS → MCX) required after CHARM segmentation completes

4. **Job monitoring**: Use dual monitoring — `squeue` for job state + `find` for output file count

5. **OpenSpec execute-real-ixi-wavea
