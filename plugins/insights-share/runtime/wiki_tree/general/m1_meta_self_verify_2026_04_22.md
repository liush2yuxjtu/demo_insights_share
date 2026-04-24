---
{
  "id": "m1-meta-self-verify-2026-04-22",
  "title": "CLAUDE.md 编辑后跑 agent-judge 双探针循环",
  "author": "m1",
  "confidence": 0.88,
  "tags": ["CLAUDE.md", "agent-judge", "self-verify", "probe", "meta"],
  "status": "active",
  "applies_when": ["任何 CLAUDE.md 编辑后"],
  "do_not_apply_when": ["CLAUDE.md 纯阅读无编辑"],
  "topic_id": "delivery-patterns",
  "label": "good",
  "label_note": "claudefast 双探针：一条发 probe + 一条当裁判输出 PASS/REFINE/FAIL JSON",
  "raw_log": null
}
---

# CLAUDE.md 编辑后跑 agent-judge 双探针循环

> author: m1 · confidence: 0.88

## 规则

每次编辑 CLAUDE.md 后跑 agent-judge 双探针循环：
- `claudefast -p` 发 probe
- 另一条 `claudefast -p` 当裁判输出 PASS/REFINE/FAIL JSON

## 轮次约束

- fast 模式最多 5 轮
- 连续停滞或 FAIL 升级 `claude -p` 托底
- **禁止**硬编码关键词匹配

## Good probe 内容

```
READ ONLY. Analyze recent CLAUDE.md edits and rules.
Reply JSON: {"verdict":"PASS|REFINE|FAIL", "rules_understood":[...], "inconsistencies":[]}
```

## 与 finish-flag 区别

- meta-self-verify：专验 CLAUDE.md 编辑后规则被 CLI reasoning 路径理解
- finish-flag：验任意 job 的 commit + docs 一致性

两规则可叠加：CLAUDE.md 改动既走 meta-self-verify 也走 finish flag。

## Applies when

- 任何 CLAUDE.md 编辑后

## Do NOT apply when

- CLAUDE.md 纯阅读无编辑
