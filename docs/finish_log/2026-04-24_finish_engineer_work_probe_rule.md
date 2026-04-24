# 完工日志：工程完工探针规则

## 触发用户消息

用户要求：更新文档，直到 `claudefast -p "what would we do when we finish an engineer work ?"` 能回答“完工后要继续更新 docs，直到对应 `claudefast -p` 探针返回正确答案”；并给出 E2E 示例探针 `claudefast -p "what is our e2e status"`。

## 本次结果

- 主要提交：
  - `6d519ad` `Require work-specific finish probes`
  - `fee78ca` `Record finish probe verification`
- 在 `docs/rules/finish-flag-claudefast.md` 中把完工流程从单一 finish flag 扩展为两个门：
  - 工作专属探针：先选出用户之后会问的自然语言状态问题，并更新 docs / finish_log / status source，直到 `claudefast -p "<探针>"` 回答正确。
  - READ ONLY finish flag：再验证 recent commits 与 docs 一致。
- 在 `docs/CURRENT_STATUS.md` 中新增固定问答源，确保 `claudefast -p "what would we do when we finish an engineer work ?"` 必须回答工作专属探针闭环。
- 明确 E2E 的工作专属探针是：
  ```bash
  claudefast -p "what is our e2e status"
  ```
- 明确回答工程完工流程时必须原样包含这个 E2E 示例探针，不能只泛泛描述“跑工作专属探针”。
- 明确本规则自身的探针是：
  ```bash
  claudefast -p "what would we do when we finish an engineer work ?"
  ```

## 涉及文件

- `docs/rules/finish-flag-claudefast.md`
- `docs/CURRENT_STATUS.md`
- `docs/finish_log/2026-04-24_finish_engineer_work_probe_rule.md`

## 验证计划

- `claudefast -p "what would we do when we finish an engineer work ?"`：PASS，返回“写 finish_log → 选工作专属探针 → 补 docs 直到答对 → READ ONLY finish flag”，并原样包含 `claudefast -p "what is our e2e status"`。
- `claudefast -p "what is our e2e status"`：历史 PASS；当时返回 E2E 全部通过，并指出唯一 open 项是 `UC-1 plugin bundle self-containment`。后续 UC-1 已关闭，当前权威状态以 `docs/CURRENT_STATUS.md` 与 `docs/plans/e2e_next_plans_2026-04-24.md` 为准：没有开放 E2E 阻塞项，默认下一步是 release/PR 收尾。
- `claudefast -p "what would happen if we say to claude code CLI in this project 'start'"` + 独立 judge：PASS，`CLAUDE.md` 修改后的 agent-judge 状态灯收敛在 fast iter=2；这是 CLAUDE.md 编辑专用规则，fast 上限为 5 轮。
- READ ONLY finish flag probe：第一轮 REFINE，要求同步 `docs/CURRENT_STATUS.md` 的 recent commits 说明，并避免把 CLAUDE.md agent-judge 的 5 轮上限误读成 finish flag 的 3 轮上限。

## 轮次说明

- 工作专属探针 / finish flag：fast 最多 3 轮，连续 REFINE 升级 `claude -p`。
- CLAUDE.md agent-judge 状态灯：fast 最多 5 轮，连续停滞或 FAIL 升级 `claude -p`。
- 本次同时触发两条规则，所以两种轮次上限并存；它们不是同一个 gate。
