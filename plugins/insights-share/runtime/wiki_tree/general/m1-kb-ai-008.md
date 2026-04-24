---
{
  "id": "m1-kb-ai-008",
  "title": "7. Verification Command Patterns",
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
  "label_note": "\n### 7.1 File Existence + Size\n\n```bash\nls -la index.html\nwc -c index.html  # ≤ 30720 for 30KB gate\n```\n\n### 7.2 JS Syntax in Inline Scripts\n\n```bash\nnode -e \"\nconst fs = require('fs');\nconst html = fs.readFileSync('index.html', 'utf8');\nconst scripts = html.match(/<script[^>]*>([\\\\s\\\\S]*?)<\\\\/script>/gi) || [];\nlet ok = true;\nscripts.forEach((s, i) => {\n  const src = s.match(/src=\\\\\\\"([^\\\\\\\"]+)\\\\\\\"/);\n  if (!src) {\n    const code = s.replace(/<script[^>]*>/, '').replace(/<\\\\/script>/i, '');\n   ",
  "applies_when": [],
  "do_not_apply_when": []
}
---

# 7. Verification Command Patterns

> author: m1 · confidence: 0.85


### 7.1 File Existence + Size

```bash
ls -la index.html
wc -c index.html  # ≤ 30720 for 30KB gate
```

### 7.2 JS Syntax in Inline Scripts

```bash
node -e "
const fs = require('fs');
const html = fs.readFileSync('index.html', 'utf8');
const scripts = html.match(/<script[^>]*>([\\s\\S]*?)<\\/script>/gi) || [];
let ok = true;
scripts.forEach((s, i) => {
  const src = s.match(/src=\\\"([^\\\"]+)\\\"/);
  if (!src) {
    const code = s.replace(/<script[^>]*>/, '').replace(/<\\/script>/i, '');
