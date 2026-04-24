---
{
  "id": "m1-kb-ah-011",
  "title": "Project-Specific Knowledge",
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
  "label_note": "\n### openclaw-plugin-testing-agent-sdk\n\n**Key Files:**\n- `claude_agent_sdk.py` — Python SDK for Claude Agent\n- `orchestrator.py` — 7-step workflow orchestrator\n- `prompt/*.md` — 8 prompt templates\n- `plugin-bench.py` — CLI performance benchmarker\n- `release/` — delivery artifacts\n\n**MiniMax Config:**\n```python\nDEFAULT_BASE_URL = \"https://api.minimaxi.com/anthropic\"\nDEFAULT_MODEL = \"MiniMax-M2.7-highspeed\"\n# ~10x cheaper than official Anthropic\n```\n\n**Sensor Example (8 total):**\n- S1: `python plu",
  "applies_when": [],
  "do_not_apply_when": []
}
---

# Project-Specific Knowledge

> author: m1 · confidence: 0.85


### openclaw-plugin-testing-agent-sdk

**Key Files:**
- `claude_agent_sdk.py` — Python SDK for Claude Agent
- `orchestrator.py` — 7-step workflow orchestrator
- `prompt/*.md` — 8 prompt templates
- `plugin-bench.py` — CLI performance benchmarker
- `release/` — delivery artifacts

**MiniMax Config:**
```python
DEFAULT_BASE_URL = "https://api.minimaxi.com/anthropic"
DEFAULT_MODEL = "MiniMax-M2.7-highspeed"
# ~10x cheaper than official Anthropic
```

**Sensor Example (8 total):**
- S1: `python plu
