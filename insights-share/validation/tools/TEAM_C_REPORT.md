# Team C 报告：WITH/WITHOUT tmux 对照实验

## 交付物清单

| 路径 | 说明 |
|---|---|
| `insights-share/validation/tools/claude_session_export.py` | jsonl → 易读 txt 导出工具，支持 `--session-id` |
| `insights-share/validation/tmux_with_without.sh` | tmux 双轮对照脚本（先 WITHOUT、后 WITH） |
| `insights-share/validation/reports/deliverables/claude_export_WITHOUT.txt` | 无 skill 的 claude -p 回答（3018 字节） |
| `insights-share/validation/reports/deliverables/claude_export_WITH.txt` | 装载 insights-wiki skill 后的回答（1962 字节） |
| `insights-share/validation/reports/deliverables/diff.md` | 体量、关键词、定性三维差异分析 |

## 执行流程

1. 探测前置：确认 `claude --help` 无 `/export` 命令，必须自写 jsonl 解析
2. 写 `claude_session_export.py`：按 mtime 取最新 jsonl 或 `--session-id` 指定，提取 `message.role in (user, assistant)`，去 ANSI、textwrap 至 120 列
3. 写 `tmux_with_without.sh`：
   - 固定 prompt: `Our checkout API is timing out, postgres is rejecting new connections during the lunch spike`
   - WITHOUT 轮先把 `~/.claude/skills/insights-wiki` 临时移除
   - 通过 `tmux send-keys` 启 `claude -p`，每 5 秒探测 `tee` 文件大小并读 `__DONE__` 哨兵
   - 60 秒后用 `sed -E 's/\x1b\[[0-9;]*[A-Za-z]//g'` 去 ANSI 落盘
   - WITH 轮拷 `demo_codes/.claude/skills/insights-wiki` 到 `~/.claude/skills/`
   - 两轮均 `tmux kill-session` 清理
4. 软依赖处理：先确认 `SKILL.md` 是否存在；不存在就跳过 WITH 轮并写占位文件。本次 Team A 已交付，两轮均完整执行
5. 跑后清理：删除 `~/.claude/skills/insights-wiki.bak.*` 残留备份

## 关键结果

- **体量**：WITH 比 WITHOUT 减少 35%（1962 vs 3018 字节）
- **wiki 专有名词命中**：WITH 引用 `alice` ×3、`2026-04-10` ×1、`confidence` ×1、`do_not_apply` ×1、`idle_in_transaction` ×2；WITHOUT 全部为 0
- **WITHOUT 开场**："这个项目里没有 checkout 或 PostgreSQL 相关代码"——只能给通用 SOP
- **WITH 开场**："这个症状和 `alice_pgpool.json` 里记录的 2026-04-10 事故完全吻合"——直接命中本地 card

## 注意事项

- Bash 脚本注意点：原版用了 `${round^^}` 大小写转换和 `printf '%(...)T'` 时间格式，在 macOS bash 3.2 下报 bad substitution，已改用 `tr` + `date` 子命令
- claude -p 的实际响应时间约 40 秒，60 秒等待留有余量，未触发"会话超时"分支
- jsonl 导出脚本未在本次跑里被强制使用（tmux 直接 tee stdout 即可），但仍保留作为 Team D 二次取证或日后回放工具
