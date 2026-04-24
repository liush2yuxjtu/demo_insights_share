# 完成日志：start.demo.sh latest 日志补齐右 pane 证据

## 本轮处理

- 真实运行 `bash start.demo.sh`，确认 Stage 0-7 能进入 tmux 双 pane。
- 发现 `insights-share/validation/reports/deliverables/start_demo.latest.txt` 只归档左 pane guide，缺少右 pane self-check 证据。
- 更新 `start.demo.sh`：
  - 新增沙箱内 `right.log`。
  - 右 pane 输出通过 `tee` 同步写入 `right.log`。
  - cleanup 时把 `guide.log` 和 `right.log` 合并写入 `start_demo.latest.txt`。
  - `--dry-run` 不再覆盖真实 `start_demo.latest.txt`。
- 更新 `test_start_scripts.py`，锁定 latest log 必须包含右 pane self-check 归档逻辑。

## 最新验证

- `bash -n start.demo.sh`：PASS。
- `bash insights-share/validation/run_contract_tests.sh insights-share/validation/test_start_scripts.py -q`：7 passed。
- `bash start.demo.sh --dry-run`：PASS，dry-run 输出仍包含 right pane self-check 命令。
- 真实 `bash start.demo.sh`：PASS，进入 tmux 后右 pane 显示：
  - `[share ✓ 0/today]`
  - `version: 0.6.1-m7`
  - 5 条 `/share-*` 命令全 `✓`
  - 2 个 agent 全 `✓`
  - `plugin self-check: ALL GREEN`
- 最新日志路径：`insights-share/validation/reports/deliverables/start_demo.latest.txt`。
- 端口清理：退出后无 `:7821` / `:18821` 残留监听。

## 本次工作专属探针

```bash
claudefast -p "does start.demo.sh latest log include right pane self-check evidence?"
```

正确答案必须包含：

- 是，`start_demo.latest.txt` 现在同时包含 left guide log 与 right pane self-check log。
- 右 pane 证据包含 `[share ✓ 0/today]`、`version: 0.6.1-m7`、5 条 `/share-*` 命令、2 个 agent 和 `plugin self-check: ALL GREEN`。
- 退出后无 `:7821` / `:18821` 残留监听。

## 探针结果

- 首次探针回答引用旧 `insights-wiki` / `[wiki ✓]` / M3 日志，判定为 REFINE。
- 已把最新固定答案补入 `docs/CURRENT_STATUS.md` 的 `start.demo.sh latest 日志固定答案`。
- 已更新 `~/.claude/live_terminal/CURRENT` 指向的 `start_demo_latest_20260424` 实机日志，最终探针 PASS，能读到 right pane self-check 证据。
