---
{
  "id": "m1-kb-ah-022",
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
  "label_note": "\n### Zotero\n```bash\n# Zotero MCP fallback\nGET https://api.zotero.org/users/{user_id}/collections/{collection_key}/items?format=bibtex\nGET https://api.crossref.org/works/{DOI}\n```\n\n### 系统进程\n```bash\n# 杀 runaway codex\npkill -9 -f \"codex-darwin-arm64/vendor.*codex\"\nkill -9 <pid>\nps -Ao pid,pcpu,comm -r | head -5\n\n# Paperclip\n./node_modules/.bin/paperclipai\nnpx paperclipai\n```\n\n### GPU/ML\n```bash\n# HPC 代码路径\n/data1/syliu/pmcx2026v2\n\n# 可视化脚本\npython pmcx2026v2/generate_real_visualizations.py\npython pmcx",
  "applies_when": [],
  "do_not_apply_when": []
}
---

# CLI Commands & Tools

> author: m1 · confidence: 0.85


### Zotero
```bash
# Zotero MCP fallback
GET https://api.zotero.org/users/{user_id}/collections/{collection_key}/items?format=bibtex
GET https://api.crossref.org/works/{DOI}
```

### 系统进程
```bash
# 杀 runaway codex
pkill -9 -f "codex-darwin-arm64/vendor.*codex"
kill -9 <pid>
ps -Ao pid,pcpu,comm -r | head -5

# Paperclip
./node_modules/.bin/paperclipai
npx paperclipai
```

### GPU/ML
```bash
# HPC 代码路径
/data1/syliu/pmcx2026v2

# 可视化脚本
python pmcx2026v2/generate_real_visualizations.py
python pmcx
