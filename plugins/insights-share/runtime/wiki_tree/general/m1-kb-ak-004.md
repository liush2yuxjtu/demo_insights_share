---
{
  "id": "m1-kb-ak-004",
  "title": "CLI 命令技巧",
  "author": "m1",
  "confidence": 0.85,
  "tags": [
    "knowledge-extraction",
    "session-analysis",
    "group_ak"
  ],
  "status": "active",
  "topic_id": "m1-kb-ak",
  "label": "good",
  "label_note": "\n```bash\n# 列出最新截图\nls -lt screenshots/ | head -5\n\n# 查看已安装 plugin\ncat ~/.claude/plugins/installed_plugins.json\n\n# 验证 plugin 安装\nclaude plugin list | grep <name>\n\n# 扫描 .claude 目录\nls ~/.claude/ | head -30\n```\n\n---",
  "applies_when": [],
  "do_not_apply_when": []
}
---

# CLI 命令技巧

> author: m1 · confidence: 0.85


```bash
# 列出最新截图
ls -lt screenshots/ | head -5

# 查看已安装 plugin
cat ~/.claude/plugins/installed_plugins.json

# 验证 plugin 安装
claude plugin list | grep <name>

# 扫描 .claude 目录
ls ~/.claude/ | head -30
```

---
