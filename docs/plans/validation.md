# validation.md → 实现文件导航

源文档：[validation.md](../../validation.md)（只读）

---

## 验证框架总览

验证以 **PM 友好 + STAR 框架** 呈现，所有阶段均通过 tmux + claude -p 录制并保存快照。

总入口：[run_all_validations.sh](../../insights-share/validation/run_all_validations.sh)

---

## 验证任务 1：触发率

| 内容 | 文件路径 |
|------|---------|
| 20 个触发用例（12训练/8测试） | [trigger_cases/cases.yml](../../insights-share/validation/trigger_cases/cases.yml) |
| 触发率计算脚本 | [trigger_rate.py](../../insights-share/validation/trigger_rate.py) |
| 全量结果 | [reports/trigger_rate_all.json](../../insights-share/validation/reports/trigger_rate_all.json) |
| 训练集结果 | [reports/trigger_rate_train.json](../../insights-share/validation/reports/trigger_rate_train.json) |
| 测试集结果 | [reports/trigger_rate_test.json](../../insights-share/validation/reports/trigger_rate_test.json) |
| Phase 0 tmux 快照 | [snapshots/phase0_tmux.txt](../../insights-share/validation/snapshots/phase0_tmux.txt) |

---

## 验证任务 2：优化触发效果（Bob 案例）

**STAR 场景**：Bob 打开 Claude Code 输入 PostgreSQL 相关内容 → 静默触发 haiku-agent 检索 wiki → 汇报结果

触发方式：`SILENT_AND_JUST_RUN`（静默直接执行）

| 内容 | 文件路径 |
|------|---------|
| Bob 会话录制脚本 | [phase2_bob_session.sh](../../insights-share/validation/phase2_bob_session.sh) |
| Phase 2 tmux 快照 | [snapshots/phase2_tmux.txt](../../insights-share/validation/snapshots/phase2_tmux.txt) |
| 参考场景文档 | [pm_walkthrough.md](../../insights-share/demo_docs/pm_walkthrough.md) |

---

## 验证任务 3：更新 wiki（CRUD）

| 操作 | 文件路径 |
|------|---------|
| CRUD 演示脚本 | [phase3_crud.sh](../../insights-share/validation/phase3_crud.sh) |
| Phase 3 tmux 快照 | [snapshots/phase3_tmux.txt](../../insights-share/validation/snapshots/phase3_tmux.txt) |
| wiki 迁移脚本 | [migrate_wiki_to_tree.py](../../insights-share/validation/migrate_wiki_to_tree.py) |
| wiki 上传导出 | [reports/deliverables/wiki_upload.txt](../../insights-share/validation/reports/deliverables/wiki_upload.txt) |

---

## 验证任务 4：wiki 四层结构

```
wiki_type_index
  └── wiki 类型目录 / 类型 INDEX.md   ← 条目格式同 CLAUDE.md 表格规则
       └── wiki_item.md               ← 完整问题 + 反例 + 正例
            └── {full_log}.jsonl / {full_export}.txt
```

| 内容 | 文件路径 |
|------|---------|
| 结构验证脚本 | [check_wiki_layers.py](../../insights-share/validation/check_wiki_layers.py) |
| 结构报告 | [reports/wiki_structure.json](../../insights-share/validation/reports/wiki_structure.json) |
| 种子条目（alice pgpool） | [seeds/alice_pgpool.json](../../insights-share/demo_codes/seeds/alice_pgpool.json) |
| 种子条目（alice celery） | [seeds/alice_celery_retry.json](../../insights-share/demo_codes/seeds/alice_celery_retry.json) |
| 种子条目（carol redis） | [seeds/carol_redis_eviction.json](../../insights-share/demo_codes/seeds/carol_redis_eviction.json) |

---

## 验证任务 5：MiniMax Agentic Wiki 搜索

| 内容 | 文件路径 |
|------|---------|
| 烟雾测试脚本 | [minimax_smoke.py](../../insights-share/validation/minimax_smoke.py) |

---

## 工具集

| 工具 | 文件路径 |
|------|---------|
| Claude 会话导出 | [tools/claude_session_export.py](../../insights-share/validation/tools/claude_session_export.py) |
| 线性时间线提取 | [tools/extract_linear_timeline.py](../../insights-share/validation/tools/extract_linear_timeline.py) |

---

## 最终报告

| 报告 | 文件路径 |
|------|---------|
| 最终 HTML 报告 | [reports/final_report.html](../../insights-share/validation/reports/final_report.html) |
| 最终摘要 JSON | [reports/final_summary.json](../../insights-share/validation/reports/final_summary.json) |
| 交付物总览 | [reports/deliverables/DELIVERABLES_SUMMARY.html](../../insights-share/validation/reports/deliverables/DELIVERABLES_SUMMARY.html) |
