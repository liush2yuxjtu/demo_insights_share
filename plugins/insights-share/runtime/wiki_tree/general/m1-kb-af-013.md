---
{
  "id": "m1-kb-af-013",
  "title": "整体策略：5 个 phase + 1 个汇总 harness",
  "author": "m1",
  "confidence": 0.85,
  "tags": [
    "knowledge-extraction",
    "session-analysis",
    "group_af"
  ],
  "status": "active",
  "topic_id": "m1-kb-af",
  "label": "good",
  "label_note": "\n每个 phase 严格遵循\"进入条件 → 动作 → 退出条件（tmux 快照可验证）\"。所有 tmux 会话名使用 `isv-pN` 前缀（isv =\n\n- Base directory for this skill: /Users/m1/.claude/plugins/cache/insights-share-plugin/insights-share/0.6.0-m7/skills/insights-share\n\n# insights-share Skill\n\n把局域网 `insightsd`(Bob 团队的私有 wiki)里的实战 insight\n\n- 沙箱真隔离验证通过。最终结构：\n\n```\n/tmp/demo-sandbox-<ts>/\n├── home/                              ← 右 pane export HOME 指向这里\n│   ├── .cache/                        ← skill 写缓存的沙箱位置\n│   └── .claude/\n│       ├── .cred\n\n- This session",
  "applies_when": [],
  "do_not_apply_when": []
}
---

# 整体策略：5 个 phase + 1 个汇总 harness

> author: m1 · confidence: 0.85


每个 phase 严格遵循"进入条件 → 动作 → 退出条件（tmux 快照可验证）"。所有 tmux 会话名使用 `isv-pN` 前缀（isv =

- Base directory for this skill: /Users/m1/.claude/plugins/cache/insights-share-plugin/insights-share/0.6.0-m7/skills/insights-share

# insights-share Skill

把局域网 `insightsd`(Bob 团队的私有 wiki)里的实战 insight

- 沙箱真隔离验证通过。最终结构：

```
/tmp/demo-sandbox-<ts>/
├── home/                              ← 右 pane export HOME 指向这里
│   ├── .cache/                        ← skill 写缓存的沙箱位置
│   └── .claude/
│       ├── .cred

- This session
