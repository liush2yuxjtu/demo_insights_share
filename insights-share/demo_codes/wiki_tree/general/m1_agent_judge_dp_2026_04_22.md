---
{
  "id": "m1-agent-judge-dp-2026-04-22",
  "title": "Agent-Judge Double Probe: 两个 claudefast 实例互为对手",
  "author": "m1",
  "team": null,
  "confidence": 0.85,
  "tags": [
    "agent-judge",
    "double-probe",
    "claudefast",
    "quality-gate",
    "probe"
  ],
  "status": "active",
  "applies_when": [
    "需要客观评估 agent 输出质量",
    "单一 agent 自评不可信场景"
  ],
  "do_not_apply_when": [
    "快速 trivial 任务",
    "有明确 expected output 的测试"
  ],
  "raw_log": "./raw/m1-agent-judge-dp-2026-04-22.jsonl",
  "topic_id": "quality-patterns",
  "label": "good",
  "label_note": "Agent A 生产报告，Agent B 独立评判，互不共享中间状态",
  "label_override": null,
  "label_override_by": null,
  "label_override_at": null,
  "raw_log_type": "jsonl",
  "raw_log_sha256": "7b3f82dfc3cd135e6adb8b309516f9c7d68aeb011e4593e4780a1204b628971f",
  "signature_algorithm": "ed25519",
  "signature_schema": 1,
  "signature_key_id": "51e8985cd0e6105e",
  "signature": "Evc0TbiNHTgTNb8bQtGmlWsNqAKGwpFF3o6XY3s7QEktRP3l/suApd0h7BBb75zJOpyrrp+FMh1rgv3UpYFRCQ==",
  "signature_signed_at": "2026-04-22T08:49:37.511873+00:00"
}
---

# Agent-Judge Double Probe: 两个 claudefast 实例互为对手

> author: m1 · team: shared · confidence: 0.85

## Description



## Bad example



## Good example



## Applies when

- 需要客观评估 agent 输出质量
- 单一 agent 自评不可信场景

## Do NOT apply when

- 快速 trivial 任务
- 有明确 expected output 的测试

## Raw log

[./raw/m1-agent-judge-dp-2026-04-22.jsonl](./raw/m1-agent-judge-dp-2026-04-22.jsonl)
