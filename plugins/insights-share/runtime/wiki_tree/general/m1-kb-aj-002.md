---
{
  "id": "m1-kb-aj-002",
  "title": "Patterns & Solutions",
  "author": "m1",
  "confidence": 0.85,
  "tags": [
    "knowledge-extraction",
    "session-analysis",
    "group_aj"
  ],
  "status": "active",
  "topic_id": "m1-kb-aj",
  "label": "good",
  "label_note": "\n- Multi-agent team with subagents for parallel work\n- Hookify plugin uses markdown rule files (.claude/hookify.*.local.md) instead of hooks.json\n- Claude Code plugin system: SessionStart (agent), PreToolUse (command), Stop (prompt) hooks\n- Prompt-based hooks: only approve/block, cannot modify output\n- SessionStart agent hook reads AGENTS.md, research.md, git logs for context\n- PreToolUse hook blocks git commit on protected files without valid pass marker\n- Stop hook enforces ASCII art presence ",
  "applies_when": [],
  "do_not_apply_when": []
}
---

# Patterns & Solutions

> author: m1 · confidence: 0.85


- Multi-agent team with subagents for parallel work
- Hookify plugin uses markdown rule files (.claude/hookify.*.local.md) instead of hooks.json
- Claude Code plugin system: SessionStart (agent), PreToolUse (command), Stop (prompt) hooks
- Prompt-based hooks: only approve/block, cannot modify output
- SessionStart agent hook reads AGENTS.md, research.md, git logs for context
- PreToolUse hook blocks git commit on protected files without valid pass marker
- Stop hook enforces ASCII art presence
