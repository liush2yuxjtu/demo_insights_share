---
{
  "id": "m1-kb-al-002",
  "title": "错误模式与修复",
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
  "label_note": "\n### Caveman 误用\n- 安全警告、不可逆操作确认时仍用 caveman 语气 → 应 normal 写\n- 代码/commits/PRs 仍用 caveman → 应 normal 写\n\n### 语言裁判漏判\n- 混入英文尾巴/日文/韩文碎片 → FAIL\n- 语义上未直接回答问题 → FAIL\n\n### Hook bridge unavailable\n- OpenIslandHooks bridge 不可用时不影响主流程，继续执行",
  "applies_when": [],
  "do_not_apply_when": []
}
---

# 错误模式与修复

> author: m1 · confidence: 0.85


### Caveman 误用
- 安全警告、不可逆操作确认时仍用 caveman 语气 → 应 normal 写
- 代码/commits/PRs 仍用 caveman → 应 normal 写

### 语言裁判漏判
- 混入英文尾巴/日文/韩文碎片 → FAIL
- 语义上未直接回答问题 → FAIL

### Hook bridge unavailable
- OpenIslandHooks bridge 不可用时不影响主流程，继续执行
