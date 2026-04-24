---
{
  "id": "m1-kb-am-003",
  "title": "Error Patterns",
  "author": "m1",
  "confidence": 0.85,
  "tags": [
    "knowledge-extraction",
    "session-analysis",
    "group_am"
  ],
  "status": "active",
  "topic_id": "m1-kb-am",
  "label": "good",
  "label_note": "\n### Language Rule Violations\n- English words in Chinese responses fail verification\n- Technical identifiers (filenames, paths, commands) are exempt\n- Generic English words like \"session\", \"mode\" are NOT exempt\n\n### Rate Limiting\n- Model: `<synthetic>` with 429 status\n- Message: \"You've hit your limit · resets 11pm (Asia/Shanghai)\"\n- Input tokens shown in usage statistics",
  "applies_when": [],
  "do_not_apply_when": []
}
---

# Error Patterns

> author: m1 · confidence: 0.85


### Language Rule Violations
- English words in Chinese responses fail verification
- Technical identifiers (filenames, paths, commands) are exempt
- Generic English words like "session", "mode" are NOT exempt

### Rate Limiting
- Model: `<synthetic>` with 429 status
- Message: "You've hit your limit · resets 11pm (Asia/Shanghai)"
- Input tokens shown in usage statistics
