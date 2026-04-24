---
{
  "id": "m1-kb-ah-006",
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
  "label_note": "\n- **Recording/Replay System**: Build with YAML scenario definitions + TypeScript executors + dual-mode report generation (static HTML + dynamic webapp)\n- **Webapp Testing Decision Tree**: Static HTML → direct reading → Playwright script; Dynamic → check if server running → with_server.py helper or侦察-然后-行动 pattern\n- **Test Video Evidence**: Use Playwright `recordVideo` API for capturing full test runs as evidence\n- **Parallel Agent Task Execution**: Create 10-task parallel agent execution for ra",
  "applies_when": [],
  "do_not_apply_when": []
}
---

# Actionable Insights

> author: m1 · confidence: 0.85


- **Recording/Replay System**: Build with YAML scenario definitions + TypeScript executors + dual-mode report generation (static HTML + dynamic webapp)
- **Webapp Testing Decision Tree**: Static HTML → direct reading → Playwright script; Dynamic → check if server running → with_server.py helper or侦察-然后-行动 pattern
- **Test Video Evidence**: Use Playwright `recordVideo` API for capturing full test runs as evidence
- **Parallel Agent Task Execution**: Create 10-task parallel agent execution for ra
