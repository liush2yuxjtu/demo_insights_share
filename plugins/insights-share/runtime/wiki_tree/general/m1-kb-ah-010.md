---
{
  "id": "m1-kb-ah-010",
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
  "label_note": "\n### Vitest\n```bash\npnpm test                    # Unit/Integration\npnpm test:e2e               # Multi-instance gateway\npnpm test:live              # Real API providers\npnpm test:docker:*          # Container isolation\npnpm test:contracts         # Interface compliance\n```\n\n### Playwright\n```bash\npython -m http.server 3000 --directory release/v2/src\nnpx playwright test tests/playwright/demo_video.spec.ts\npkill -f chromium           # cleanup\n```\n\n### Claude Code\n```bash\n/model sonnet           ",
  "applies_when": [],
  "do_not_apply_when": []
}
---

# CLI Commands & Tools

> author: m1 · confidence: 0.85


### Vitest
```bash
pnpm test                    # Unit/Integration
pnpm test:e2e               # Multi-instance gateway
pnpm test:live              # Real API providers
pnpm test:docker:*          # Container isolation
pnpm test:contracts         # Interface compliance
```

### Playwright
```bash
python -m http.server 3000 --directory release/v2/src
npx playwright test tests/playwright/demo_video.spec.ts
pkill -f chromium           # cleanup
```

### Claude Code
```bash
/model sonnet
