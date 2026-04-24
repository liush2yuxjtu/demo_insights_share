---
{
  "id": "m1-kb-ao-003",
  "title": "3. 文件写入规则",
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
  "label_note": "\n### 典型模式\n```markdown\nwrite to AGENTS.md , for *.html , open with chrome\n```\n\n### 关键规则\n- `AGENTS.md` 用于记录 agent 协调规则和技能映射\n- HTML 文件默认用 Chrome 打开\n- 写入后需要检查链接有效性（特别是 GitHub Pages 推送前）\n- 使用 `@AGENTS.md` 引用来驱动行为\n\n### 文件写入最佳实践\n- 原子提交：每次写入后立即 commit\n- 检查目标文件是否存在\n- 验证写入后的链接可用性\n\n---",
  "applies_when": [],
  "do_not_apply_when": []
}
---

# 3. 文件写入规则

> author: m1 · confidence: 0.85


### 典型模式
```markdown
write to AGENTS.md , for *.html , open with chrome
```

### 关键规则
- `AGENTS.md` 用于记录 agent 协调规则和技能映射
- HTML 文件默认用 Chrome 打开
- 写入后需要检查链接有效性（特别是 GitHub Pages 推送前）
- 使用 `@AGENTS.md` 引用来驱动行为

### 文件写入最佳实践
- 原子提交：每次写入后立即 commit
- 检查目标文件是否存在
- 验证写入后的链接可用性

---
