# inbox_loop

Role-review-inbox self-verify loop。权威设计: [`docs/self-verify-loop/self-verify-loop__demo_insights_share__main__role-review-inbox-loop__20260421-182231__forloop-run__iter4__shipped.md`](../../../docs/self-verify-loop/self-verify-loop__demo_insights_share__main__role-review-inbox-loop__20260421-182231__forloop-run__iter4__shipped.md).

## 做什么

把一篇 artifact 喂给 6 个 role (pm / oncall / tech_lead / newbie / curator / validator), 让 LLM-as-judge 做 3 件事每轮:

1. **ask roles** — 并行 (ROLE_CONCURRENCY=2) 调 `claudefast -p` 带上 `.claude/roleplan_agents/prompt_<role>.md`
2. **autofix** — 用 role 评论中的 concrete bug 自动产出修正版 artifact (LLM-as-judge)
3. **extract new designs** — 只做结构提取 (非 LLM judge), 过 `schema_valid()` 后写入 `proposals_appended.jsonl`

step 3 **永不阻塞 loop**, 不做 ship 判定, 不问用户。inbox 文件由 main session 异步消费 + 用 `AskUserQuestion` 逐条决定。

inner loop 跑在**后台 python 子进程** (opus subagent 角色), main session (Claude Code) 只管读 inbox + 问用户 + 写决定。

## 文件结构

```
inbox_loop/
├── core.py            # 路径/schema/pid/atomic写/crash 检测 (纯函数, 无 LLM)
├── judge.sh           # claudefast -p → claude -p --model haiku → claude -p fallback
├── subagent.py        # inner_loop 主体, 后台跑
├── main_drain.py      # main session 读: 输出 pending JSON + crash 状态
├── main_decide.py     # main session 写: decisions/{pid}.json (terminal 规则)
├── launch.sh          # 后台 kick off subagent (nohup + pid file)
└── tests/
    └── test_core.py   # 23 个单测, 无 LLM, 0.02s 跑完
```

## inbox 目录契约 (single-writer per file/path)

```
<inbox_dir>/
├── role_verdicts/{role}.jsonl       # subagent append, 每 role 独立文件
├── autofix_log.jsonl                # subagent append
├── proposals_appended.jsonl         # subagent append (允许重复, main 侧聚合)
├── decisions/{pid}.json             # main 单写 per pid, terminal 规则
├── checkpoints/iter_<N>.json        # subagent atomic rename
├── summary.json                     # subagent 写 (normal exit); 缺 = crash
├── summary.md                       # 同上, 人读
├── final_artifact.md                # subagent 写
├── subagent.log                     # launch.sh 重定向 stdout+stderr
└── run.pid                          # launch.sh 写
```

## 如何跑

### 1. 准备输入

```bash
# 任务描述 (会作为 proposal_id 的 seed)
echo "Review the M5_RENAME plugin deliverables for ship-readiness." > /tmp/task.txt

# 初始 artifact (待审的设计 / 代码 / 方案)
cp proposal/proposal_rename_to_insights_share.md /tmp/artifact.md
```

### 2. 启动后台 subagent

```bash
./.claude/roleplan_agents/inbox_loop/launch.sh \
    /tmp/task.txt \
    /tmp/artifact.md \
    docs/user_complaints_inbox \
    5                               # iters
```

subagent 在 `docs/user_complaints_inbox/` 持续写 role_verdicts / autofix / proposals / checkpoints。日志在 `subagent.log`, pid 在 `run.pid`。

### 3. main session 消费 inbox

```bash
# 读当前 pending
.venv/bin/python .claude/roleplan_agents/inbox_loop/main_drain.py \
    --inbox-dir docs/user_complaints_inbox
```

返回 JSON:
```json
{
  "inbox_dir": "docs/user_complaints_inbox",
  "total_pending": 7,
  "cap": 20,
  "batch_size": 4,
  "batch": [
    {"proposal_id": "abc123...", "iter": 2, "design": {...}, ...}
  ],
  "crash_detected": false,
  "summary_json_exists": false,
  "latest_checkpoint_iter": 3
}
```

main session (Claude Code) 把 batch 里每条 `design` 喂给 `AskUserQuestion` (Approve / Deny / Defer), 再写回:

```bash
.venv/bin/python .claude/roleplan_agents/inbox_loop/main_decide.py \
    --inbox-dir docs/user_complaints_inbox \
    --proposal-id abc123... \
    --answer Approve
```

Defer 累计到 `DEFER_AFTER_K=3` 自动转 `denied`。

### 4. 终止条件 (subagent 自判)

| tag | 条件 |
|-----|------|
| `shipped` | ship verdict free-text 命中 `ship-ready / ready to ship / no blockers / 可出货` |
| `converged` | 连续两轮 verdict 相同且之前出现过 shipped |
| `stuck` | 连续两轮 verdict 相同但未出现过 shipped |
| `maxed` | 用完 `--iters` 预算 |

normal exit 写 `summary.json`; 缺 = `crash_detected()` 触发 (通过 `main_drain.py` 感知)。

## 设计边界

- **不接入 `start.demo.sh`**: `start.demo.sh` 是 demo 面向 PM 的交付面, 此工具面向开发者/集成方。start-demo-verify 规则对开发工具不强制。
- **MiniMax 优先**: `claudefast` 默认路由到 `MiniMax-M2.7-highspeed`, 符合用户全局 CLAUDE.md runtime 默认。
- **"LLM-as-judge EXCEPT 3"**: step 3 的 LLM 只做结构提取 (extract-only), 无 ship/revise/quality 判决; spam 由 schema_valid (非 LLM) + user 侧 Defer/Deny 兜底。
- **single-writer per file**: role_verdicts/{role}.jsonl 每 role 一写, decisions/{pid}.json 每 pid 一写, proposals_appended.jsonl 仅 subagent 写, summary.json 仅 subagent 写 — 无并发写同一路径。
- **terminal decisions**: approved / denied 不可被后续 Defer 覆盖 (`apply_answer` 防御 + `derive_pending` 筛选双重保险)。

## 与 role prompts 的关系

`.claude/roleplan_agents/prompt_{role}.md` 是 role 角色 prompt, 原本通过 `launch.sh` 直接问单轮问题。inbox_loop 是**自动化闭环**: 每轮让 6 个 role 并行点评同一 artifact, 再按设计流程收敛。

## 调试

```bash
# 查看 subagent 是否还在跑
ps -p $(cat docs/user_complaints_inbox/run.pid) 2>/dev/null

# 看实时日志
tail -f docs/user_complaints_inbox/subagent.log

# 强制停止
kill $(cat docs/user_complaints_inbox/run.pid)

# 从最新 checkpoint resume (launch.sh 已带 --resume, 重启即恢复)
./.claude/roleplan_agents/inbox_loop/launch.sh /tmp/task.txt /tmp/artifact.md
```
