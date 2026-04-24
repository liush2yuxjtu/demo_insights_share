---
{
  "id": "m1-kb-ah-017",
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
  "label_note": "\n### openclaw-plugin-testing-agent-sdk Project Structure\n```\n├── orchestrator.py              # 7+1 loop implementation (Python)\n├── claude_agent_sdk.py          # MiniMax API SDK (~700 lines)\n├── plugin-bench.py              # Module 1: performance benchmarker\n├── plugin-recorder.py           # Module 2: recording & replay system\n├── proposal.md                  # 背景/目标/范围/验收标准\n├── validation.md                # v2 spec (WORKDONE: true)\n├── control.md                   # Orchestrator workflow s",
  "applies_when": [],
  "do_not_apply_when": []
}
---

# Project-Specific Knowledge

> author: m1 · confidence: 0.85


### openclaw-plugin-testing-agent-sdk Project Structure
```
├── orchestrator.py              # 7+1 loop implementation (Python)
├── claude_agent_sdk.py          # MiniMax API SDK (~700 lines)
├── plugin-bench.py              # Module 1: performance benchmarker
├── plugin-recorder.py           # Module 2: recording & replay system
├── proposal.md                  # 背景/目标/范围/验收标准
├── validation.md                # v2 spec (WORKDONE: true)
├── control.md                   # Orchestrator workflow s
