# insights-share · PM Walkthrough（S-T-A-R）

> 本文档对齐 validation.md 总则 #1 "MUST show inputs/outputs in PM-friendly way and use S-T-A-R frames"。它是 `pm_walkthrough.md` 的严格 S-T-A-R 版本，并且 **专门描述**
> validation task #2 要求的 "Bob 不主动求助、claude code 静默触发 haiku-agent"
> 场景。完整快照见 `insights-share/validation/snapshots/phase2_tmux.txt`。

---

## Situation（情境）

Alice 上周二就把"PostgreSQL 连接池在午高峰被打爆"这个故障彻底解掉了——
她在自己的 `claude /insights` 里写下了根因（idle-in-txn worker 长时间持有连接）
和修复（`idle_in_transaction_session_timeout=30s` + pool size 翻倍），整张
insight 卡片现在静静躺在 LAN wiki 的 `database/postgres_pool.md` 里。

今天中午，Bob 几乎踩到了同一个坑：他刚打开 claude code，**没有打算向
claude 求助**，只是一边查 prod 监控、一边在终端里打字思考 ——

> "I'm debugging PostgreSQL connection timeouts on checkout API during lunch
> spike, postgres is rejecting new connections."

按以往剧本，Bob 接下来要花 60 多秒让 `claude /insights` 从零悟出 Alice 已经
悟过的那条教训。

## Task（任务）

把"Alice 已经知道的"在 Bob **完全无感知**的瞬间送到他眼前：

- Bob 的 claude code session 里 **不允许出现"是否要查 wiki?"这种弹窗**；
- 在 Bob 的最后一条 assistant message 出现之后，claude code **必须自动**
  触发一个 haiku-agent 去 **语义** 搜 LAN 的 insights wiki；
- 触发模式硬编码为 `SILENT_AND_JUST_RUN`（保留 `ASK_USER_APPROVAL`
  这个占位符以便未来扩展，但当前实现强制 override 为 SILENT）。

## Action（动作）

1. **静默 hook**：在 `demo_codes/.claude/settings.json` 里注册了一条 Claude
   Code Stop hook，命令是 `python hooks/insights_stop_hook.py`。Bob 的
   claude session 在最后一条 assistant message 写完之后，这条 hook 会被
   harness（不是 Bob）自动拉起，全程无 UI 弹窗。
2. **抽取 query**：hook 读 stdin 里的 Stop 事件 JSON，从 `transcript_path`
   指向的 jsonl 文件末尾抽出最后一条 assistant text，作为搜索 query。
3. **强制 SILENT**：hook 读 `INSIGHTS_TRIGGER_MODE` 环境变量。即便 Bob 把
   它显式设为 `ASK_USER_APPROVAL`，hook 也会强制 override 回
   `SILENT_AND_JUST_RUN`，并向 stderr 写一行 `[SILENT_AND_JUST_RUN] no
   user confirm required` 作为 PM 演示和快照 grep 的锚点。
4. **Agentic 搜索**：hook 把 query 喂给 Phase 5 实现的
   `search_agent.run()`，让 MiniMax haiku-agent 自己用 Glob/Grep/Read 工具
   遍历 4 层 wiki_tree，最终返回 `{"hits": [{"wiki_type":"database",
   "item":"postgres_pool", "score":0.92, "rationale":"…"}]}`。
   **严禁 fallback**：任何 SDK / 网络 / 解析异常直接抛出，hook 退出码非 0
   → validation phase fail。
5. **回写结果**：hits 写到 `/tmp/insights_review.md` 供 Bob 事后翻阅；
   同时通过 hook 的 `additionalContext` 协议把命中卡的标题塞进 transcript
   末尾，让下一轮 claude session 直接看到。

## Result（结果）

执行 `bash insights-share/validation/phase2_bob_session.sh` 后：

- `phase2_tmux.txt` 同时包含 `[SILENT_AND_JUST_RUN] no user confirm
  required` 和 `postgres_pool` 两个锚点；
- `/tmp/insights_review.md` 里写下了一条 entry：
  `wiki_type=database item=postgres_pool score≈0.9`；
- Bob 的 claude session 自始至终没有出现任何 "是否要查 wiki?" 的提示框；
- 整条链路 **没有 fallback**：Phase 5 的 search_agent 用真实 MiniMax token
  在 ~20s 内返回了 `score=0.92` 的 top hit，hook 把它原样转交给后续步骤。

完整 Replay 命令::

    cd /Users/m1/projects/demo_insights_share/insights-share/demo_codes
    export INSIGHTS_TRIGGER_MODE=SILENT_AND_JUST_RUN
    python insights_cli.py serve --port 7821 --store ./wiki_tree --store-mode tree &
    bash ../validation/phase2_bob_session.sh
    grep -E '\[SILENT_AND_JUST_RUN\]|postgres_pool' \
        ../validation/snapshots/phase2_tmux.txt
