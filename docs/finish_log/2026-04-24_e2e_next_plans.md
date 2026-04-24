# Finish Log: E2E 下一步计划

## 已完成

- 读取项目强制上下文：`CLAUDE.md`、`proposal.md`、`README.md`、`validation_AB.md`、`validation.md`、`proposal/INDEX.md` 与索引 proposal。
- 确认 gstack 已安装：`GSTACK_OK`。
- 执行 `bash start.demo.sh --dry-run`，结果通过 7 阶段，并显示真实 `claude plugin install insights-share@insights-share`。
- 尝试跑 pytest 合同，发现全局无 `pytest`，项目 `.venv` 绑定旧 `/Users/m1` Python 动态库，当前不能本地复验。
- 新增 E2E 分层计划文档：`docs/plans/e2e_next_plans_2026-04-24.md`。
- 新增固定 P3 合同测试入口：`bash insights-share/validation/run_contract_tests.sh`，默认用 `uv + Python 3.11 + pytest`，不依赖全局 pytest 或破损的 `demo_codes/.venv`。
- 已跑通 P3 合同测试：`test_start_scripts.py`、`test_plugin_contract.py`、`test_release_package.py` 共 15 项全绿。
- `start.demo.sh` 已新增 demo venv 自修复：检测到 `.venv/bin/python` 无法启动时，先把旧目录移到 `.venv.broken-<ts>/`，再用可用 Python 重建并安装 `requirements.txt`。
- 已跑 live `bash start.demo.sh`：Stage 0-7 通过，daemon :7821 正常启动，右 pane 显示 `[share ✓ 0/today]` 与 `plugin self-check: ALL GREEN`，退出后沙箱和 daemon 已清理。
- 修复左 pane 讲解旧检查：不再等待旧式 `~/.claude/skills/.../SKILL.md`，改为检测 sandbox plugin cache 内的 `skills/insights-share/SKILL.md`，避免真实 plugin install 路径误报。
- 已修复并跑通 `npm run handout:verify`：verify 现在会按需临时启动 daemon 与 `web_cli_demo` tmux session，结束后清理；同时修复 daemon 内 tmux socket 环境，CLI 输入框可写，5 个 handout step 全部 passed。
- 已修复并跑通 `npm run handout:record`：完整 Dashboard/CLI/Validation/handout 用户流录制通过，生成 `artifacts/handout/latest.json` 指向新的 `user-flow.mp4`；ffmpeg 退出现在有超时兜底，不再卡住 daemon 清理。
- 修复 `start_demo_driver.sh` 的 auto 模式：`--auto-approve` 不再调用 Claude/Codex coach 生成讲解，改用内置说明，避免 tmux smoke 卡在外部 LLM 调用。
- 已跑通 `bash insights-share/validation/run_start_tmux_smoke.sh`：`start.claude.sh` 与 `start.codex.sh` 均完成 healthz、publish_good、publish_bad、solve、install、cache，报告写入 `tmux_claude_smoke.txt` 与 `tmux_codex_smoke.txt`。
- 新增并跑通 AP-1 最小 adoption proof 入口：`bash insights-share/validation/run_adoption_proof.sh`，用隔离 `HOME` 与临时 wiki store 验证 clean-machine install、first relevant hit、first publish、day-2 return，最新报告写入 `adoption_proof_latest.json`。
- 新增 CI/pre-commit 共用 gate：`bash insights-share/validation/run_ci_gate.sh`；新增 `.github/workflows/e2e-gates.yml`，在 `start.*`、plugin、demo_codes、validation、release 改动时跑确定性门禁。
- 对账 `TODOS.md`：`SB-1`、`AP-1`、`FL-1`、`FL-2`、`UC-2` 已关闭；当前唯一 open 项是 `UC-1 plugin bundle self-containment`。
- 补 raw log trust boundary：`TreeInsightStore` 写 export/jsonl raw log 前会脱敏敏感字段和常见 token pattern；`additionalContext` 注入链路有公开字段 allowlist 合同测试。
- 最新本机 gate：`bash insights-share/validation/run_ci_gate.sh` 通过，包含 39 项合同测试、adoption proof、`start.demo.sh --dry-run`。
- 清理状态：没有残留 `:7821` / `:18821` daemon 监听；工作区只剩预先存在且未触碰的 `.claude/settings.local.json` 未跟踪。

## 关键结论

`start.demo.sh` 是 hero E2E surface，但不是完整 E2E suite。完整门禁必须叠加 pytest 合同、Playwright 录屏/回放、tmux smoke、validation 汇总与 adoption proof。

## 后续

Python/pytest runner、hero path、Playwright record/verify、tmux smoke、adoption proof、CI gate 与 raw log trust boundary 已恢复；下一步推进 `UC-1 plugin bundle self-containment`。
