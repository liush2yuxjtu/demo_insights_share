---
{
  "id": "m1-kb-ai-003",
  "title": "2. Error Patterns & Fixes",
  "author": "m1",
  "confidence": 0.85,
  "tags": [
    "knowledge-extraction",
    "session-analysis",
    "group_ai"
  ],
  "status": "active",
  "topic_id": "m1-kb-ai",
  "label": "good",
  "label_note": "\n### 2.1 Flood Fill Algorithm (Iterative vs Recursive)\n\n**Problem**: Recursive flood fill in JS causes stack overflow on large canvases (32×32+).\n\n**Fix**: Use iterative queue/stack-based algorithm with visited pixel marker array.\n\n### 2.2 localStorage Quota / Disabled Storage\n\n**Problem**: localStorage blocked in private mode or quota exceeded.\n\n**Fix**: Wrap all `localStorage` calls in `try/catch`, silently fallback to default value.\n\n```javascript\nlet count = 0;\ntry {\n  const stored = localSt",
  "applies_when": [],
  "do_not_apply_when": []
}
---

# 2. Error Patterns & Fixes

> author: m1 · confidence: 0.85


### 2.1 Flood Fill Algorithm (Iterative vs Recursive)

**Problem**: Recursive flood fill in JS causes stack overflow on large canvases (32×32+).

**Fix**: Use iterative queue/stack-based algorithm with visited pixel marker array.

### 2.2 localStorage Quota / Disabled Storage

**Problem**: localStorage blocked in private mode or quota exceeded.

**Fix**: Wrap all `localStorage` calls in `try/catch`, silently fallback to default value.

```javascript
let count = 0;
try {
  const stored = localSt
