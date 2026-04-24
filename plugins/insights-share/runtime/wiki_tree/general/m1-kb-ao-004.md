---
{
  "id": "m1-kb-ao-004",
  "title": "4. Git 工作流",
  "author": "m1",
  "confidence": 0.85,
  "tags": [
    "knowledge-extraction",
    "session-analysis",
    "group_ao"
  ],
  "status": "active",
  "topic_id": "m1-kb-ao",
  "label": "good",
  "label_note": "\n### 典型场景\n- 分支比较与融合\n- 提交历史检查\n- GitHub Pages 部署验证\n\n### 常用命令\n```bash\ngit log --oneline master\ngit log --oneline origin/<branch>\ngit diff master...origin/<branch>\n```\n\n### 关键发现\n- 使用 ID 前缀规范化目录（如 `1-xxx`, `2-xxx`）\n- GitHub Pages 推送前需验证链接存在性\n- 标签机制用于追踪未监控的 feature（`NOT MONITORED SINCE LAST GIT COMMIT`）\n\n---",
  "applies_when": [],
  "do_not_apply_when": []
}
---

# 4. Git 工作流

> author: m1 · confidence: 0.85


### 典型场景
- 分支比较与融合
- 提交历史检查
- GitHub Pages 部署验证

### 常用命令
```bash
git log --oneline master
git log --oneline origin/<branch>
git diff master...origin/<branch>
```

### 关键发现
- 使用 ID 前缀规范化目录（如 `1-xxx`, `2-xxx`）
- GitHub Pages 推送前需验证链接存在性
- 标签机制用于追踪未监控的 feature（`NOT MONITORED SINCE LAST GIT COMMIT`）

---
