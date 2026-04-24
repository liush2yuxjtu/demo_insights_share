# Proposal: CEO 级下一步执行与验收

> 日期：2026-04-24
> 状态：2026-04-22 三项已落地；当前下一步切到 E2E 检查闭环

## 下一步做什么

当前 next plans 以 [docs/plans/e2e_next_plans_2026-04-24.md](../docs/plans/e2e_next_plans_2026-04-24.md) 为准：

1. 先修 Python/pytest runner，让 start/plugin/release 三组合同测试可执行。
2. 跑 `bash start.demo.sh --dry-run` 与一次 live `bash start.demo.sh`，确认 hero path 真实走 `claude plugin install`。
3. 跑 Playwright `handout:record` / `handout:verify`，确认录屏与 manifest 不漂移。
4. 跑 `run_start_tmux_smoke.sh`，覆盖 `start.claude.sh` 与 `start.codex.sh`。
5. 补 adoption proof：clean-machine install、first relevant hit、first publish、day-2 return。
6. 全部本地门绿后再加 CI/pre-commit gate，避免把 broken test runner 固化成假红。

`start.demo.sh` 的定位：可以做 hero E2E surface；不能替代 pytest、Playwright、tmux smoke、release package 与 adoption proof。

## 已完成的上一轮下一步

## 落地状态（2026-04-22 更新）

| 下一步 | 状态 | 证据 |
|--------|------|------|
| 1. 兜底稳定性 | ✅ PASS | `latency_gate.py` O5 async hook 有 `INSIGHTS_STOP_HOOK_ASYNC=0` 降级路径；`search_agent.run` 新 local-first 两层（本地 → MiniMax），单点失败不阻断下一轮 |
| 2. 状态清晰度 | ✅ PASS | statusline 三态 `[share ✓ / ✗ / …]` + 数值徽章 `[share ⏱ p95=Xms]`；metrics 按 stage 拆分落 `metrics/<date>.jsonl`，人眼和 gate 都能读 |
| 3. 多主题优先级固化 | ✅ PASS（commit `87acecf`） | `topics.json` 新增 `priority: int` 字段（缺省 0）；`search_agent._load_topics_payload` 按 `priority desc → created_at asc` 稳定排序；`local_search.search` 也同一规则。`test_search_agent_priority.py` 3 条 stability 测试、`test_local_search.py::test_priority_breaks_score_ties` 断言 5 次连续调用顺序完全一致 |

## 如何验证

| 验证目标 | CEO 级通过标准 | 当前结果 |
|----------|----------------|----------|
| 兜底稳定性 | 在关键命令失灵、局部状态缺失或链路波动时，系统仍能继续给出可用结果，或明确进入可接受的降级路径，而不是卡住。 | ✅ local-first + SDK fallback 两层，任一层单独可用都不中断 |
| 状态清晰度 | 演示中能够直接看出系统是否在线、是否命中、是否走了兜底，减少"看不见系统在工作"的不确定性。 | ✅ statusline + metrics jsonl 双通道，肉眼 + gate 均可读 |
| 决策一致性 | 对同一组多主题输入，系统多次运行仍优先打开同一主题，并给出一致、可解释的选择顺序。 | ✅ `priority desc → created_at asc` 硬编码规则；29 单测全绿，5 次连跑顺序 identical |
| 端到端可演示 | 通过一轮完整 demo，同步覆盖正常路径、兜底路径和多主题命中路径，且结果可重复。 | ✅ `capture_m7_post_local_search.py` 重复执行，cache-miss p95=1059ms < budget 6000ms |

## priority 使用约定

- `topics.json` 每条 topic 可选 `priority` 字段（int；缺省 0）
- 排序规则：`priority desc → created_at asc`（既决定 PROMPT 注入顺序，也决定本地检索 tiebreak）
- 管理员用 share-curator agent 调 `label_override` 时可同步提 priority，无需动 MiniMax 模型侧
