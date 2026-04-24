---
{
  "id": "m1-kb-am-002",
  "title": "Patterns",
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
  "label_note": "\n### JSONL Message Types\n- `queue-operation`: enqueue/dequeue operations\n- `permission-mode`: permission configuration\n- `hook_success` / `hook_additional_context`: hook event attachments\n- `skill_listing`: initial skill inventory\n- `file-history-snapshot`: tracked file changes\n- `last-prompt`: final prompt storage\n\n### Session Entry Points\n- `sdk-cli`: SDK CLI interface\n- `cli`: command-line interface\n- `sdk-cli` with `bypassPermissions` mode\n\n### Working Directory Patterns\n- Primary: `/Users/m",
  "applies_when": [],
  "do_not_apply_when": []
}
---

# Patterns

> author: m1 · confidence: 0.85


### JSONL Message Types
- `queue-operation`: enqueue/dequeue operations
- `permission-mode`: permission configuration
- `hook_success` / `hook_additional_context`: hook event attachments
- `skill_listing`: initial skill inventory
- `file-history-snapshot`: tracked file changes
- `last-prompt`: final prompt storage

### Session Entry Points
- `sdk-cli`: SDK CLI interface
- `cli`: command-line interface
- `sdk-cli` with `bypassPermissions` mode

### Working Directory Patterns
- Primary: `/Users/m
