---
{
  "id": "m1-kb-ah-016",
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
  "label_note": "\n### claim-finish Validation\n```bash\n# CP4: Probe test framework\nnpx vitest run                    # Node/TypeScript\npytest -v --tb=short             # Python\ngo test ./... -v -coverprofile=  # Go\nmake test                         # Makefile\n\n# CP7: Playwright discover\nnpx playwright test --list      # Must pass\n\n# CP6: Release package\nfind release/final -type f       # List files\ndu -sh release/final             # Package size\n\n# CP8: Config check\ngrep -E \"video|screenshot\" playwright.config.ts",
  "applies_when": [],
  "do_not_apply_when": []
}
---

# CLI Commands & Tools

> author: m1 · confidence: 0.85


### claim-finish Validation
```bash
# CP4: Probe test framework
npx vitest run                    # Node/TypeScript
pytest -v --tb=short             # Python
go test ./... -v -coverprofile=  # Go
make test                         # Makefile

# CP7: Playwright discover
npx playwright test --list      # Must pass

# CP6: Release package
find release/final -type f       # List files
du -sh release/final             # Package size

# CP8: Config check
grep -E "video|screenshot" playwright.config.ts
