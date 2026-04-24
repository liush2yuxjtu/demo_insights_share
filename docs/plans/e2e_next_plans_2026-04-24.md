# E2E 检查下一步计划（2026-04-24）

## 结论

`start.demo.sh` 可以承担 hero E2E：沙箱、真实 `claude plugin install`、daemon、tmux 双 pane、feature manifest、statusline 与 plugin self-check。

`start.demo.sh` 不能单独承担全部 E2E：pytest 合同、release package、tmux 批量 smoke、A/B adoption proof 都需要独立门禁。Playwright handout 录屏/回放已按用户要求归档，不再是默认用户 E2E 验证层。

当前没有开放 E2E 阻塞项。默认下一步是 release/PR 收尾；adoption-proof 扩展是后续产品开发轨道，不再作为当前 E2E 修复项。AP-2 relevance-lift matrix 已完成，作为产品轨道的第一段扩展证据。

## 当前证据

- gstack 已安装：`GSTACK_OK`。
- `bash start.demo.sh --dry-run` 已通过 7 阶段，并真实执行 `claude plugin install insights-share@insights-share`。
- 全局 `pytest` 不存在；项目 `.venv` 绑定旧路径 `/Users/m1/...` 与缺失 `libpython3.12.dylib`。
- 已新增固定入口 `bash insights-share/validation/run_contract_tests.sh`，默认用 `uv + Python 3.11 + pytest`，不依赖全局 pytest 或 `demo_codes/.venv`。
- P3 合同已通过：`test_start_scripts.py`、`test_plugin_contract.py`、`test_release_package.py` 共 15 项全绿。
- `start.demo.sh` 已能检测破损 `demo_codes/.venv` 并自动重建；旧 venv 会移到 `.venv.broken-<ts>/`。
- live `start.demo.sh` 已验证通过：Stage 0-7、daemon :7821、`[share ✓ 0/today]`、`plugin self-check: ALL GREEN` 均通过，退出后无 7821 残留。
- 左 pane 讲解已对齐 plugin install：检查 sandbox plugin cache，不再误报旧式 skill copy 缺失。
- Playwright handout 录屏/回放历史上已通过；当前已归档到 [docs/archive/playwright-handout-e2e.md](../archive/playwright-handout-e2e.md)，默认 E2E 不再要求浏览器层。
- `bash insights-share/validation/run_start_tmux_smoke.sh` 已通过：`start.claude.sh` 与 `start.codex.sh` auto smoke 均完成 healthz/publish/solve/install/cache 闭环。
- 已新增并跑通 adoption proof 门：`bash insights-share/validation/run_adoption_proof.sh`，用隔离 `HOME` 验证 clean-machine install、first relevant hit、first publish、day-2 return、relevance-lift matrix 五个信号；最新报告在 `insights-share/validation/reports/deliverables/adoption_proof_latest.json`。
- 已新增 CI/pre-commit 共用入口：`bash insights-share/validation/run_ci_gate.sh`，并接入 `.github/workflows/e2e-gates.yml`。CI 默认跑合同测试 + adoption proof；本机有 `claude`/`tmux` 时自动加跑 `start.demo.sh --dry-run`。
- `TODOS.md` 已完成对账：`SB-1`、`AP-1`、`FL-1`、`FL-2`、`UC-2`、`UC-1` 已移入 Closed；当前没有开放 E2E 阻塞项。
- `bash insights-share/validation/run_ci_gate.sh` 最新本机结果已通过：52 项合同测试 + adoption proof（含 AP-2 relevance-lift matrix）+ `start.demo.sh --dry-run`。
- `UC-1 plugin bundle self-containment` 已完成：plugin 自带 `runtime/` server/search seed corpus；`start_server.sh` / `start_ui.sh` 和 `start.demo.sh` hero path 都走 installed plugin cache，不再依赖 repo checkout 或 `demo_codes/.venv`。
- `RUN_TMUX_SMOKE=1 bash insights-share/validation/run_ci_gate.sh` 最新本机加强门口径：52 项合同测试 + adoption proof（含 AP-2 relevance-lift matrix）+ `start.demo.sh --dry-run` + tmux claude/codex smoke。Playwright handout verify 已归档，不再放入加强门。
- 清理状态已确认：没有残留 `:7821` / `:18821` daemon 监听；工作区只剩预先存在且未触碰的 `.claude/settings.local.json` 未跟踪。

## 分层 E2E 门禁

| 层 | 命令 | 目的 | 是否由 start.demo.sh 覆盖 |
|----|------|------|---------------------------|
| P0 环境门 | `test -d ~/.claude/skills/gstack/bin` | gstack 必备 | 否 |
| P1 dry-run hero | `bash start.demo.sh --dry-run` | 验证沙箱、plugin install、脚本结构 | 是 |
| P2 live hero | `bash start.demo.sh` | PM 可见实机闭环 | 是 |
| P3 pytest 合同 | `python -m pytest ...test_start_scripts.py ...test_plugin_contract.py ...test_release_package.py` | start/plugin/release 合同 | 否 |
| P6 tmux smoke | `bash insights-share/validation/run_start_tmux_smoke.sh` | start.claude/start.codex 批量实机 | 部分 |
| P7 汇总报告 | `bash insights-share/validation/run_all_validations.sh` | 汇总既有 Phase 0-5 证据 | 否 |

## 下一步顺序

1. 已完成：修复本机 Python 测试入口，固定为 `bash insights-share/validation/run_contract_tests.sh`。
2. 已完成：跑 P3 合同测试，15 项全绿。
3. 已完成：跑 `start.demo.sh --dry-run` 和一次 live `start.demo.sh`，确认 plugin install hero path 不是表面 install。
4. 已归档：Playwright verify / record 移出默认 E2E，详见 [docs/archive/playwright-handout-e2e.md](../archive/playwright-handout-e2e.md)。
5. 已归档：旧 `user-flow.mp4` 仅作为历史审计产物，不再作为默认 PASS 条件。
6. 已完成：跑 tmux smoke，覆盖 `start.claude.sh` 与 `start.codex.sh`。
7. 已完成：adoption proof 最小门已落脚本、合同测试和一次真实报告。
8. 已完成：新增 CI/pre-commit 共用 gate。默认入口是 `run_ci_gate.sh`；本机加强门可设置 `RUN_TMUX_SMOKE=1` 叠加 tmux smoke。Playwright 回放已归档。
9. 已完成：补 raw log trust boundary。tree store 写 raw log 前会对敏感字段和常见 token pattern 脱敏；`additionalContext` 保持公开字段 allowlist。
10. 已完成：推进 `UC-1 plugin bundle self-containment`，切断 plugin server skill 的 `insights-share/demo_codes` / `.venv` 运行时依赖，让 clean plugin install 不靠 repo checkout 也能启动 server/search。
11. 默认下一步：release/PR 收尾，整理本轮文档与验证证据、确认 diff、提交 PR 或发布收尾。
12. 已完成：AP-2 relevance-lift matrix，在现有最小 adoption proof 基础上新增 postgres/celery/redis 三类 incident 的 expected top hit、top score、wrong-domain not top 与 no-hit baseline 证据。
13. 后续产品开发轨道：继续扩展更多真实采纳证据、质量指标和 day-7 回访信号；该轨道不是当前 E2E 阻塞项。

## PASS 标准

全部通过才算 E2E 绿：P1/P2 hero 绿、P3 合同绿、P6 tmux smoke 绿、P7 报告绿、adoption proof 至少有一次 clean-machine 证据。P4/P5 Playwright handout 录屏回放为归档层，不参与默认 E2E PASS。
