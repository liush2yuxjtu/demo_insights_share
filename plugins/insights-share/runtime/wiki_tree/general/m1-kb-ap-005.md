---
{
  "id": "m1-kb-ap-005",
  "title": "4. Project-Specific Knowledge",
  "author": "m1",
  "confidence": 0.85,
  "tags": [
    "knowledge-extraction",
    "session-analysis",
    "group_ap"
  ],
  "status": "active",
  "topic_id": "m1-kb-ap",
  "label": "good",
  "label_note": "\n### 4.1 Claude Code Plugin Development\n\n**Project structure for plugins:**\n- `plugins/<name>/` — plugin root\n- `plugin.json` — plugin manifest\n- `skills/` — skill definitions\n- `hooks/` — hook scripts\n- `commands/` — slash commands\n\n**Key files:**\n- `settings.json` — CLI configuration, permissions, hooks\n- `settings.local.json` — local overrides\n\n### 4.2 Boris Workflow (ML Research Pipeline)\n\n**3-phase flow:**\n1. **Research** — parallel agent exploration → `/tmp/<topic>/research_*.md` → fused i",
  "applies_when": [],
  "do_not_apply_when": []
}
---

# 4. Project-Specific Knowledge

> author: m1 · confidence: 0.85


### 4.1 Claude Code Plugin Development

**Project structure for plugins:**
- `plugins/<name>/` — plugin root
- `plugin.json` — plugin manifest
- `skills/` — skill definitions
- `hooks/` — hook scripts
- `commands/` — slash commands

**Key files:**
- `settings.json` — CLI configuration, permissions, hooks
- `settings.local.json` — local overrides

### 4.2 Boris Workflow (ML Research Pipeline)

**3-phase flow:**
1. **Research** — parallel agent exploration → `/tmp/<topic>/research_*.md` → fused i
