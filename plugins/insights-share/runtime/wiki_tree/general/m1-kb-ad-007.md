---
{
  "id": "m1-kb-ad-007",
  "title": "Actionable Insights",
  "author": "m1",
  "confidence": 0.85,
  "tags": [
    "knowledge-extraction",
    "session-analysis",
    "group_ad"
  ],
  "status": "active",
  "topic_id": "m1-kb-ad",
  "label": "good",
  "label_note": "\n1. **严格文件边界**: 任务只应在 state/memory/*.md 中执行，禁止修改其他文件\n2. **事实优先**: 获取时间/行数等必须用 Bash 真实执行，不猜测\n3. **状态明确**: 完成后在 status.md 标记 completed，阻塞时标记 blocked 并写明原因\n4. **循环管理**: 新任务到达时先 `/cancel` 旧循环，再 `/loop 10m` 新任务",
  "applies_when": [],
  "do_not_apply_when": []
}
---

# Actionable Insights

> author: m1 · confidence: 0.85


1. **严格文件边界**: 任务只应在 state/memory/*.md 中执行，禁止修改其他文件
2. **事实优先**: 获取时间/行数等必须用 Bash 真实执行，不猜测
3. **状态明确**: 完成后在 status.md 标记 completed，阻塞时标记 blocked 并写明原因
4. **循环管理**: 新任务到达时先 `/cancel` 旧循环，再 `/loop 10m` 新任务
