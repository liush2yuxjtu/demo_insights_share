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

## 关键结论

`start.demo.sh` 是 hero E2E surface，但不是完整 E2E suite。完整门禁必须叠加 pytest 合同、Playwright 录屏/回放、tmux smoke、validation 汇总与 adoption proof。

## 后续

Python/pytest runner 与 P3 合同测试已恢复；下一步推进 `start.demo.sh --dry-run` + live hero、Playwright、tmux smoke、adoption proof 与 CI gate。
