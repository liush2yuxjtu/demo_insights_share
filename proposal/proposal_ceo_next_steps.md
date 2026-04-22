# Proposal: CEO 级下一步执行与验收

> 日期：2026-04-22
> 状态：全部下一步已落地（2026-04-22 更新）

## 下一步做什么

1. 把命令失灵时的兜底链路做稳，避免 demo 或实际使用因为单点失败而中断。
2. 把本地状态与提示规则收敛成清晰、一致的信号，让用户和管理者都能快速判断系统当前在做什么。
3. 把"命中多个主题时先看哪一个"固化为固定优先级，确保不同人、不同轮次得到一致结果。

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
