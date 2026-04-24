---
{
  "id": "m1-kb-am-007",
  "title": "Actionable Insights",
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
  "label_note": "\n1. **Language Verification**: Use `claudefast -p` probes with JSON verdict output for automated rule checking\n2. **Caveman Mode**: Effective for token reduction, auto-triggers on \"be brief\" or \"less tokens\"\n3. **Session Context**: UUID-based sessions allow parallel agent workflows\n4. **Hooks**: SessionStart and UserPromptSubmit hooks provide extensibility\n5. **Rate Limits**: Plan around 11pm Asia/Shanghai reset for intensive tasks\n6. **Subagents**: Parent-child session relationships via `parent",
  "applies_when": [],
  "do_not_apply_when": []
}
---

# Actionable Insights

> author: m1 · confidence: 0.85


1. **Language Verification**: Use `claudefast -p` probes with JSON verdict output for automated rule checking
2. **Caveman Mode**: Effective for token reduction, auto-triggers on "be brief" or "less tokens"
3. **Session Context**: UUID-based sessions allow parallel agent workflows
4. **Hooks**: SessionStart and UserPromptSubmit hooks provide extensibility
5. **Rate Limits**: Plan around 11pm Asia/Shanghai reset for intensive tasks
6. **Subagents**: Parent-child session relationships via `parent
