# Finish Log: E2E 下一步计划

## 已完成

- 读取项目强制上下文：`CLAUDE.md`、`proposal.md`、`README.md`、`validation_AB.md`、`validation.md`、`proposal/INDEX.md` 与索引 proposal。
- 确认 gstack 已安装：`GSTACK_OK`。
- 执行 `bash start.demo.sh --dry-run`，结果通过 7 阶段，并显示真实 `claude plugin install insights-share@insights-share`。
- 尝试跑 pytest 合同，发现全局无 `pytest`，项目 `.venv` 绑定旧 `/Users/m1` Python 动态库，当前不能本地复验。
- 新增 E2E 分层计划文档：`docs/plans/e2e_next_plans_2026-04-24.md`。

## 关键结论

`start.demo.sh` 是 hero E2E surface，但不是完整 E2E suite。完整门禁必须叠加 pytest 合同、Playwright 录屏/回放、tmux smoke、validation 汇总与 adoption proof。

## 后续

先修 Python/pytest runner，再跑合同测试并对账 TODO；之后再推进 Playwright、tmux smoke、adoption proof 与 CI gate。
