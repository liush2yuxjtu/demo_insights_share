---
{
  "id": "m1-finish-flag-2026-04-22",
  "title": "job 完工走 claudefast READ ONLY finish flag",
  "author": "m1",
  "confidence": 0.88,
  "tags": ["finish-flag", "claudefast", "READ ONLY", "job-complete", "docs"],
  "status": "active",
  "applies_when": ["任意 job (feature/fix/refactor/chore) 自认完成时"],
  "do_not_apply_when": ["正在进行的中间步骤", "用户要求跳过 finish 阶段"],
  "topic_id": "delivery-patterns",
  "label": "good",
  "label_note": "先写 docs/finish_log/ 再跑 claudefast -p READ ONLY probe",
  "raw_log": null
}
---

# job 完工走 claudefast READ ONLY finish flag

> author: m1 · confidence: 0.88

## 强制顺序

1. **写 docs**：把 job 结果落到 `docs/finish_log/<YYYY-MM-DD>_<slug>.md`，包含主要 commit hash、涉及文件、执行结果
2. **跑 finish flag probe**（READ ONLY，禁写）：
   ```bash
   claudefast -p "READ ONLY, tell me what we have done in recent commits and based on docs. Reply JSON: {\"verdict\":\"PASS|REFINE|FAIL\", \"recent_commits\":[hashes], \"docs_referenced\":[paths], \"summary\":\"<≤120字>\", \"missing_or_inconsistent\":[]}"
   ```
3. **判定**：
   - `PASS` → 工作完成
   - `REFINE/FAIL` → 修 docs 回到 step 1 重跑
4. **轮次上限**：fast 模式最多 3 轮；连续 REFINE 升级 `claude -p` 托底

## 失败回滚

- finish probe FAIL 不回滚已 commit 的代码，改 docs 补全
- docs 写错可 amend 同一 finish_log md
- 仍 FAIL → user-visible 标 BLOCKED，不报"完成"

## 与 meta-self-verify 区别

meta-self-verify 专验 CLAUDE.md 编辑后规则被理解；finish flag 验任意 job 的 commit + docs 一致性。两规则可叠加。

## Applies when

- 任意 job (feature/fix/refactor/chore) 自认完成时

## Do NOT apply when

- 正在进行的中间步骤
- 用户要求跳过 finish 阶段
