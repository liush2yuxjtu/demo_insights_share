---
{
  "id": "m1-kb-ah-015",
  "title": "Error Patterns & Fixes",
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
  "label_note": "\n### CP6: MANIFEST.txt Missing\n- **Pattern**: `find release/final -type f` returns files but MANIFEST.txt absent\n- **Fix**: Generate with `du -sh` + file list; format: title + directory tree + summary + per-file paths\n- **Prohibited items scan**: `*.log | .env | .env.* | *.local | node_modules/__pycache__/ | *.pyc | .pytest_cache/ | .DS_Store | dist/build/ | *.egg-info/ | coverage/`\n\n### CP4: npm test Placeholder\n- **Pattern**: `\"test\": \"echo \\\"Error: no test specified\\\" && exit 1\"` in package.j",
  "applies_when": [],
  "do_not_apply_when": []
}
---

# Error Patterns & Fixes

> author: m1 · confidence: 0.85


### CP6: MANIFEST.txt Missing
- **Pattern**: `find release/final -type f` returns files but MANIFEST.txt absent
- **Fix**: Generate with `du -sh` + file list; format: title + directory tree + summary + per-file paths
- **Prohibited items scan**: `*.log | .env | .env.* | *.local | node_modules/__pycache__/ | *.pyc | .pytest_cache/ | .DS_Store | dist/build/ | *.egg-info/ | coverage/`

### CP4: npm test Placeholder
- **Pattern**: `"test": "echo \"Error: no test specified\" && exit 1"` in package.j
