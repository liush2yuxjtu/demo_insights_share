---
{
  "id": "m1-kb-ah-008",
  "title": "Technical Findings & Patterns",
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
  "label_note": "\n### OpenClaw Plugin Architecture\n\n**Plugin Structure:**\n```\nmy-plugin/\n├── .claude-plugin/\n│   └── plugin.json\n├── skills/\n├── agents/\n├── hooks/\n└── .mcp.json\n```\n\n**Entry Point Pattern:**\n```typescript\nexport default definePluginEntry({\n  id: 'testing-loop-plugin',\n  name: 'Testing Loop Plugin',\n  version: '0.1.0',\n  register(api) {\n    api.registerService({ id: '...', name: '...', start(), stop() })\n    api.registerTool({ name: '...', description: '...', parameters: {...}, async execute() {}",
  "applies_when": [],
  "do_not_apply_when": []
}
---

# Technical Findings & Patterns

> author: m1 · confidence: 0.85


### OpenClaw Plugin Architecture

**Plugin Structure:**
```
my-plugin/
├── .claude-plugin/
│   └── plugin.json
├── skills/
├── agents/
├── hooks/
└── .mcp.json
```

**Entry Point Pattern:**
```typescript
export default definePluginEntry({
  id: 'testing-loop-plugin',
  name: 'Testing Loop Plugin',
  version: '0.1.0',
  register(api) {
    api.registerService({ id: '...', name: '...', start(), stop() })
    api.registerTool({ name: '...', description: '...', parameters: {...}, async execute() {}
