---
{
  "id": "m1-kb-ah-004",
  "title": "CLI Commands & Tools",
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
  "label_note": "\n- **Git Tagging**: `git tag -a v1.0.0 -m \"message\"` for semantic versioning releases\n- **Playwright Screenshot**: `page.screenshot({ path: 'full.png', fullPage: true })` for full page; `page.locator('.selector').screenshot()` for elements\n- **Playwright Video Recording**: `browser.newContext({ recordVideo: { dir: './videos/', size: { width: 1920, height: 1080 } } })`\n- **Playwright PDF**: `page.pdf({ path: 'page.pdf', format: 'A4', printBackground: true })` (Chromium only)\n- **Multi-Server Test",
  "applies_when": [],
  "do_not_apply_when": []
}
---

# CLI Commands & Tools

> author: m1 · confidence: 0.85


- **Git Tagging**: `git tag -a v1.0.0 -m "message"` for semantic versioning releases
- **Playwright Screenshot**: `page.screenshot({ path: 'full.png', fullPage: true })` for full page; `page.locator('.selector').screenshot()` for elements
- **Playwright Video Recording**: `browser.newContext({ recordVideo: { dir: './videos/', size: { width: 1920, height: 1080 } } })`
- **Playwright PDF**: `page.pdf({ path: 'page.pdf', format: 'A4', printBackground: true })` (Chromium only)
- **Multi-Server Test
