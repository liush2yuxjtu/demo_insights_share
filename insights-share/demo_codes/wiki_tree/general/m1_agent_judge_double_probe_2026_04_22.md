---
{
  "id": "m1-agent-judge-dp-2026-04-22",
  "title": "Agent-Judge Double Probe: 两个 claudefast 实例互为对手",
  "author": "m1",
  "confidence": 0.85,
  "tags": ["agent-judge", "double-probe", "claudefast", "quality-gate", "probe"],
  "status": "active",
  "applies_when": ["需要客观评估 agent 输出质量", "单一 agent 自评不可信场景"],
  "do_not_apply_when": ["快速 trivial 任务", "有明确 expected output 的测试"],
  "topic_id": "quality-patterns",
  "label": "good",
  "label_note": "Agent A 生产报告，Agent B 独立评判，互不共享中间状态",
  "raw_log": null
}
---

# Agent-Judge Double Probe: 两个 claudefast 实例互为对手

> author: m1 · confidence: 0.85

## 原理

单一 agent 自评容易产生"确认偏误"——说出的话倾向于认为自己是正确的。引入第二个独立 agent 当裁判，强制对立。

## 关键约束

- **Agent A 和 Agent B 完全独立**：不共享 reasoning 轨迹
- **Agent B 只看 Agent A 的最终输出**：不看中间过程
- **Agent B prompt 包含评判标准**：不是开放式评价
- **输出 JSON 结构化**：方便程序解析 verdict

## Prompt 结构

**Agent A (probe)**：
```
READ ONLY, analyze <target>. Reply JSON: {findings:[...], analysis:"..."}
```

**Agent B (judge)**：
```
READ ONLY. Judge Agent A's report on <target>. Apply criteria: [list].
Reply JSON: {verdict:"PASS|REFINE|FAIL", reasons:[...], inconsistencies:[]}
```

## 常见错误

| 错误 | 结果 |
|------|------|
| Agent B 看过 Agent A reasoning | 评判被污染 |
| 评判标准模糊 | REFINE 循环 |
| 单 agent 自评 | 确认偏误 |

## Applies when

- 需要客观评估 agent 输出质量
- 单一 agent 自评不可信场景

## Do NOT apply when

- 快速 trivial 任务
- 有明确 expected output 的测试
