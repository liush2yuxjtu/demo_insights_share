---
{
  "id": "m1-kb-ai-004",
  "title": "3. CLI Commands & Tools",
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
  "label_note": "\n### 3.1 Playwright (Browser Automation)\n\n```bash\n# Check if Playwright is available\npx playwright test --version\n\n# Install Playwright with Chromium\nnpx playwright install --with-deps chromium\n\n# Run tests\npx playwright test\n```\n\n```javascript\n// Page load + console error check\nconst { chromium } = require('playwright');\n(async () => {\n  const browser = await chromium.launch();\n  const page = await browser.newPage();\n  const errors = [];\n  page.on('console', msg => { if (msg.type() === 'error')",
  "applies_when": [],
  "do_not_apply_when": []
}
---

# 3. CLI Commands & Tools

> author: m1 · confidence: 0.85


### 3.1 Playwright (Browser Automation)

```bash
# Check if Playwright is available
px playwright test --version

# Install Playwright with Chromium
npx playwright install --with-deps chromium

# Run tests
px playwright test
```

```javascript
// Page load + console error check
const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  const errors = [];
  page.on('console', msg => { if (msg.type() === 'error')
