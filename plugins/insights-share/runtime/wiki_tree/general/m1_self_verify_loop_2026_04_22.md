---
{
  "id": "m1-self-verify-loop-2026-04-22",
  "title": "Self-Verify Loop: Agent-Judge 双探针模式",
  "author": "m1",
  "confidence": 0.9,
  "tags": ["self-verify-loop", "agent-judge", "probe", "quality-gate", "double-probe"],
  "status": "active",
  "applies_when": ["feature 开发完成自检", "CLAUDE.md 规则验证", "finish flag 自检"],
  "do_not_apply_when": ["纯阅读任务", "已确定 PASS 的 trivial 改动"],
  "topic_id": "quality-patterns",
  "label": "good",
  "label_note": "两个独立 agent：一个发 probe，一个当裁判输出 PASS/REFINE/FAIL",
  "raw_log": null
}
---

# Self-Verify Loop: Agent-Judge 双探针模式

> author: m1 · confidence: 0.9

## 架构

```
┌─────────────────────────────────────┐
│  Agent A (probe)                    │
│  claudefast -p "READ ONLY, analyze │
│  recent changes..."                  │
└──────────────┬──────────────────────┘
               ↓ JSON report
┌─────────────────────────────────────┐
│  Agent B (judge)                    │
│  claudefast -p "READ ONLY, judge   │
│  Agent A report. Reply JSON:        │
│  {verdict:PASS|REFINE|FAIL, ...}"  │
└──────────────┬──────────────────────┘
               ↓
         final PASS/REFINE/FAIL
```

## 轮次约束

- fast 模式最多 5 轮
- 连续 REFINE/FAIL 升级 `claude -p` 托底
- 禁止硬编码关键词匹配（规则写入 judge prompt 里）

## 典型应用

1. **CLAUDE.md self-verify**：每次编辑 CLAUDE.md 后验规则触发是否生效
2. **finish flag**：验 commit + docs 一致性
3. **feature self-verify**：feature 开发完成，验交付物

## Applies when

- feature 开发完成自检
- CLAUDE.md 规则验证
- finish flag 自检

## Do NOT apply when

- 纯阅读任务
- 已确定 PASS 的 trivial 改动
