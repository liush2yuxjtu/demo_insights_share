---
{
  "id": "m1-kb-ap-003",
  "title": "2. Error Patterns & Fixes",
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
  "label_note": "\n### 2.1 Hookify Rule Non-Activation\n\n**Problem:** `hookify` rules defined but not triggering.\n\n**Diagnosis approach:**\n1. Check `~/.claude/settings.json` for hook configuration\n2. Verify hook event name matches (e.g., `SessionStart`, `UserPromptSubmit`)\n3. Run `/hookify-list` to see active rules\n4. Use `/hookify-help` for troubleshooting\n\n### 2.2 Skill Not Visible in `$` List\n\n**Problem:** Skill path exists but not discovered by Codex.\n\n**Fix sequence:**\n1. Check `SKILL.md` frontmatter has `nam",
  "applies_when": [],
  "do_not_apply_when": []
}
---

# 2. Error Patterns & Fixes

> author: m1 · confidence: 0.85


### 2.1 Hookify Rule Non-Activation

**Problem:** `hookify` rules defined but not triggering.

**Diagnosis approach:**
1. Check `~/.claude/settings.json` for hook configuration
2. Verify hook event name matches (e.g., `SessionStart`, `UserPromptSubmit`)
3. Run `/hookify-list` to see active rules
4. Use `/hookify-help` for troubleshooting

### 2.2 Skill Not Visible in `$` List

**Problem:** Skill path exists but not discovered by Codex.

**Fix sequence:**
1. Check `SKILL.md` frontmatter has `nam
