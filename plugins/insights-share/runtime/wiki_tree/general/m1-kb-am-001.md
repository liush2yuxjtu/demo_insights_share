---
{
  "id": "m1-kb-am-001",
  "title": "Technical Findings",
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
  "label_note": "\n### Session Management\n- Session IDs use UUID format (e.g., `efcce768-8eed-41a5-9bee-021285cae0a0`)\n- Sessions store context in JSONL format with message objects\n- Subagents store their sessions in `subagents/` subdirectory\n- File history snapshots track changes during session (`file-history-snapshot` type)\n\n### Communication Language Verification\n- Language rules enforcement: Chinese (中文) is the required communication language\n- Violations include: English words like \"session\", \"caveman mode\" ",
  "applies_when": [],
  "do_not_apply_when": []
}
---

# Technical Findings

> author: m1 · confidence: 0.85


### Session Management
- Session IDs use UUID format (e.g., `efcce768-8eed-41a5-9bee-021285cae0a0`)
- Sessions store context in JSONL format with message objects
- Subagents store their sessions in `subagents/` subdirectory
- File history snapshots track changes during session (`file-history-snapshot` type)

### Communication Language Verification
- Language rules enforcement: Chinese (中文) is the required communication language
- Violations include: English words like "session", "caveman mode"
