---
{
  "id": "m1-kb-ac-004",
  "title": "Error Patterns",
  "author": "m1",
  "confidence": 0.85,
  "tags": [
    "knowledge-extraction",
    "session-analysis",
    "group_ac"
  ],
  "status": "active",
  "topic_id": "m1-kb-ac",
  "label": "good",
  "label_note": "\n- The command was cancelled due to parallel tool call error. Let me try again with correct path.\n- The baseline experiment failed with exit code 2. Let me check the run.log to see what went wrong.\n- Line 109 also has a CUDA-specific call that will fail on CPU. Let me fix that too.\n- I see there are also HPC related files. Let me read those and then make atomic commits. I should organize commits logically:  1. Initial commit - AGENTS.md (main agent specification) 2. Core rules (se\n- Now I have a",
  "applies_when": [],
  "do_not_apply_when": []
}
---

# Error Patterns

> author: m1 · confidence: 0.85


- The command was cancelled due to parallel tool call error. Let me try again with correct path.
- The baseline experiment failed with exit code 2. Let me check the run.log to see what went wrong.
- Line 109 also has a CUDA-specific call that will fail on CPU. Let me fix that too.
- I see there are also HPC related files. Let me read those and then make atomic commits. I should organize commits logically:  1. Initial commit - AGENTS.md (main agent specification) 2. Core rules (se
- Now I have a
