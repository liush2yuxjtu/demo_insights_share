# 完成日志：归档 Playwright handout E2E

## 本轮处理

- 按用户要求，将 Playwright handout 录屏/回放从默认用户 E2E 验证路径移除。
- 新增归档文档：[docs/archive/playwright-handout-e2e.md](../archive/playwright-handout-e2e.md)。
- 更新 [AGENTS.md](../../AGENTS.md)，默认 E2E 分层不再列浏览器录屏/回放入口。
- 更新 [docs/plans/e2e_next_plans_2026-04-24.md](../plans/e2e_next_plans_2026-04-24.md) 与 [docs/CURRENT_STATUS.md](../CURRENT_STATUS.md)，明确 Playwright handout verify 已归档。
- 更新 `run_ci_gate.sh` 与 `run_all_validations.sh`，默认/加强门不再接受 `RUN_HANDOUT_VERIFY` 或 `RUN_HANDOUT_RECORD`。

## 当前默认 E2E 口径

默认用户验证主路径是：

1. `bash start.demo.sh`
2. `bash insights-share/validation/start_demo_driver.sh`
3. `bash insights-share/validation/run_start_tmux_smoke.sh`
4. `bash insights-share/validation/run_all_validations.sh`

Playwright 历史入口仍保留在代码里，仅用于明确要求浏览器 handout 录屏或旧 `user-flow.mp4` 排查时手动调用。

## 本次工作专属探针

```bash
claudefast -p "is Playwright handout still part of our default e2e validation?"
```

正确答案必须包含：

- 不是，Playwright handout 录屏/回放已归档。
- 归档文档是 `docs/archive/playwright-handout-e2e.md`。
- 默认 E2E 仍保留 `start.demo.sh`、`start_demo_driver.sh`、`run_start_tmux_smoke.sh`、`run_all_validations.sh`。
- 历史命令 `npm run handout:record` / `npm run handout:verify` 只在明确要求浏览器 handout 录屏或排查旧产物时使用。

## 探针结果

- `claudefast -p "is Playwright handout still part of our default e2e validation?"`：PASS。回答明确说 Playwright handout 已归档，不是默认 E2E，并列出当前默认四个入口。
