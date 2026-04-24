# E2E 检查下一步计划（2026-04-24）

## 结论

`start.demo.sh` 可以承担 hero E2E：沙箱、真实 `claude plugin install`、daemon、tmux 双 pane、feature manifest、statusline 与 plugin self-check。

`start.demo.sh` 不能单独承担全部 E2E：Playwright 录屏/回放、pytest 合同、release package、tmux 批量 smoke、A/B adoption proof 都需要独立门禁。

## 当前证据

- gstack 已安装：`GSTACK_OK`。
- `bash start.demo.sh --dry-run` 已通过 7 阶段，并真实执行 `claude plugin install insights-share@insights-share`。
- 全局 `pytest` 不存在；项目 `.venv` 绑定旧路径 `/Users/m1/...` 与缺失 `libpython3.12.dylib`。
- 已新增固定入口 `bash insights-share/validation/run_contract_tests.sh`，默认用 `uv + Python 3.11 + pytest`，不依赖全局 pytest 或 `demo_codes/.venv`。
- P3 合同已通过：`test_start_scripts.py`、`test_plugin_contract.py`、`test_release_package.py` 共 15 项全绿。
- `start.demo.sh` 已能检测破损 `demo_codes/.venv` 并自动重建；旧 venv 会移到 `.venv.broken-<ts>/`。
- live `start.demo.sh` 已验证通过：Stage 0-7、daemon :7821、`[share ✓ 0/today]`、`plugin self-check: ALL GREEN` 均通过，退出后无 7821 残留。
- 左 pane 讲解已对齐 plugin install：检查 sandbox plugin cache，不再误报旧式 skill copy 缺失。
- `npm run handout:verify` 已通过：临时 daemon + 临时 `web_cli_demo` tmux session 自动创建和清理，5 个 handout step 全部 passed。
- `npm run handout:record` 已通过：完整用户流 mp4 与 manifest 已刷新，ffmpeg 退出逻辑已加超时兜底。
- `bash insights-share/validation/run_start_tmux_smoke.sh` 已通过：`start.claude.sh` 与 `start.codex.sh` auto smoke 均完成 healthz/publish/solve/install/cache 闭环。
- 已新增并跑通 adoption proof 最小门：`bash insights-share/validation/run_adoption_proof.sh`，用隔离 `HOME` 验证 clean-machine install、first relevant hit、first publish、day-2 return 四个信号；最新报告在 `insights-share/validation/reports/deliverables/adoption_proof_latest.json`。
- 已新增 CI/pre-commit 共用入口：`bash insights-share/validation/run_ci_gate.sh`，并接入 `.github/workflows/e2e-gates.yml`。CI 默认跑合同测试 + adoption proof；本机有 `claude`/`tmux` 时自动加跑 `start.demo.sh --dry-run`。
- `TODOS.md` 中 `SB-1` 与 `UC-2` 很可能已由近期 commit 落地，需要用测试和文档对账后关闭。

## 分层 E2E 门禁

| 层 | 命令 | 目的 | 是否由 start.demo.sh 覆盖 |
|----|------|------|---------------------------|
| P0 环境门 | `test -d ~/.claude/skills/gstack/bin` | gstack 必备 | 否 |
| P1 dry-run hero | `bash start.demo.sh --dry-run` | 验证沙箱、plugin install、脚本结构 | 是 |
| P2 live hero | `bash start.demo.sh` | PM 可见实机闭环 | 是 |
| P3 pytest 合同 | `python -m pytest ...test_start_scripts.py ...test_plugin_contract.py ...test_release_package.py` | start/plugin/release 合同 | 否 |
| P4 Playwright 录屏 | `cd insights-share/validation && npm run handout:record` | 录完整 user-flow mp4 | 否 |
| P5 Playwright 回放 | `cd insights-share/validation && npm run handout:verify` | 回放 latest manifest | 否 |
| P6 tmux smoke | `bash insights-share/validation/run_start_tmux_smoke.sh` | start.claude/start.codex 批量实机 | 部分 |
| P7 汇总报告 | `bash insights-share/validation/run_all_validations.sh` | 汇总既有 Phase 0-5 证据 | 否 |

## 下一步顺序

1. 已完成：修复本机 Python 测试入口，固定为 `bash insights-share/validation/run_contract_tests.sh`。
2. 已完成：跑 P3 合同测试，15 项全绿。
3. 已完成：跑 `start.demo.sh --dry-run` 和一次 live `start.demo.sh`，确认 plugin install hero path 不是表面 install。
4. 已完成：跑 Playwright verify，确认 handout manifest 的 5 个 step 可自动回放。
5. 已完成：跑 Playwright record，重录完整 user-flow mp4。
6. 已完成：跑 tmux smoke，覆盖 `start.claude.sh` 与 `start.codex.sh`。
7. 已完成：adoption proof 最小门已落脚本、合同测试和一次真实报告。
8. 已完成：新增 CI/pre-commit 共用 gate。默认入口是 `run_ci_gate.sh`；本机加强门可设置 `RUN_HANDOUT_VERIFY=1 RUN_TMUX_SMOKE=1` 叠加 Playwright 回放和 tmux smoke。

## PASS 标准

全部通过才算 E2E 绿：P1/P2 hero 绿、P3 合同绿、P4/P5 录屏回放绿、P6 tmux smoke 绿、P7 报告绿、adoption proof 至少有一次 clean-machine 证据。
