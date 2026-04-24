# 完工日志：工程完工探针规则

## 触发用户消息

用户要求：更新文档，直到 `claudefast -p "what would we do when we finish an engineer work ?"` 能回答“完工后要继续更新 docs，直到对应 `claudefast -p` 探针返回正确答案”；并给出 E2E 示例探针 `claudefast -p "what is our e2e status"`。

## 本次结果

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

- 运行 `claudefast -p "what would we do when we finish an engineer work ?"`，确认返回包含工作专属探针闭环。
- 运行 `claudefast -p "what is our e2e status"`，确认 E2E 示例探针能返回当前 E2E 状态。
- 提交文档变更后运行 READ ONLY finish flag probe。
