---
{
  "id": "m1-caveman-mode-2026-04-22",
  "title": "Caveman Mode: 删助词/ filler / 冠词，碎片化输出",
  "author": "m1",
  "confidence": 0.88,
  "tags": ["caveman-mode", "token-efficiency", "output-optimization", "terse"],
  "status": "active",
  "applies_when": ["token 紧张场景", "需要极度简洁输出"],
  "do_not_apply_when": ["正式文档/代码注释/PR 描述", "安全警告/不可逆操作确认"],
  "topic_id": "output-patterns",
  "label": "good",
  "label_note": "删 articles (a/an/the)、filler (just/really/basically)、pleasantries (sure/certainly)",
  "raw_log": null
}
---

# Caveman Mode: 删助词/ filler / 冠词，碎片化输出

> author: m1 · confidence: 0.88

## 规则

| 删除 | 示例 |
|------|------|
| articles | ~~the~~ ~~a~~ ~~an~~ |
| filler | ~~just~~ ~~really~~ ~~basically~~ ~~actually~~ |
| pleasantries | ~~sure~~ ~~certainly~~ ~~of course~~ ~~happy to~~ |

## Example

**Normal**: "Sure! I'd be happy to help you with that. The issue you're experiencing is likely caused by..."

**Caveman**: "Bug in auth middleware. Token expiry check use `<` not `<=`. Fix:"

## 何时停用

- 代码/commits/PR 描述：写正常
- 安全警告：写正常
- 不可逆操作确认：写正常
- 用户要求澄清或重复问题：写正常

## 强度级别

| Level | What change |
|-------|-------------|
| **full** | Drop articles, fragments OK, short synonyms |
| **lite** | Reduce filler, keep most normal structure |
| **ultra** | 极度压缩，每句 ≤5 词 |

## Applies when

- token 紧张场景
- 需要极度简洁输出

## Do NOT apply when

- 正式文档/代码注释/PR 描述
- 安全警告/不可逆操作确认
