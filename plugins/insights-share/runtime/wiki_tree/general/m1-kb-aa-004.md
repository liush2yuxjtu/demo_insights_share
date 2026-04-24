---
{
  "id": "m1-kb-aa-004",
  "title": "4. Daily-report Skill 工作流",
  "author": "m1",
  "confidence": 0.85,
  "tags": [
    "knowledge-extraction",
    "session-analysis",
    "group_aa"
  ],
  "status": "active",
  "topic_id": "m1-kb-aa",
  "label": "good",
  "label_note": "\n1. **扫描**：`grep -rl \"$DATE\" ~/.claude/projects/ --include=\"*.jsonl\"` 提取当日记录，最多 5000 行\n2. **并行3 Haiku Agent**：\n   - Timeline Agent → `*-timeline.md`\n   - Deliverables Agent → `*-deliverables.md`\n   - Signal Agent → `*-signals.md`\n3. **合成输出**：主线程读取 bullet 文件，生成 `*-report.md` + `*-report.html`（内联CSS）\n4. **打开**：`open -a \"Google Chrome\" *.html`\n\n---",
  "applies_when": [],
  "do_not_apply_when": []
}
---

# 4. Daily-report Skill 工作流

> author: m1 · confidence: 0.85


1. **扫描**：`grep -rl "$DATE" ~/.claude/projects/ --include="*.jsonl"` 提取当日记录，最多 5000 行
2. **并行3 Haiku Agent**：
   - Timeline Agent → `*-timeline.md`
   - Deliverables Agent → `*-deliverables.md`
   - Signal Agent → `*-signals.md`
3. **合成输出**：主线程读取 bullet 文件，生成 `*-report.md` + `*-report.html`（内联CSS）
4. **打开**：`open -a "Google Chrome" *.html`

---
