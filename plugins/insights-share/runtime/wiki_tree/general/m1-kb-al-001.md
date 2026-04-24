---
{
  "id": "m1-kb-al-001",
  "title": "模式与技术发现",
  "author": "m1",
  "confidence": 0.85,
  "tags": [
    "knowledge-extraction",
    "session-analysis",
    "group_al"
  ],
  "status": "active",
  "topic_id": "m1-kb-al",
  "label": "good",
  "label_note": "\n### Caveman Mode\n- **级别**: full (默认)，可选 lite/ultra\n- **规则**: 删除冠词(a/an/the)、填充词(just/really/basically/actually/simply)、客套话(sure/certainly/of course/happy to)、hedging\n- **模式**: `[thing] [action] [reason]. [next step].`\n- **自动退出场景**: 安全警告、不可逆操作确认、多步骤序列、用户要求澄清\n- **持久性**: 每个 response 生效，不因多轮回退，关闭需 `stop caveman` / `normal mode`\n\n### Self-Verify-Loop\n- **核心**: `claudefast -p` 作为 LLM judge 替代硬编码 gate\n- **输出**: pseudo-forloop 结构\n- **应用**: skill 文档验证、CLAUDE.md 改动后 agent-judge 双探针循环\n\n### Hook 系统\n- **Ses",
  "applies_when": [],
  "do_not_apply_when": []
}
---

# 模式与技术发现

> author: m1 · confidence: 0.85


### Caveman Mode
- **级别**: full (默认)，可选 lite/ultra
- **规则**: 删除冠词(a/an/the)、填充词(just/really/basically/actually/simply)、客套话(sure/certainly/of course/happy to)、hedging
- **模式**: `[thing] [action] [reason]. [next step].`
- **自动退出场景**: 安全警告、不可逆操作确认、多步骤序列、用户要求澄清
- **持久性**: 每个 response 生效，不因多轮回退，关闭需 `stop caveman` / `normal mode`

### Self-Verify-Loop
- **核心**: `claudefast -p` 作为 LLM judge 替代硬编码 gate
- **输出**: pseudo-forloop 结构
- **应用**: skill 文档验证、CLAUDE.md 改动后 agent-judge 双探针循环

### Hook 系统
- **Ses
