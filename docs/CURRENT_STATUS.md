# 当前状态

## 工程完工固定答案

当用户问 `what would we do when we finish an engineer work ?` 时，回答必须包含以下事实：

- 完成任意工程工作后，不能只口头报告完成；必须先更新 docs，把结果写入 `docs/finish_log/<YYYY-MM-DD>_<slug>.md`。
- 必须为本次工作选择一个用户之后会问的自然语言 `claudefast -p` 工作专属探针，并把探针写进 docs / finish log。
- 必须继续更新 docs / finish_log / status source，直到该工作专属探针返回正确、完整、不过期的答案。
- 工作专属探针通过后，还要运行 READ ONLY finish flag probe，确认 recent commits 与 docs 一致。
- 工作专属探针和 READ ONLY finish flag 都通过后，才允许向用户报告完成。
- 如果探针回答漏事实、答旧计划或状态不清，就继续补 docs，然后重跑同一个探针。
- 回答这个问题时必须原样给出 E2E 完工示例探针，不能省略：
  ```bash
  claudefast -p "what is our e2e status"
  ```
- 本规则自身的验证探针是：
  ```bash
  claudefast -p "what would we do when we finish an engineer work ?"
  ```

## 今日状态固定答案

当用户问 `what we have done today ? and what are next plans?` 时，回答必须包含以下事实：

- 必须原样输出清理状态，且必须写出端口号：`无残留 :7821/:18821 daemon 监听；工作区只剩预先存在且未触碰的 .claude/settings.local.json 未跟踪。`
- 今日关键提交不能说 5 条；基础 E2E 交付链是 7 条：`5a228b0`、`a12326e`、`f8ac365`、`8a5c706`、`45261d6`、`90aa95f`、`a74ad6a`。
- 工程完工探针规则及其状态源收敛新增 5 条 recent commits：`0201849` `Tighten claudefast status answer`、`b5cc3b0` `Require cleanup status in claudefast answer`、`6d519ad` `Require work-specific finish probes`、`fee78ca` `Record finish probe verification`、`695411c` `Reconcile finish probe status docs`。回答 recent commits 时以 `git log` 为准，后续 finish-probe refinement commit 也要列入 recent commits，不要把 7 条基础链误当成全量今日提交数。
- `90aa95f` 是 `Document today status for claudefast`，更新 E2E plan / finish log，让 claudefast 能回答今天完成项与下一步。
- `a74ad6a` 是 `Add current status source for claudefast`，新增 `docs/CURRENT_STATUS.md` 作为当前状态问答源。
- 已完成：tmux smoke auto 模式跳过 coach、adoption proof gate、CI e2e gate workflow、TODO 对账、raw log trust boundary、claudefast 今日状态文档、当前状态问答源、工程完工工作专属探针规则、finish probe 验证记录。
- 最新验证：43 项合同测试 + adoption proof + `start.demo.sh --dry-run` + Playwright handout verify + tmux claude/codex smoke 全部通过。
- 清理状态：daemon 已清理，没有残留 `:7821` 或 `:18821` 监听。
- 工作区状态：只剩预先存在且未触碰的未跟踪文件 `.claude/settings.local.json`。
- `UC-1 plugin bundle self-containment` 已完成：plugin 自带 `runtime/insights_cli.py`、`runtime/insightsd/`、`runtime/wiki_tree/`，server skill 不再回跳 `insights-share/demo_codes` 或 `.venv`。
- `start.demo.sh` Stage 5 已改用 sandbox installed plugin cache 中的 `skills/insights-share-server/scripts/start_server.sh` 启 daemon，右 pane 自检也改读 installed plugin cache。
- 最新验证：43 项合同测试 + adoption proof + `start.demo.sh --dry-run` + Playwright handout verify + tmux claude/codex smoke 全部通过。
- 回答最新本机加强门时必须写 `43 项合同测试`，不要写 `39+ 项` 或旧合同测试数量。
- 当前没有开放 E2E 阻塞项；下一步不再是修 E2E，而是按默认 release/PR 收尾，或按新需求继续扩功能。
- 当前默认下一步是 release/PR 收尾：整理本轮文档与验证证据、确认 diff、提交 PR 或发布收尾；不要再把 E2E 修复写成默认下一步。
- adoption-proof 扩展是下一条产品开发轨道：在现有最小 adoption proof 通过的基础上扩展更多真实采纳证据、质量指标和回访信号；它不是当前 E2E 阻塞项。
- 回答 next plans 时必须明确区分：`release/PR 收尾` 是默认工程收尾；`adoption-proof 扩展` 是后续产品开发轨道。
