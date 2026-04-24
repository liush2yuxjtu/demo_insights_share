---
{
  "id": "m1-kb-ae-004",
  "title": "Project Patterns",
  "author": "m1",
  "confidence": 0.85,
  "tags": [
    "knowledge-extraction",
    "session-analysis",
    "group_ae"
  ],
  "status": "active",
  "topic_id": "m1-kb-ae",
  "label": "good",
  "label_note": "\n### codex_run_claude 项目\n- 后台执行器模式：定期 loop 任务，维护 memory 文件\n- Skills 目录维护：100+ skills 按类别组织到 report.md\n- 状态确认模式：每次 loop 追加时间戳到 status.md\n\n### insights_share 项目\n- Wiki tree 结构：database/、infra_cache/、tooling/、shell_env/、agent_workflow/、docs_rules/ 等 wiki_type\n- Offline search agent：4 层 wiki + topic index hint + fuzzy match\n- Good/Bad 并列决策展示\n\n### Self-Verify Loop 文件命名\n```\nself-verify-loop__demo_insights_share__main__role-review-inbox-loop__20260421-182231__forloop-run__iter4__shipped.md\n```\n\n### Ses",
  "applies_when": [],
  "do_not_apply_when": []
}
---

# Project Patterns

> author: m1 · confidence: 0.85


### codex_run_claude 项目
- 后台执行器模式：定期 loop 任务，维护 memory 文件
- Skills 目录维护：100+ skills 按类别组织到 report.md
- 状态确认模式：每次 loop 追加时间戳到 status.md

### insights_share 项目
- Wiki tree 结构：database/、infra_cache/、tooling/、shell_env/、agent_workflow/、docs_rules/ 等 wiki_type
- Offline search agent：4 层 wiki + topic index hint + fuzzy match
- Good/Bad 并列决策展示

### Self-Verify Loop 文件命名
```
self-verify-loop__demo_insights_share__main__role-review-inbox-loop__20260421-182231__forloop-run__iter4__shipped.md
```

### Ses
