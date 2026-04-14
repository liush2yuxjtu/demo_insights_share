# deliverables · 交付物索引

`demo-insights-0414-update` 演示更新的最终落盘集合。本目录由 Team A/B/C/D 协作产出，作为「insights-share skill 化 + 静默下载补强 + linear 时间线 + WITH/WITHOUT 对照」一站式验收材料。

## 流水表

| 文件 | 生成者 | 大小 | 状态 |
|---|---|---|---|
| `proposal_linear.html` | team-b | 21 KB | 已生成 |
| `validation_linear.html` | team-b | 54 KB | 已生成 |
| `claude_export_WITH.txt` | team-c | 1962 B | 已生成 |
| `claude_export_WITHOUT.txt` | team-c | 3018 B | 已生成 |
| `diff.md` | team-c | 3.2 KB | 辅助 |
| `TEAM_B_REPORT.md` | team-b | 2.8 KB | 辅助 |
| `TEAM_C_REPORT.md` | team-c | (tools/) | 辅助 |
| `regression_run.log` | team-d | 见日志 | 回归 PASS (6/6) |
| `DELIVERABLES_SUMMARY.html` | team-d | 单页证据 | 已生成 |

## 主要交付物

### `proposal_linear.html`
- 用途：`proposal.md` 关键词的线性时间线（42 事件）。
- 命令：`python3 insights-share/validation/tools/extract_linear_timeline.py --keyword proposal.md --out -`
- 数据源：`~/.claude/projects/-Users-m1-projects-demo-insights-share/*.jsonl`
- 再现：脚本 → 渲染脚本 → `open -a "Google Chrome" proposal_linear.html`

### `validation_linear.html`
- 用途：`validation.md` + `validation/` 关键词的线性时间线（118 事件）。
- 命令：`python3 insights-share/validation/tools/extract_linear_timeline.py --keyword validation.md --keyword 'validation/' --out -`
- 数据源：同上 6 份 jsonl。
- 再现：同 proposal_linear。

### `claude_export_WITH.txt`
- 用途：装载 `insights-wiki` skill 后的 `claude -p` 答复（1962B）。
- 命令：`bash insights-share/validation/tmux_with_without.sh`（WITH 轮）
- 数据源：固定 prompt + `~/.claude/skills/insights-wiki/`（拷自 `demo_codes/`）
- 再现：脚本会 `tmux send-keys` 触发 `claude -p`，60 s 后 `sed` 去 ANSI 落盘。

### `claude_export_WITHOUT.txt`
- 用途：临时移除 skill 后的对照答复（3018B）。
- 命令：`bash insights-share/validation/tmux_with_without.sh`（WITHOUT 轮）
- 数据源：同上 prompt，`~/.claude/skills/insights-wiki` 已临时移除。
- 再现：脚本自动备份 → 跑 → 恢复。

## 辅助文件

- `diff.md`：team-c 的 WITH/WITHOUT 三维差异（体量 / 关键词 / 定性）。
- `TEAM_B_REPORT.md`：linear 时间线脚本设计与脱敏边界。
- `TEAM_C_REPORT.md`（位于 `validation/tools/`）：tmux 双轮脚本与 jsonl 导出工具。
- `regression_run.log`：team-d 跑 `bash insights-share/validation/run_all_validations.sh` 的完整 stdout/stderr。本次 6/6 phase PASS，Team A 的 hook 改动未破坏验收。
- `DELIVERABLES_SUMMARY.html`：team-d 单页证据 HTML，含命令 / 预期 / 实际三要素与关键发现。
