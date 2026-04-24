---
{
  "id": "m1-kb-ak-003",
  "title": "错误模式",
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
  "label_note": "\n1. **工具使用被用户拒绝：** `User rejected tool use` → agent 停止\n2. **Rate limit：** `apiErrorStatus: 429` → \"You've hit your limit · resets 5pm (Asia/Shanghai)\"\n3. **OpenIslandHooks unavailable：** 每次 hook 调用均失败\n4. **文件不存在：** 路径截断（如 `6ba99ffc-83ac-41c0-a726-8ec` 缺少 `.jsonl` 后缀）\n\n---",
  "applies_when": [],
  "do_not_apply_when": []
}
---

# 错误模式

> author: m1 · confidence: 0.85


1. **工具使用被用户拒绝：** `User rejected tool use` → agent 停止
2. **Rate limit：** `apiErrorStatus: 429` → "You've hit your limit · resets 5pm (Asia/Shanghai)"
3. **OpenIslandHooks unavailable：** 每次 hook 调用均失败
4. **文件不存在：** 路径截断（如 `6ba99ffc-83ac-41c0-a726-8ec` 缺少 `.jsonl` 后缀）

---
