---
{
  "id": "m1-kb-ah-009",
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
  "label_note": "\n### API Compatibility Issues\n\n**MiniMax streaming API incompatibility:**\n- Problem: `InputJSONDelta` field is `partial_json` not `input_json`, no id\n- Fix: Track current tool from `tool_use_start` events\n- Workaround: Use non-streaming `messages.create`\n\n**Tool use block input empty:**\n- Problem: `input_json_delta` events accumulate but format differs\n- Fix: Accumulate from `tool_use_start` with proper ID tracking\n\n### Python SDK `get_final_message()` Issue\n- Problem: `get_final_message()` is c",
  "applies_when": [],
  "do_not_apply_when": []
}
---

# Error Patterns & Fixes

> author: m1 · confidence: 0.85


### API Compatibility Issues

**MiniMax streaming API incompatibility:**
- Problem: `InputJSONDelta` field is `partial_json` not `input_json`, no id
- Fix: Track current tool from `tool_use_start` events
- Workaround: Use non-streaming `messages.create`

**Tool use block input empty:**
- Problem: `input_json_delta` events accumulate but format differs
- Fix: Accumulate from `tool_use_start` with proper ID tracking

### Python SDK `get_final_message()` Issue
- Problem: `get_final_message()` is c
