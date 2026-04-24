---
{
  "id": "m1-kb-ao-017",
  "title": "14. 可执行洞察",
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
  "label_note": "\n1. **Agent 任务分配**: 使用 `teammate-message` 格式，标注 `summary` 字段\n2. **文件写入**: 优先使用 chrome 打开 HTML，VSCode 预览 Markdown\n3. **远程操作**: 全部通过 SSH，验证密钥授权是首要步骤\n4. **规则验证**: 用 LLM-as-judge 替代硬编码关键词匹配\n5. **Git 工作流**: 推送前验证链接，原子提交\n6. **HPC 使用**: 监控 GPU 使用率，支持多类型 GPU\n7. **技能系统**: 渐进式披露，AGENTS.md 作为入口\n\n---",
  "applies_when": [],
  "do_not_apply_when": []
}
---

# 14. 可执行洞察

> author: m1 · confidence: 0.85


1. **Agent 任务分配**: 使用 `teammate-message` 格式，标注 `summary` 字段
2. **文件写入**: 优先使用 chrome 打开 HTML，VSCode 预览 Markdown
3. **远程操作**: 全部通过 SSH，验证密钥授权是首要步骤
4. **规则验证**: 用 LLM-as-judge 替代硬编码关键词匹配
5. **Git 工作流**: 推送前验证链接，原子提交
6. **HPC 使用**: 监控 GPU 使用率，支持多类型 GPU
7. **技能系统**: 渐进式披露，AGENTS.md 作为入口

---
