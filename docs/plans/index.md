# INDEX.md — 全项目重要 .md 文件索引

所有重要 Markdown 文件在此登记。新增 .md 文件时必须同步更新本索引。

---

## 根目录（只读）

| 文件 | 说明 |
|------|------|
| [proposal.md](../../proposal.md) | 项目提案：STAR 框架 — 背景/目标/行动/交付物 |
| [README.md](../../README.md) | 仓库简介 |
| [validation.md](../../validation.md) | 验证框架：触发率/wiki CRUD/四层结构/minimax 搜索 |
| [validation_AB.md](../../validation_AB.md) | A/B 对照实验门禁规则（同 prompt 不同环境） |
| [CLAUDE.md](../../CLAUDE.md) | Agent 规则索引（本项目） |

---

## docs/plans（根文档 → 实现文件导航）

| 文件 | 说明 |
|------|------|
| [INDEX.md](index.md) | 本文件：全项目 .md 文件索引 |
| [proposal.md](proposal.md) | proposal.md → 实现文件导航 |
| [validation.md](validation.md) | validation.md → 验证文件导航 |
| [validation-ab.md](validation-ab.md) | validation_AB.md → A/B 资产导航 |
| [readme.md](readme.md) | README.md → 快速入口导航 |

---

## docs/rules（Agent 规则全文）

| 文件 | 说明 |
|------|------|
| [claude-md-format.md](../rules/claude-md-format.md) | CLAUDE.md 规则格式要求 |
| [language.md](../rules/language.md) | 仅使用中文规则全文 |
| [uneditable-md.md](../rules/uneditable-md.md) | 根目录 md 禁止编辑规则全文 |
| [read-before-task.md](../rules/read-before-task.md) | 任务开始前必读四文件规则全文 |

---

## insights-share/demo_docs（PM 面向文档）

| 文件 | 说明 |
|------|------|
| [design.md](../../insights-share/demo_docs/design.md) | 系统设计文档 |
| [pm_walkthrough.md](../../insights-share/demo_docs/pm_walkthrough.md) | PM 演示文档（Alice/Bob 案例） |
| [pm_walkthrough_star.md](../../insights-share/demo_docs/pm_walkthrough_star.md) | PM 演示文档（STAR 格式） |
| [terminal_snapshot.md](../../insights-share/demo_docs/terminal_snapshot.md) | 终端截图/日志快照 |

---

## insights-share/demo_codes/wiki_tree（Wiki 内容）

| 文件 | 说明 |
|------|------|
| [wiki_tree/database/INDEX.md](../../insights-share/demo_codes/wiki_tree/database/INDEX.md) | database 类型 wiki 目录 |
| [wiki_tree/database/postgres_pool.md](../../insights-share/demo_codes/wiki_tree/database/postgres_pool.md) | PostgreSQL 连接池问题条目 |
| [wiki_tree/infra_cache/INDEX.md](../../insights-share/demo_codes/wiki_tree/infra_cache/INDEX.md) | infra_cache 类型 wiki 目录 |
| [wiki_tree/infra_cache/redis_lru_session_eviction.md](../../insights-share/demo_codes/wiki_tree/infra_cache/redis_lru_session_eviction.md) | Redis LRU 会话淘汰条目 |
| [wiki_tree/infra_queue/INDEX.md](../../insights-share/demo_codes/wiki_tree/infra_queue/INDEX.md) | infra_queue 类型 wiki 目录 |
| [wiki_tree/infra_queue/celery_retry_storm.md](../../insights-share/demo_codes/wiki_tree/infra_queue/celery_retry_storm.md) | Celery 重试风暴条目 |

---

## insights-share/demo_codes/.claude/skills（Skill 定义）

| 文件 | 说明 |
|------|------|
| [skills/insights-wiki/SKILL.md](../../insights-share/demo_codes/.claude/skills/insights-wiki/SKILL.md) | insights-wiki skill 定义（--install） |
| [skills/insights-wiki/TEAM_A_REPORT.md](../../insights-share/demo_codes/.claude/skills/insights-wiki/TEAM_A_REPORT.md) | Team A 实现报告 |
| [skills/insights-wiki-server/SKILL.md](../../insights-share/demo_codes/.claude/skills/insights-wiki-server/SKILL.md) | insights-wiki-server skill 定义（--start/--ui） |

---

## insights-share/validation/reports/deliverables（最终交付物）

| 文件 | 说明 |
|------|------|
| [deliverables/README.md](../../insights-share/validation/reports/deliverables/README.md) | 交付物目录说明 |
| [deliverables/diff.md](../../insights-share/validation/reports/deliverables/diff.md) | A/B 对比差异分析 |
| [deliverables/claude_export_WITH.md](../../insights-share/validation/reports/deliverables/claude_export_WITH.md) | Claude 导出（有 insights-wiki） |
| [deliverables/claude_export_WITHOUT.md](../../insights-share/validation/reports/deliverables/claude_export_WITHOUT.md) | Claude 导出（无 insights-wiki） |
| [deliverables/TEAM_B_REPORT.md](../../insights-share/validation/reports/deliverables/TEAM_B_REPORT.md) | Team B 验证报告 |

---

## insights-share/validation/tools（验证工具报告）

| 文件 | 说明 |
|------|------|
| [tools/TEAM_C_REPORT.md](../../insights-share/validation/tools/TEAM_C_REPORT.md) | Team C 工具链报告 |

---

## examples（A/B 对照资产）

| 文件 | 说明 |
|------|------|
| [A_without.human.md](../../examples/A_without.human.md) | A 侧人工录制导出（无 insights-wiki） |
| [B_with.human.md](../../examples/B_with.human.md) | B 侧人工录制导出（有 insights-wiki） |
| [A_without.md](../../examples/A_without.md) | A 侧 agent 格式导出 |
| [B_with.md](../../examples/B_with.md) | B 侧 agent 格式导出 |
| [duck_story.md](../../examples/duck_story.md) | 示例故事（参考用） |

---

## 其他

| 文件 | 说明 |
|------|------|
| [insights-share/plan.md](../../insights-share/plan.md) | insights-share 子模块计划文档 |

---

## 项目顶层目录树（排除 .venv）

```
demo_insights_share/
├── proposal.md                   ← 项目提案（只读）
├── README.md                     ← 仓库简介（只读）
├── validation.md                 ← 验证框架（只读）
├── validation_AB.md              ← A/B 门禁规则（只读）
│
├── examples/                     ← A/B 对照资产 + 录制脚本
│   ├── COMMON_PROMPT.txt
│   ├── A_without.human.md / B_with.human.md
│   ├── A_without.md / B_with.md
│   ├── run_human_AB.sh / validate_commands.sh
│   └── index.html
│
├── insights-share/
│   ├── plan.md
│   ├── demo_codes/
│   │   ├── adapter.py / ui.py / run_demo.sh
│   │   ├── insightsd/
│   │   ├── seeds/
│   │   ├── wiki_tree/            ← 四层 wiki 结构
│   │   │   ├── database/INDEX.md + postgres_pool.md
│   │   │   ├── infra_cache/INDEX.md + redis_lru_session_eviction.md
│   │   │   └── infra_queue/INDEX.md + celery_retry_storm.md
│   │   └── .claude/skills/
│   │       ├── insights-wiki/SKILL.md + TEAM_A_REPORT.md
│   │       └── insights-wiki-server/SKILL.md
│   ├── demo_docs/
│   │   ├── design.md / pm_walkthrough.md
│   │   ├── pm_walkthrough_star.md / terminal_snapshot.md
│   └── validation/
│       ├── trigger_cases/cases.yml
│       ├── trigger_rate.py / minimax_smoke.py
│       ├── check_wiki_layers.py / migrate_wiki_to_tree.py
│       ├── run_all_validations.sh
│       ├── snapshots/ / tools/
│       └── reports/deliverables/
│           ├── README.md / diff.md
│           ├── claude_export_WITH.md / claude_export_WITHOUT.md
│           ├── TEAM_B_REPORT.md / tools/TEAM_C_REPORT.md
│           └── *.html / *.txt / *.json
│
└── docs/
    ├── plans/INDEX.md + proposal.md + validation.md + validation-ab.md + readme.md
    └── rules/claude-md-format.md + language.md + uneditable-md.md + read-before-task.md
```
