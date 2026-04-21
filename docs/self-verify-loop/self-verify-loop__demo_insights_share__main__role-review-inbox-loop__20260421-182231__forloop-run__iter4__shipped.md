# self-verify-loop plan

- task: design a for-loop that (1) asks 6 roles for comments via claudefast -p LLM-judge, (2) auto-fixes bugs via claudefast -p LLM-judge, (3) drafts new designs from role comments — step 3 is main-session-only via AskUserQuestion; inner loop runs in opus subagent; step 3 never creates a stuck point; drafts land in a "user complaints inbox" and are reported to main session
- project: demo_insights_share
- branch: main
- generated: 2026-04-21T18:22:31+08:00
- N budget: 3
- mode: plan-only (未执行)

## pseudo for-loop

```text
# === inputs ===
task              = <原始任务字面>
artifact_0        = <初版产物 / 设计>
roles             = [pm, oncall, tech_lead, newbie, curator, validator]
role_prompt_dir   = .claude/roleplan_agents/
N                 = 5
inbox_dir         = <project>/docs/user_complaints_inbox/
  ├─ proposals_pending.jsonl       # step 3 drafts, status=pending_user_review
  ├─ role_verdicts.jsonl           # step 1 raw
  ├─ autofix_log.jsonl             # step 2 patches
  └─ summary.md                    # written when loop ends

# === main session ===
spawn opus subagent (background) with:
    tools  = [Read, Write, Edit, Bash]
    prompt = """run inner_loop(task, artifact_0, N);
               append to inbox_dir; do NOT call AskUserQuestion;
               on finish write summary.md and exit"""

main session NOT blocked. main continues other work.
main periodically (or on subagent-complete):
    pending = read_jsonl(inbox_dir/proposals_pending.jsonl)
              where status == "pending_user_review"
    if pending non-empty:
        for each proposal (or batched group ≤4):
            ans = AskUserQuestion(question, preview, [Approve, Deny, Defer])
            update proposal.status = ans

# === inner_loop (runs inside opus subagent) ===
prior_ship_verdict = None
for i in 1..N:
    # step 1 — ask 6 roles in parallel
    role_comments = {}
    for role in roles (parallel):
        p = read(role_prompt_dir + "prompt_" + role + ".md")
              + "\n\n---\n## review this artifact (iter " + i + ")\n\n"
              + artifact_i
        role_comments[role] = claudefast_p(p)          # LLM-as-judge #1
    append_jsonl(inbox_dir/role_verdicts.jsonl, {iter, comments, ts})

    # step 2 — auto-fix concrete bugs
    fix_verdict = claudefast_p("""
        task, artifact, role_comments.
        只挑 concrete bugs (code/logic/schema/contract/命名错/路径错).
        若有 → FIXED:\n<完整修正后 artifact>
        若无 → NOBUG
        忽略"升级建议"或"新设计", 留给 step 3.
    """)                                               # LLM-as-judge #2
    artifact_next = parse_fixed(fix_verdict) if startswith "FIXED:" else artifact_i
    if fixed: append_jsonl(inbox_dir/autofix_log.jsonl, {iter, diff})

    # step 3 — distill new designs (NO judge, NO ask from subagent)
    proposals = claudefast_p("""
        从 role_comments 抽"升级建议/新设计"→ JSON 数组, 每条 {title, rationale, affected_roles, impact}.
        只抽超出 artifact 范围的, 不重复 step 2.
    """)                                               # extract-only, 非裁决
    for p in proposals:
        append_jsonl(inbox_dir/proposals_pending.jsonl,
            {iter, design:p, source_roles, status:"pending_user_review", ts})
    # NOTE: 不调 AskUserQuestion; 不等用户; step 3 不参与 break 条件

    # convergence — step 1 + step 2 only, 忽略 step 3
    ship_verdict = claudefast_p("""
        task, artifact_next, role_comments, autofix_applied.
        忽略 "proposal for new design" — 已入 inbox, 不卡 loop.
        基于 role 点评 + autofix 后, 本 artifact 可出货? 自由作答.
    """)                                               # LLM-as-judge #3
    if ship_verdict reads-as "ship/ready/no blockers":
        break
    if ship_verdict == prior_ship_verdict (2 轮同话):
        break                                          # 收敛或 stuck 都停
    prior_ship_verdict = ship_verdict
    artifact_i = artifact_next

write(inbox_dir/summary.md, {
    final_artifact, ship_verdict, iters_used,
    pending_proposals_count, autofix_count, inbox_path
})
return (artifact_final, ship_verdict, inbox_dir)
```

## 本次裁判切入点（给下轮 agent 参考）

审的维度 (由裁判自选, 以下仅建议):

1. **inbox contract 正确性**: proposals_pending.jsonl 的 schema 是否完备 (iter/design/source_roles/status/ts)? 状态流转 pending_user_review → approved/denied/deferred 是否闭环?
2. **step 3 真的非 stuck**: 是否任何 code path 会让 step 3 结果卡住 loop? 比如空 proposals 时是否仍继续? proposals 过多时是否压垮 main session?
3. **claudefast 使用边界**: step 1 / step 2 / ship 判定用 judge (verdict 语义); step 3 仅 extract (结构提取), 没有 ship/revise 语义判决 — 区分是否清晰?
4. **main/subagent 分离干净**: subagent 绝不调 AskUserQuestion, main 绝不直接跑 inner_loop iter; 耦合点只在 inbox_dir 文件系统
5. **edge cases**: subagent crash 后 inbox 是否可恢复? main 未及时 poll 时 proposals 堆积的上限? 同一 proposal 重复 append 如何去重?
6. **role prompt 加载**: `.claude/roleplan_agents/prompt_<role>.md` 路径是否稳定? 新增 role 时 inner_loop 是否自动发现 (glob)?
7. **终止语义**: break 条件分别对应 verdict = shipped / converged / stuck / maxed, 与 skill spec 对齐
8. **parallel roles**: 6 role 并行用 Agent subagent 嵌套 opus 内, 开销可控?

ship 判定标准 (软):

- 裁判自由文本读出"ready / no blockers / ship" → shipped
- 裁判列出具体修复清单 → revise
- 连续两轮 verdict 相同 → 停 (收敛或 stuck)

---

mode: executed

# run trace (self-verify-loop --save --run)

- iters_used: 4
- verdict_tag: shipped
- judge fallback chain: claudefast -p (MiniMax-M2.7-highspeed via /Users/m1/.local/bin/claudefast) — all 4 iters succeeded at layer 1


## iter 1

### artifact (iter 1)

```markdown
# self-verify-loop plan

- task: design a for-loop that (1) asks 6 roles for comments via claudefast -p LLM-judge, (2) auto-fixes bugs via claudefast -p LLM-judge, (3) drafts new designs from role comments — step 3 is main-session-only via AskUserQuestion; inner loop runs in opus subagent; step 3 never creates a stuck point; drafts land in a "user complaints inbox" and are reported to main session
- project: demo_insights_share
- branch: main
- generated: 2026-04-21T18:22:31+08:00
- N budget: 3
- mode: plan-only (未执行)

## pseudo for-loop

```text
# === inputs ===
task              = <原始任务字面>
artifact_0        = <初版产物 / 设计>
roles             = [pm, oncall, tech_lead, newbie, curator, validator]
role_prompt_dir   = .claude/roleplan_agents/
N                 = 5
inbox_dir         = <project>/docs/user_complaints_inbox/
  ├─ proposals_pending.jsonl       # step 3 drafts, status=pending_user_review
  ├─ role_verdicts.jsonl           # step 1 raw
  ├─ autofix_log.jsonl             # step 2 patches
  └─ summary.md                    # written when loop ends

# === main session ===
spawn opus subagent (background) with:
    tools  = [Read, Write, Edit, Bash]
    prompt = """run inner_loop(task, artifact_0, N);
               append to inbox_dir; do NOT call AskUserQuestion;
               on finish write summary.md and exit"""

main session NOT blocked. main continues other work.
main periodically (or on subagent-complete):
    pending = read_jsonl(inbox_dir/proposals_pending.jsonl)
              where status == "pending_user_review"
    if pending non-empty:
        for each proposal (or batched group ≤4):
            ans = AskUserQuestion(question, preview, [Approve, Deny, Defer])
            update proposal.status = ans

# === inner_loop (runs inside opus subagent) ===
prior_ship_verdict = None
for i in 1..N:
    # step 1 — ask 6 roles in parallel
    role_comments = {}
    for role in roles (parallel):
        p = read(role_prompt_dir + "prompt_" + role + ".md")
              + "\n\n---\n## review this artifact (iter " + i + ")\n\n"
              + artifact_i
        role_comments[role] = claudefast_p(p)          # LLM-as-judge #1
    append_jsonl(inbox_dir/role_verdicts.jsonl, {iter, comments, ts})

    # step 2 — auto-fix concrete bugs
    fix_verdict = claudefast_p("""
        task, artifact, role_comments.
        只挑 concrete bugs (code/logic/schema/contract/命名错/路径错).
        若有 → FIXED:\n<完整修正后 artifact>
        若无 → NOBUG
        忽略"升级建议"或"新设计", 留给 step 3.
    """)                                               # LLM-as-judge #2
    artifact_next = parse_fixed(fix_verdict) if startswith "FIXED:" else artifact_i
    if fixed: append_jsonl(inbox_dir/autofix_log.jsonl, {iter, diff})

    # step 3 — distill new designs (NO judge, NO ask from subagent)
    proposals = claudefast_p("""
        从 role_comments 抽"升级建议/新设计"→ JSON 数组, 每条 {title, rationale, affected_roles, impact}.
        只抽超出 artifact 范围的, 不重复 step 2.
    """)                                               # extract-only, 非裁决
    for p in proposals:
        append_jsonl(inbox_dir/proposals_pending.jsonl,
            {iter, design:p, source_roles, status:"pending_user_review", ts})
    # NOTE: 不调 AskUserQuestion; 不等用户; step 3 不参与 break 条件

    # convergence — step 1 + step 2 only, 忽略 step 3
    ship_verdict = claudefast_p("""
        task, artifact_next, role_comments, autofix_applied.
        忽略 "proposal for new design" — 已入 inbox, 不卡 loop.
        基于 role 点评 + autofix 后, 本 artifact 可出货? 自由作答.
    """)                                               # LLM-as-judge #3
    if ship_verdict reads-as "ship/ready/no blockers":
        break
    if ship_verdict == prior_ship_verdict (2 轮同话):
        break                                          # 收敛或 stuck 都停
    prior_ship_verdict = ship_verdict
    artifact_i = artifact_next

write(inbox_dir/summary.md, {
    final_artifact, ship_verdict, iters_used,
    pending_proposals_count, autofix_count, inbox_path
})
return (artifact_final, ship_verdict, inbox_dir)
```

## 本次裁判切入点（给下轮 agent 参考）

审的维度 (由裁判自选, 以下仅建议):

1. **inbox contract 正确性**: proposals_pending.jsonl 的 schema 是否完备 (iter/design/source_roles/status/ts)? 状态流转 pending_user_review → approved/denied/deferred 是否闭环?
2. **step 3 真的非 stuck**: 是否任何 code path 会让 step 3 结果卡住 loop? 比如空 proposals 时是否仍继续? proposals 过多时是否压垮 main session?
3. **claudefast 使用边界**: step 1 / step 2 / ship 判定用 judge (verdict 语义); step 3 仅 extract (结构提取), 没有 ship/revise 语义判决 — 区分是否清晰?
4. **main/subagent 分离干净**: subagent 绝不调 AskUserQuestion, main 绝不直接跑 inner_loop iter; 耦合点只在 inbox_dir 文件系统
5. **edge cases**: subagent crash 后 inbox 是否可恢复? main 未及时 poll 时 proposals 堆积的上限? 同一 proposal 重复 append 如何去重?
6. **role prompt 加载**: `.claude/roleplan_agents/prompt_<role>.md` 路径是否稳定? 新增 role 时 inner_loop 是否自动发现 (glob)?
7. **终止语义**: break 条件分别对应 verdict = shipped / converged / stuck / maxed, 与 skill spec 对齐
8. **parallel roles**: 6 role 并行用 Agent subagent 嵌套 opus 内, 开销可控?

ship 判定标准 (软):

- 裁判自由文本读出"ready / no blockers / ship" → shipped
- 裁判列出具体修复清单 → revise
- 连续两轮 verdict 相同 → 停 (收敛或 stuck)
```

### judge prompt (iter 1) — abbreviated

```text
You are an open-ended design reviewer.

TASK (verbatim user request):
design a for loop to 1. ask roles for comments 2. auto-fix the bugs if have 3. draft new designs from role comments and ask users to approve or deny with ask user question tool. use claudefast -p to offer LLM-as-judge EXCEPT 3 please. we also design this loop in opus subagents and in main session only report 3. 3 should NOT work as a stuck point and should by default ignore it and add a "user complaints inbox" to store them and report to main session.

CURRENT ARTIFACT (iter 1, a pseudo for-loop markdown):
---BEGIN_ARTIFACT---
# self-verify-loop plan

- task: design a for-loop that (1) asks 6 roles for comments via claudefast -p LLM-judge, (2) auto-fixes bugs via claudefast -p LLM-judge, (3) drafts new designs from role comments — step 3 is main-session-only via AskUserQuestion; inner loop runs in opus subagent; step 3 never creates a stuck point; drafts land in a "user complaints inbox" and are reported to main session
- project: demo_insights_share
- branch: main
- generated: 2026-04-21T18:22:31+08:00
- N budget: 3
- mode: plan-only (未执行)

## pseudo for-loop

```text
# === inputs ===
task              = <原始任务字面>
artifact_0        = <初版产物 / 设计>
roles             = [pm, oncall, tech_lead, newbie, curator, validator]
role_prompt_dir   = .claude/roleplan_agents/
N                 = 5
inbox_dir         = <project>/docs/user_complaints_inbox/
  ├─ proposals_pending.jsonl       # step 3 drafts, status=pending_user_review
  ├─ role_verdicts.jsonl           # step 1 raw
  ├─ autofix_log.jsonl             # step 2 patches
  └─ summary.md                    # written when loop ends

# === main session ===
spawn opus subagent (background) with:
    tools  = [Read, Write, Edit, Bash]
    prompt = """run inner_loop(task, artifact_0, N);
               append to inbox_dir; do NOT call AskUserQuestion;
               on finish write summary.md and exit"""

main session NOT blocked. main continues other work.
main periodically (or on subagent-complete):
...
(full artifact embedded above; full prompt preserved in /tmp/svl_iter1_prompt_final.txt at run time)
```

### judge verdict (iter 1)

```text
Design 有几个硬伤，直接列：

**1. Step 3 仍会卡住 — AskUserQuestion 是阻塞的**

文档说 step 3 不卡 loop，但 main session 在 `on subagent-complete` 时会调 AskUserQuestion。如果 user 长期不响应，pending proposals 堆积，main session 每次启动都拿到同一批。如果 user 在移动端「假装没看见」，所有后续 iteration 产物全部 pending — inbox 无上限。

**修复**：AskUserQuestion 必须带 timeout 或 deferred 计数门控。连续 K 个 pending 就自动 skip，主 session 只在 user 有响应时才处理。

**2. proposals_pending.jsonl 缺 unique key，dedup 无解**

每轮 step 3 append，相同 role 的相同 proposal 会被重复写入。iter 不同但 design 完全一致，两条 record 同时 pending。AskUserQuestion 用户看到重复会困惑。

**修复**：schema 加 `proposal_id = SHA256(task + design.title + design.rationale)`，append 前查重。

**3.  subagent crash = loop 中途停止，无 checkpoint**

每轮 Write 后没有 snapshot。如果第 3 轮崩了，已 append 的 role_verdicts 和 autofix_log 是残缺的，summary.md 不会写，main session 不知道是崩溃还是还在跑。

**修复**：每轮迭代写 `inbox_dir/iter_N_checkpoint.jsonl`，含 artifact_next 快照 + iters_run。subagent 启动时读最新 checkpoint 恢复。

**4. inbox_dir 路径是 template，artifact 未填充**

`<project>/docs/user_complaints_inbox/` 实际项目是 `demo_insights_share`，但代码里没写死。

**5. N budget 在代码里未体现**

pseudo 里写 `for i in 1..N` 但 N 没作为参数传入 inner_loop，只在注释里是 `N = 5`。如果 outer caller 想传不同 budget，无法注入。

**6. main session 轮询策略缺失**

`periodically (or on subagent-complete)` 太模糊。subagent-complete 时 main 收到通知没问题，但「定期轮询」是多久一次？ Proposals 堆积时 main 怎么知道？

---

**结论**：不是 ship-ready 状态。核心问题是 step 3 的「忽略」和「堆积」之间的边界没划清楚 — inbox 是无限大的 leak，user 不响应时整个机制退化。

最小修复路径：加 proposal dedup + AskUserQuestion timeout/defer 门控 + iter checkpoint。其他的可以慢慢补。```

## iter 2

### artifact (iter 2)

```markdown
# self-verify-loop plan (iter 2, revised)

- task: design a for-loop (ask roles → auto-fix → distill designs → main-only AskUserQuestion); inner loop in opus subagent; step 3 never blocks; user complaints inbox; claudefast-as-judge for 1+2+ship, extract-only for 3.
- project: demo_insights_share
- N budget: 5

## pseudo for-loop (revised v2)

```text
# === inputs (typed) ===
task              : str                # 原始任务字面
artifact_0        : str                # 初版产物
roles             : list = [pm, oncall, tech_lead, newbie, curator, validator]
role_prompt_dir   : path = .claude/roleplan_agents/
N                 : int  = 5                         # FIX#5: 显式参数, 可注入
inbox_dir         : path = docs/user_complaints_inbox/   # FIX#4: 具体到 demo_insights_share
MAX_PENDING       : int  = 20                        # FIX#1: inbox 软上限
DEFER_AFTER_K     : int  = 3                         # FIX#1: 同一 proposal 被 Defer K 次自动 skip

# === inbox layout (每文件 schema) ===
inbox_dir/
├── proposals_pending.jsonl     # {proposal_id, iter, design, source_roles, status, defer_count, ts}
├── role_verdicts.jsonl         # {iter, role, comment, ts}
├── autofix_log.jsonl           # {iter, diff, ts}
├── checkpoints/                # FIX#3: 每轮 snapshot
│   └── iter_<N>_checkpoint.json  # {iter, artifact_next, ship_verdict_prev, iters_done, ts}
└── summary.md                  # 仅 loop 正常结束时写; crash 时不写, 靠 checkpoints 恢复

# === proposal_id schema (FIX#2: dedup) ===
proposal_id = sha256(task + "|" + design.title + "|" + design.rationale)[:16]

# === main session ===
spawn opus subagent (background, task_id=T) with:
    tools  = [Read, Write, Edit, Bash]
    input  = {task, artifact_0, N, inbox_dir, resume_from_checkpoint: true}
    prompt = """
      if exists(inbox_dir/checkpoints/iter_*_checkpoint.json):
          latest = argmax(iter, glob)
          resume from latest.artifact_next, iters_done
      else:
          start fresh
      run inner_loop; append to inbox_dir; DO NOT call AskUserQuestion;
      on each iter finish, write iter_<N>_checkpoint.json (atomic rename);
      on normal finish write summary.md
    """

main session NOT blocked.
main polling (FIX#6: explicit cadence):
    trigger = (subagent-complete event) OR (manual user cmd /inbox-drain) OR (periodic 10 min tick)
    NOT while-loop sleep-polling (浪费 context)

    pending = read_jsonl(inbox_dir/proposals_pending.jsonl)
              where status == "pending_user_review"
              dedup by proposal_id (take first)
              exclude defer_count >= DEFER_AFTER_K
    if len(pending) > MAX_PENDING:
        report_to_user(f"inbox saturated: {len(pending)} pending; showing top {MAX_PENDING} by recency")
        pending = pending[-MAX_PENDING:]
    batch = pending[:4]    # AskUserQuestion 最多 4 题/batch
    for p in batch:
        ans = AskUserQuestion(
            question = f"proposal from {p.source_roles}: {p.design.title}?",
            preview  = p.design.rationale + "\n\nimpact: " + p.design.impact,
            options  = [Approve, Deny, Defer]
        )
        if ans == "Defer":
            p.defer_count += 1
        p.status = ans.lower()
        p.ts_resolved = now
        # 原地重写 (jsonl 重写非 append, 避免重复)

# === inner_loop (在 opus subagent 执行; 纯函数式, 副作用仅对 inbox) ===
def inner_loop(task, artifact_0, N, inbox_dir):
    artifact_i = artifact_0
    prior_ship_verdict = None
    start_iter = 1

    # FIX#3: resume from checkpoint
    ckpts = glob(inbox_dir + "/checkpoints/iter_*_checkpoint.json")
    if ckpts:
        latest = max(ckpts, key=lambda f: parse_iter(f))
        ck = json.load(latest)
        artifact_i = ck.artifact_next
        prior_ship_verdict = ck.ship_verdict_prev
        start_iter = ck.iters_done + 1

    for i in start_iter..N:
        # step 1: ask 6 roles (parallel)
        role_comments = {}
        for role in roles (parallel via subagent or seq):
            p = read(role_prompt_dir + "prompt_" + role + ".md")
                  + "\n---\n## review iter " + i + "\n\n" + artifact_i
            role_comments[role] = claudefast_p(p)     # judge #1
        append_jsonl(inbox_dir/role_verdicts.jsonl, {iter:i, role:role, ...})

        # step 2: auto-fix concrete bugs
        fix_verdict = claudefast_p("""
            task, artifact, role_comments.
            只挑 concrete bugs (code/logic/schema/contract/命名/路径).
            有 → FIXED:\n<完整 artifact>    无 → NOBUG    忽略"升级建议"(留 step 3).
        """)                                          # judge #2
        if fix_verdict startswith "FIXED:":
            artifact_next = parse(fix_verdict)
            append_jsonl(inbox_dir/autofix_log.jsonl, {iter:i, diff})
        else:
            artifact_next = artifact_i

        # step 3: distill (NO judge, NO ask, NO block)
        proposals = claudefast_p("""
            extract-only: 从 role_comments 抽新设计 → JSON [{title, rationale, affected_roles, impact}]
            忽略已在 step 2 修掉的内容.
        """)                                          # extract-only
        for d in proposals:
            pid = sha256(task + "|" + d.title + "|" + d.rationale)[:16]
            if exists proposals_pending.jsonl where proposal_id == pid:
                continue                              # FIX#2: dedup
            append_jsonl(proposals_pending.jsonl, {
                proposal_id: pid, iter:i, design:d, source_roles,
                status:"pending_user_review", defer_count:0, ts:now
            })
        # step 3 不影响 break; 空 proposals 正常, 仍继续

        # ship 判定 (步骤 1+2, 忽略 step 3)
        ship_verdict = claudefast_p("""
            task, artifact_next, role_comments, autofix_applied.
            忽略所有 "new design proposal" — 已入 inbox, 不卡 loop.
            基于 role 点评 + autofix, 本 artifact 可出货? 自由作答.
        """)                                          # judge #3

        # FIX#3: checkpoint (atomic: write .tmp 再 rename)
        write_atomic(inbox_dir/f"checkpoints/iter_{i}_checkpoint.json", {
            iter:i, artifact_next, ship_verdict_prev: ship_verdict,
            iters_done:i, ts:now
        })

        if ship_verdict reads-as "ship/ready/no blockers":
            verdict_tag = "shipped"; artifact_final = artifact_next; break
        if ship_verdict == prior_ship_verdict:        # 2 轮同话
            verdict_tag = ("converged" if 上轮 shipped else "stuck")
            artifact_final = artifact_next; break
        prior_ship_verdict = ship_verdict
        artifact_i = artifact_next
    else:
        verdict_tag = "maxed"; artifact_final = artifact_i

    write(inbox_dir/summary.md, {
        final_artifact, ship_verdict: prior_ship_verdict, verdict_tag,
        iters_used: i, pending_count, autofix_count, inbox_path: inbox_dir
    })
    return (artifact_final, verdict_tag, inbox_dir)
```

## 本次裁判切入点（iter 2）

此版针对 iter 1 verdict 的 6 条修复:

- FIX#1: AskUserQuestion 上 MAX_PENDING + DEFER_AFTER_K 门控, 不再无上限
- FIX#2: proposal_id = sha256(...) dedup, append 前查重
- FIX#3: 每轮 atomic checkpoint + resume-from-latest, subagent crash 可恢复
- FIX#4: inbox_dir 具体到 `demo_insights_share/docs/user_complaints_inbox/`
- FIX#5: N 作为 inner_loop 显式参数, 可由 caller 注入
- FIX#6: main polling 改为事件驱动 (subagent-complete / 手动 /inbox-drain / 定期 10 min), 不用 busy loop

剩余开放点 (裁判可质疑):

- role prompt 并行时的 token 成本上限
- defer_count 是否应该跨 session 持久化 (现在持久化了, jsonl 原地重写)
- summary.md 与 checkpoints/ 的职责分离: summary 仅 happy path, crash 靠 checkpoints
```

### judge prompt (iter 2) — abbreviated

```text
You are an open-ended design reviewer.

TASK (verbatim user request):
design a for loop to 1. ask roles for comments 2. auto-fix the bugs if have 3. draft new designs from role comments and ask users to approve or deny with ask user question tool. use claudefast -p to offer LLM-as-judge EXCEPT 3 please. we also design this loop in opus subagents and in main session only report 3. 3 should NOT work as a stuck point and should by default ignore it and add a "user complaints inbox" to store them and report to main session.

PRIOR VERDICT (iter 1): the previous version had 6 concrete issues — AskUserQuestion blocking w/o timeout, no proposal dedup, no checkpoint on subagent crash, inbox_dir un-concrete, N not a parameter, main polling cadence vague. The author applied fixes; see FIX#1 through FIX#6 in this iter 2 artifact.

CURRENT ARTIFACT (iter 2):
---BEGIN_ARTIFACT---
# self-verify-loop plan (iter 2, revised)

- task: design a for-loop (ask roles → auto-fix → distill designs → main-only AskUserQuestion); inner loop in opus subagent; step 3 never blocks; user complaints inbox; claudefast-as-judge for 1+2+ship, extract-only for 3.
- project: demo_insights_share
- N budget: 5

## pseudo for-loop (revised v2)

```text
# === inputs (typed) ===
task              : str                # 原始任务字面
artifact_0        : str                # 初版产物
roles             : list = [pm, oncall, tech_lead, newbie, curator, validator]
role_prompt_dir   : path = .claude/roleplan_agents/
N                 : int  = 5                         # FIX#5: 显式参数, 可注入
inbox_dir         : path = docs/user_complaints_inbox/   # FIX#4: 具体到 demo_insights_share
MAX_PENDING       : int  = 20                        # FIX#1: inbox 软上限
DEFER_AFTER_K     : int  = 3                         # FIX#1: 同一 proposal 被 Defer K 次自动 skip

# === inbox layout (每文件 schema) ===
inbox_dir/
├── proposals_pending.jsonl     # {proposal_id, iter, design, source_roles, status, defer_count, ts}
├── role_verdicts.jsonl         # {iter, role, comment, ts}
├── autofix_log.jsonl           # {iter, diff, ts}
├── checkpoints/                # FIX#3: 每轮 snapshot
│   └── iter_<N>_checkpoint.json  # {iter, artifact_next, ship_verdict_prev, iters_done, ts}
└── summary.md                  # 仅 loop 正常结束时写; crash 时不写, 靠 checkpoints 恢复

# === proposal_id schema (FIX#2: dedup) ===
proposal_id = sha256(task + "|" + design.title + "|" + design.rationale)[:16]

...
(full artifact embedded above; full prompt preserved in /tmp/svl_iter2_prompt_final.txt at run time)
```

### judge verdict (iter 2)

```text
## iter-2 review

### FIX#1–#6 实际检查

**FIX#1 (AskUserQuestion 软上限):** MAX_PENDING=20 + DEFER_AFTER_K=3 有数量限制，但实现有漏洞——`pending` 取的是 `status=="pending_user_review"` 的全部记录，defer_count 不影响入队，只要没被用户 resolve 就一直占名额。真正能 bound 增长的只有 MAX_PENDING 截断，但 `batch = pending[:4]` 每次只问 4 个，20 个 pending 全是 "pending_user_review" 时，后 16 个永远沉底等不到服务。inbox 不会爆，但会饿死人。

**FIX#3 (checkpoint 恢复):** 恢复时 partial iteration 的副作用残留在 jsonl 里——role_verdicts 和 autofix_log 中对应 crashed iter 的行不会被清理。resume 后同一批 role 又被 query 一遍，fix 又被 apply 一遍（可能重复 apply），虽然 artifact_next 最终一致，但 jsonl 里有脏数据。语义上不对。

**FIX#6 (事件驱动 polling):** "write .tmp 再 atomic rename" 在 subagent crash 时会产生孤立的 .tmp 文件。如果 rename 没发生（subagent kill -9），下次 resume 时 glob `iter_*_checkpoint.json` 会匹配到 .tmp 但 json.load 失败。

### 新问题

**inbox jsonl in-place rewrite 不是原子的。** `proposals_pending.jsonl` 中某条记录被用户 resolve 后，代码说"原地重写"，但 jsonl 是行Append文件，没有原地改的结构。实际做法是读全量→过滤→写全量。这与 role_verdicts/autofix_log 的 append 模式不一致，而且写全量时 main session 如果在读，会读到半截文件。race condition 明确存在。

**main session 读取 inbox 时 subagent 可能同时在写 proposals_pending.jsonl**（上一条问题）。没有文件锁或 write-ahead log 来保证一致性。

**defer_count 跨 session 持久化但无 escape hatch。** N 轮 loop 跑完，所有还是 "pending_user_review" 状态的 proposal（包括被defer过但未超 K 的）直接写入 summary.md 的 pending_count 然后被遗忘。这些 proposal 的 defer_count 也随之沉底，用户永远不知道有这些东西在 inbox 里躺着。

**step 3 extract-only 模式不judge——设计质量没人把关。** 所有 role comment 里含的 new design proposal 照单全收，只要 sha256 不重复就入 inbox。没有过滤"这个 proposal 实际上会导致 X 问题"的判断。

**inner_loop 返回 tuple `(artifact_final, verdict_tag, inbox_dir)` 给 background opus subagent——这不会传回主 session。** subagent background mode 下 return 值丢失，只能靠写文件通信。

**proposals_pending.jsonl 的 dedup 检查有竞速窗口。** 检查 `exists proposals_pending.jsonl where proposal_id == pid` 和实际 append 之间，别的 iter 或别的 subagent 可能已经写入了同名 pid。

**role 并行没有 token 预算。** roles=[pm, oncall, tech_lead, newbie, curator, validator] 6 个并行调用，每个 role_prompt_dir 读文件 + claudefast_p 调用，没有并发上限，token 燃烧率不可控。

**summary.md 只写正常结束，crash 时不写——但 main session 也不知道 subagent 什么时候彻底死掉。** 没有 dead-letter 检测。

### 总结

6 个 FIX 中 FIX#2 (dedup) 和 FIX#5 (N 参数) 真正 resolve 了。FIX#1 部分有效但 inbox 会饿死。FIX#3/FIX#4/FIX#6 有根本性缺陷：checkpoint 恢复带脏数据、inbox path hardcode race condition 依然存在、polling 事件驱动没有 dead-letter 检测。

新增问题中阻塞性最大的两个：
1. inbox jsonl 的 append-vs-rewrite 不一致 + 无锁 race（主 session 和 subagent 并发读写）
2. step 3 无质量门控，所有 design proposal 透传给用户，AskUserQuestion 被设计成阻塞点反而变成了用户侧的垃圾信息入口

**结论：not ready to ship。** 需要至少一次完整重写 inbox 文件操作语义（统一 append-only + 只在 main session 做 final dedup），以及为 step 3 加上 extract-only 后的 judge 把关。```

## iter 3

### artifact (iter 3)

```markdown
# self-verify-loop plan (iter 3, append-only partition + dead-letter)

- task: design a for-loop (ask roles → auto-fix → distill designs → main-only AskUserQuestion); inner loop in opus subagent; step 3 never blocks; user complaints inbox; claudefast-as-judge for step 1 / step 2 / ship verdict, **extract-only (无 judge)** for step 3.
- project: demo_insights_share
- N: 5

## 设计原则 (iter 3 新增 / 修订)

**R1 — Single-writer per file**: 每个 inbox jsonl 只有一个 owner process 写入。race 消除。
**R2 — Append-only inbox**: 所有 jsonl 只 append, 从不 rewrite。状态变更 = 追加一条新 record。final status = 同 key 的最新 record。
**R3 — "EXCEPT 3" 严守**: step 3 的 proposals 不经过任何 ship/revise/quality LLM judge。垃圾是 user 侧 Defer/Deny 的职责。LLM 只做 extract (结构提取), 不做判决。
**R4 — Dead-letter by observation**: main session 不追 subagent 进程状态; 用 "summary.json 是否写成" + "最新 checkpoint 时间 > threshold" 推断 crash。
**R5 — Bounded token per iter**: role 并行上限 = 2; 超额顺序执行。

## inbox 目录布局 (iter 3 重构)

```text
docs/user_complaints_inbox/
├── proposals_appended.jsonl    # subagent 单写: {proposal_id, iter, design, source_roles, ts_appended}
├── proposals_resolved.jsonl    # main 单写: {proposal_id, status∈{approved,denied,deferred}, defer_count, ts_resolved}
├── role_verdicts.jsonl         # subagent 单写: {iter, role, comment, ts}
├── autofix_log.jsonl           # subagent 单写: {iter, diff, ts}
├── checkpoints/                # subagent 单写 (atomic rename)
│   └── iter_<N>.json           # 只保留 .json; .tmp 孤儿忽略
├── summary.json                # subagent 单写, 仅 normal exit; main 判断 crash 靠此文件不存在
└── summary.md                  # 同上, 人读版
```

**current_status(proposal_id)**:
```
find latest record in proposals_resolved.jsonl with matching proposal_id
  → if exists: that status + defer_count
  → else: "pending"
```
**pending pool** = `proposals_appended` 的 proposal_id - `proposals_resolved` 里状态 ∈ {approved, denied} 的 id - defer_count ≥ DEFER_AFTER_K 的 id。

dedup 窗口消除: proposals_appended 本就允许同 pid 重复 (append-only), main side derive_pending() 自动聚合成一份。

## pseudo for-loop

```text
# === inputs (typed, 显式) ===
task              : str
artifact_0        : str
roles             : list = [pm, oncall, tech_lead, newbie, curator, validator]
role_prompt_dir   : path = .claude/roleplan_agents/
N                 : int  = 5
inbox_dir         : path = docs/user_complaints_inbox/
MAX_PENDING       : int  = 20            # 显示给 user 的上限
DEFER_AFTER_K     : int  = 3             # 同一 pid 被 Defer K 次后自动 skip (视为 denied)
ROLE_CONCURRENCY  : int  = 2             # R5
DEAD_LETTER_SEC   : int  = 1800          # 最新 checkpoint 超过 30 min 视为 dead-letter

# === main session (不阻塞) ===
task_handle = spawn_subagent(opus, background=true, ...)

main_inbox_drain_trigger()  # 由下列任一触发
  - task_handle complete event
  - user /inbox-drain
  - periodic 10 min tick
  - dead-letter detector (summary.json 不在 + 最新 checkpoint 停止 > DEAD_LETTER_SEC)

def main_inbox_drain():
    pending_ids = derive_pending(inbox_dir)        # 聚合 appended - resolved 得到 pid 列表
    pending     = [load_proposal(pid) for pid in pending_ids][:MAX_PENDING]
    if count_total_pending > MAX_PENDING:
        report_to_user(f"inbox has {count_total_pending} pending, showing top {MAX_PENDING}")
    if not pending and crash_detected():
        report_to_user("subagent appears dead; no pending items to approve")
        return

    batch = pending[:4]  # AskUserQuestion 最多 4/batch
    for p in batch:
        ans = AskUserQuestion(
            question = f"{p.source_roles} 建议: {p.design.title}?",
            preview  = p.design.rationale + "\nimpact: " + p.design.impact,
            options  = [Approve, Deny, Defer]
        )
        new_defer = (get_latest_defer_count(p.proposal_id) + 1) if ans=="Defer" else 0
        status = "denied" if (ans=="Defer" and new_defer >= DEFER_AFTER_K) else ans.lower()
        append_jsonl(proposals_resolved.jsonl, {
            proposal_id: p.proposal_id, status, defer_count: new_defer, ts_resolved: now
        })
    # 剩余 pending 留给下次触发; inbox never blocks subagent

# === inner_loop (opus subagent 内部) ===
def inner_loop(task, artifact_0, N, inbox_dir):
    artifact_i = artifact_0
    prior_ship_verdict = None
    start_iter = 1

    # R4 resume: 只认 .json (忽略 .tmp 孤儿)
    ckpts = [f for f in glob(inbox_dir+"/checkpoints/iter_*.json")
             if not f.endswith(".tmp")]
    if ckpts:
        latest = max(ckpts, key=parse_iter)
        try:
            ck = json.load(latest)
            artifact_i = ck.artifact_next
            prior_ship_verdict = ck.ship_verdict_prev
            start_iter = ck.iter + 1
            # 脏 jsonl 不回滚: 下游消费者用 pid/timestamp 去重 (proposals) 或按 iter 筛选最新 (role_verdicts)
        except: pass  # 损坏 ckpt 忽略, 从头跑

    verdict_tag = "maxed"
    for i in start_iter..N:
        # step 1 — roles (并发上限 ROLE_CONCURRENCY)
        role_comments = parallel_map(
            roles, max_concurrency=ROLE_CONCURRENCY,
            fn=lambda role: claudefast_p(
                read(role_prompt_dir+"prompt_"+role+".md")
                + "\n---\n## review iter "+i+"\n\n"+artifact_i
            )
        )
        for role, c in role_comments.items():
            append_jsonl(role_verdicts.jsonl, {iter:i, role, comment:c, ts:now})

        # step 2 — auto-fix
        fix_verdict = claudefast_p("""<原样>""")
        if fix_verdict startswith "FIXED:":
            artifact_next = parse(fix_verdict)
            append_jsonl(autofix_log.jsonl, {iter:i, diff, ts:now})
        else:
            artifact_next = artifact_i

        # step 3 — extract-only, NO judge, NO ask
        proposals_raw = claudefast_p("""
            extract-only: 从 role_comments 抽 new design → JSON [{title, rationale, affected_roles, impact}].
            这是提取, 不是评审. 不打分, 不筛选, 不判断质量.
        """)
        for d in proposals_raw:
            pid = sha256(task+"|"+d.title+"|"+d.rationale)[:16]
            append_jsonl(proposals_appended.jsonl, {
                proposal_id: pid, iter:i, design:d,
                source_roles: d.affected_roles, ts_appended: now
            })
            # dedup 不在写时做 (allow重复append), main side derive_pending 聚合

        # ship verdict (step 1+2 base, 显式忽略 step 3)
        ship_verdict = claudefast_p("""
            task, artifact_next, role_comments, autofix_applied.
            忽略 "new design proposal" (已入 inbox, 是 user 侧决策, 与 ship 无关).
            基于 role 点评 + autofix, 本 artifact 可出货? 自由作答.
        """)

        # R4 checkpoint (atomic rename)
        write_json_atomic(inbox_dir/f"checkpoints/iter_{i}.json", {
            iter:i, artifact_next, ship_verdict_prev: ship_verdict, ts:now
        })

        if ship_verdict reads-as "ship/ready/no blockers":
            verdict_tag = "shipped"; artifact_final = artifact_next; break
        if ship_verdict == prior_ship_verdict:
            verdict_tag = ("converged" if previously_shipped else "stuck")
            artifact_final = artifact_next; break
        prior_ship_verdict = ship_verdict
        artifact_i = artifact_next
    else:
        artifact_final = artifact_i

    # normal exit 才写 summary
    write_json_atomic(inbox_dir/summary.json, {
        verdict_tag, iters_used: i, artifact_final_path,
        pending_proposals_hint: derive_pending_count(inbox_dir),
        autofix_count: count_appended(autofix_log.jsonl),
        exit_reason: "normal", ts: now
    })
    write(inbox_dir/summary.md, pretty_print(summary.json))
    return                           # return 丢失无关紧要, 靠 summary.json 通信

# === 辅助: atomic write ===
def write_json_atomic(path, obj):
    tmp = path + ".tmp"
    open(tmp, "w").write(json.dumps(obj))
    os.rename(tmp, path)     # POSIX atomic on same fs

# === main 侧的 crash 检测 ===
def crash_detected():
    if exists(inbox_dir/summary.json):
        return False           # normal exit
    ckpts = glob(inbox_dir/"checkpoints/iter_*.json")
    if not ckpts: return False  # 可能还没开始
    latest_mtime = max(os.stat(f).st_mtime for f in ckpts)
    return (now - latest_mtime) > DEAD_LETTER_SEC
```

## 覆盖 iter 2 verdict 的所有新问题

| iter-2 发现 | iter-3 对策 |
|-------------|-------------|
| MAX_PENDING 饿死 starved items | batch=4 rolling + 无限触发 (event/user/periodic); 且 DEFER_AFTER_K 到达后自动 denied, 不再占名额 |
| checkpoint resume 带脏 jsonl | 下游消费者用 pid/timestamp 聚合 (proposals) 或按 iter 取最新 (role_verdicts); 脏数据被自然覆盖, 不需清理 |
| .tmp 孤儿 | glob 过滤 .tmp; write_json_atomic 用 rename, crash 时 tmp 留着, 下次 resume 时被 glob 跳过 |
| jsonl rewrite race | **R1 R2**: 所有文件 append-only + single-writer, 无并发写 |
| defer escape hatch | summary 里出 `pending_proposals_hint`, 下次 main 触发仍可 drain; DEFER_AFTER_K 自动降级到 denied |
| step 3 无 judge (spam 入口) | **明确设计决策**: user 要求 "EXCEPT 3", spam 过滤是 user 侧 Defer/Deny 职责; MAX_PENDING + DEFER_AFTER_K 防溢出 |
| background return 丢失 | 用 summary.json 通信, 不依赖 return value |
| dedup race | append-only 允许重复 pid, main 侧 derive_pending() 聚合 |
| role 并行 token 无预算 | ROLE_CONCURRENCY=2 |
| dead-letter 检测缺失 | `crash_detected()` 基于 summary.json + 最新 checkpoint mtime |

## 仍然开放 (裁判可再挑)

- 如果 subagent 在 step 3 extract 途中 crash, proposals_appended 里有 partial 批次 — 可接受 (append-only, 下次 resume 再跑 step 3 会重新生成; pid 去重保证 user 不看到重复)
- ROLE_CONCURRENCY=2 是 magic number, 不会根据 token budget 自适应 — 留 v4
- checkpoints/ 目录无自动清理, N=5 最多 5 个 json 文件, 可接受
```

### judge prompt (iter 3) — abbreviated

```text
You are an open-ended design reviewer.

TASK (verbatim user request):
design a for loop to 1. ask roles for comments 2. auto-fix the bugs if have 3. draft new designs from role comments and ask users to approve or deny with ask user question tool. use claudefast -p to offer LLM-as-judge EXCEPT 3 please. we also design this loop in opus subagents and in main session only report 3. 3 should NOT work as a stuck point and should by default ignore it and add a "user complaints inbox" to store them and report to main session.

PRIOR VERDICT iter 1: 6 concrete issues (AskUserQuestion timeout, dedup, checkpoint, concrete paths, N param, polling cadence).
PRIOR VERDICT iter 2: 6 FIXes partially effective but new problems — inbox starve, partial-iter dirty jsonl, .tmp orphans, rewrite-vs-append race, defer escape hatch, step 3 spam ingress, bg subagent return lost, dedup race, unbounded role tokens, dead-letter detection missing.

CURRENT ARTIFACT (iter 3):
---BEGIN_ARTIFACT---
# self-verify-loop plan (iter 3, append-only partition + dead-letter)

- task: design a for-loop (ask roles → auto-fix → distill designs → main-only AskUserQuestion); inner loop in opus subagent; step 3 never blocks; user complaints inbox; claudefast-as-judge for step 1 / step 2 / ship verdict, **extract-only (无 judge)** for step 3.
- project: demo_insights_share
- N: 5

## 设计原则 (iter 3 新增 / 修订)

**R1 — Single-writer per file**: 每个 inbox jsonl 只有一个 owner process 写入。race 消除。
**R2 — Append-only inbox**: 所有 jsonl 只 append, 从不 rewrite。状态变更 = 追加一条新 record。final status = 同 key 的最新 record。
**R3 — "EXCEPT 3" 严守**: step 3 的 proposals 不经过任何 ship/revise/quality LLM judge。垃圾是 user 侧 Defer/Deny 的职责。LLM 只做 extract (结构提取), 不做判决。
**R4 — Dead-letter by observation**: main session 不追 subagent 进程状态; 用 "summary.json 是否写成" + "最新 checkpoint 时间 > threshold" 推断 crash。
**R5 — Bounded token per iter**: role 并行上限 = 2; 超额顺序执行。

## inbox 目录布局 (iter 3 重构)

```text
docs/user_complaints_inbox/
├── proposals_appended.jsonl    # subagent 单写: {proposal_id, iter, design, source_roles, ts_appended}
├── proposals_resolved.jsonl    # main 单写: {proposal_id, status∈{approved,denied,deferred}, defer_count, ts_resolved}
├── role_verdicts.jsonl         # subagent 单写: {iter, role, comment, ts}
├── autofix_log.jsonl           # subagent 单写: {iter, diff, ts}
├── checkpoints/                # subagent 单写 (atomic rename)
│   └── iter_<N>.json           # 只保留 .json; .tmp 孤儿忽略
├── summary.json                # subagent 单写, 仅 normal exit; main 判断 crash 靠此文件不存在
└── summary.md                  # 同上, 人读版
```

**current_status(proposal_id)**:
```
...
(full artifact embedded above; full prompt preserved in /tmp/svl_iter3_prompt_final.txt at run time)
```

### judge verdict (iter 3)

```text
## iter 3 review — not ship-ready

### .tmp orphans, dedup race, dead-letter detection, inbox starve — resolved

glob 过滤 .tmp + atomic rename 确实消除孤儿。append-only + derive_pending() 聚合同 pid 确实消除 dedup race。crash_detected() 基于 summary.json + checkpoint mtime > threshold 确实覆盖 dead-letter。batch=4 rolling + DEFER_AFTER_K 自动降级确实消除 starved items。

---

### 3 unresolved issues

**1. R1 "single-writer per file" is violated by role parallelism**

`parallel_map(roles, max_concurrency=2, fn=...)` — 6 个 role 并发执行，全部写同一个 `role_verdicts.jsonl`。parallel_map 不是原子的：如果两个 role callback 同时结束并同时 `append_jsonl(role_verdicts.jsonl, ...)`，race 仍然存在。

R1 的本意是"一个文件只被一个 owner process 写入"，但这里 role 是 6 个独立进程（subagent 内部的 worker），共享同一个文件描述符或文件路径。**这不是 single-writer，这是 multi-writer。**

Fix: 要么 `ROLE_CONCURRENCY=1` 强制串行（消除 race 但失去并发），要么每个 role 写自己专属文件 `role_verdicts/{role}.jsonl`，最后 main side merge。

**2. approve → defer 语义覆盖问题**

`current_status(pid)` 取 latest record。如果 user 先 approve，后来又 Defer K 次，latest record 是 defer — proposal 被降级为 denied。这违反"已批准提案不能被降级"的直觉预期。

append-only 的本意是"不 rewrite，只追加"，但没有 `effective_status` 字段来表达"最终有效状态"。latest ≠ effective，尤其是跨 batch 的场景。

Fix: 添加 `effective_status` 字段，approve 只升不降；或者把 approve/deny/defer 分离为 `decisions/{pid}.json`（main 单写）而不是堆在同一个 jsonl 里。

**3. "EXCEPT 3" 过度放松，质量门缺失**

设计把 step 3 定义为"extract-only, no judge"，但 extract 操作本身不是无状态的 — 如果 subagent 在 extract 时把"用户抱怨"（complaints）当成"新设计方案"塞进 proposals_appended，或者 prompt injection 让 extract 跑偏，没有任何 LLM 门拦截。

真正的问题是：**inbox 里的 proposal 质量完全依赖 subagent 的 extract prompt，而 prompt 没有防御机制。**

Step 3 不能是纯黑洞。至少需要：schema validation（proposal 必须有 title/rationale/impact 字段）、impact 评分门槛（impact == "low" 的自动 skip）、或一个极简 sanity check LLM（不是 ship verdict，就是"这是不是一个有效设计提案"的二元判断）。

---

### Remaining open items (acceptable for v3)

- `.tmp orphan ignore` — resume 时 glob 跳过 .tmp，脏数据不清理但也不影响正确性
- `ROLE_CONCURRENCY=2` magic number — 接受，不自适应是 v4 的 todo
- `DEFER_AFTER_K` 到达后自动 denied — 行为清晰
- crash during step 3 extract → partial batch in proposals_appended — 接受（pid 去重保证 user 不看到重复，但 dirty proposal 可能仍然可见直到 denied）

---

### Verdict

Not ready to ship. Revisions needed:

1. **Role 输出到独立文件**（`role_verdicts/{role}.jsonl`）或强制 `ROLE_CONCURRENCY=1`。R1 invariant 否则不成立。
2. **添加 `effective_status` 语义**或分离 decisions 到 main 单写的 `decisions/{pid}.json`，防止 approve 被后续 defer 覆盖。
3. **Step 3 至少加 schema validation** — 即使不做 LLM gate，proposal 入 inbox 前要过 schema 检查（title/rationale/impact 非空，impact 不是 "minimal" 等明显垃圾）。

这三个修复可以在 iter 4 里落地，不需要重写整个设计。```

## iter 4

### artifact (iter 4)

```markdown
# self-verify-loop plan (iter 4, per-role files + terminal decisions + schema gate)

- task: design a for-loop (ask roles → auto-fix → distill designs → main-only AskUserQuestion); inner loop in opus subagent; step 3 never blocks; user complaints inbox; claudefast LLM-judge for step 1 / step 2 / ship verdict; step 3 = extract-only + schema validation (no LLM judge on content).
- project: demo_insights_share
- N: 5

## 设计原则 (iter 4 变更)

**R1 single-writer**: 每个文件路径只被一个 writer 进程写入。并发 roles 现在各写自己的文件; decisions per-pid 各写自己的文件。
**R2 append-only for logs, single-file-per-key for decisions**:
   - logs (role_verdicts, autofix_log, proposals_appended) = append-only jsonl
   - decisions = `decisions/{pid}.json` 单文件单写
**R3 "EXCEPT 3" 严守 (LLM judge)**, 但 step 3 加**结构性 schema gate** (非 LLM)
**R4 dead-letter 检测** (同 iter 3)
**R5 bounded concurrency** ROLE_CONCURRENCY=2 (每 role 独立文件, 无需串行)

## 决策语义 (iter 4 新增)

一个 proposal 的**生命周期状态机**:

```
    appended ──┐
               ↓
         [pending] ←─┐  (init state, 无 decision file)
            │ Defer  │
            ↓        │
         [deferred N=1..K-1] ──┐
            │ Defer            │
            ↓                  │
         [denied auto K]       │
                               │
    [pending/deferred] ─ Approve ─→ [approved]    # terminal, 不可回退
    [pending/deferred] ─ Deny ────→ [denied]      # terminal, 不可回退
```

**terminal 规则**: approved / denied 是终止态。一旦 decisions/{pid}.json 写了 terminal 状态, 后续 AskUserQuestion 不再对该 pid 出题。

**effective_status(pid)**:
```
if exists decisions/{pid}.json:
    return loaded.status         # 单源真相, 无 "取最新 jsonl 行" 歧义
else:
    return "pending"
```

## inbox 目录布局 (iter 4 重构)

```text
docs/user_complaints_inbox/
├── role_verdicts/              # R1: 每 role 独立文件
│   ├── pm.jsonl                # subagent(role=pm) 单写
│   ├── oncall.jsonl
│   ├── tech_lead.jsonl
│   ├── newbie.jsonl
│   ├── curator.jsonl
│   └── validator.jsonl
├── autofix_log.jsonl           # subagent 单写
├── proposals_appended.jsonl    # subagent 单写 (dedup 在 main 侧聚合)
├── decisions/                  # main 单写 per pid
│   └── <pid>.json              # {proposal_id, status, defer_count, ts_resolved, history: [...]}
├── checkpoints/                # subagent 单写, atomic rename
│   └── iter_<N>.json
├── summary.json                # subagent 单写 (normal exit 标记)
└── summary.md                  # subagent 单写 (人读)
```

## pseudo for-loop (iter 4)

```text
# === inputs ===
task                 : str
artifact_0           : str
roles                : list = [pm, oncall, tech_lead, newbie, curator, validator]
role_prompt_dir      : path = .claude/roleplan_agents/
N                    : int  = 5
inbox_dir            : path = docs/user_complaints_inbox/
MAX_PENDING          : int  = 20
DEFER_AFTER_K        : int  = 3
ROLE_CONCURRENCY     : int  = 2
DEAD_LETTER_SEC      : int  = 1800

# === proposal schema gate (R3, 非 LLM) ===
REQUIRED_FIELDS   = ["title", "rationale", "impact", "affected_roles"]
INVALID_IMPACT    = ["", None, "minimal", "none", "n/a", "tbd"]

def schema_valid(d):
    if not all(f in d and d[f] for f in REQUIRED_FIELDS): return False
    if d["impact"].lower().strip() in INVALID_IMPACT: return False
    if len(d["title"]) < 5 or len(d["rationale"]) < 20: return False
    return True

# === main session ===
task_handle = spawn_subagent(opus, background=true, input=...)

# 触发 (不变, 同 iter 3)
def main_inbox_drain():
    pending_ids = derive_pending(inbox_dir)
    # pending = appended 中 effective_status(pid)=="pending" 或 "deferred"(未达K)
    pending = []
    for pid in pending_ids:
        eff = effective_status(pid)
        if eff == "pending" or (eff == "deferred" and get_defer_count(pid) < DEFER_AFTER_K):
            pending.append(load_proposal(pid))
    if len(pending) > MAX_PENDING:
        report_to_user(f"inbox: {len(pending)} pending, showing top {MAX_PENDING}")
        pending = pending[-MAX_PENDING:]
    if not pending and crash_detected(): report_to_user("subagent dead, no pending"); return

    for p in pending[:4]:     # AskUserQuestion ≤ 4/batch
        ans = AskUserQuestion(question, preview, [Approve, Deny, Defer])
        # 写 decisions/{pid}.json (单写)
        prev = load_decision(p.proposal_id) or {defer_count:0, history:[]}
        new_defer = (prev.defer_count + 1) if ans=="Defer" else prev.defer_count
        status = (
            "approved" if ans=="Approve" else
            "denied"   if ans=="Deny"    else
            "denied"   if new_defer >= DEFER_AFTER_K else
            "deferred"
        )
        # terminal 检查: 若 prev.status ∈ {approved, denied} 则 skip (不回退)
        if prev.get("status") in ("approved","denied"):
            continue  # 理论不可达 (pending 筛选已过滤), 防御
        write_json_atomic(decisions_dir/f"{p.proposal_id}.json", {
            proposal_id: p.proposal_id,
            status,
            defer_count: new_defer,
            ts_resolved: now,
            history: prev.history + [{ans, ts:now}]
        })

# === inner_loop (subagent) ===
def inner_loop(task, artifact_0, N, inbox_dir):
    artifact_i = artifact_0
    prior_ship_verdict = None
    start_iter = 1

    ckpts = [f for f in glob(inbox_dir+"/checkpoints/iter_*.json") if not f.endswith(".tmp")]
    if ckpts:
        try:
            ck = json.load(max(ckpts, key=parse_iter))
            artifact_i = ck.artifact_next
            prior_ship_verdict = ck.ship_verdict_prev
            start_iter = ck.iter + 1
        except: pass

    verdict_tag = "maxed"
    for i in start_iter..N:
        # step 1: roles 并发 (每 role 写自己的文件, R1 OK)
        def ask_role(role):
            c = claudefast_p(read(role_prompt_dir+"prompt_"+role+".md")
                             + "\n---\n## review iter "+i+"\n\n"+artifact_i)
            append_jsonl(inbox_dir/f"role_verdicts/{role}.jsonl", {iter:i, role, comment:c, ts:now})
            return c
        role_comments = parallel_map(roles, max_concurrency=ROLE_CONCURRENCY, fn=ask_role)

        # step 2: auto-fix (同 iter 3)
        fix_verdict = claudefast_p("...")
        if fix_verdict startswith "FIXED:":
            artifact_next = parse(fix_verdict)
            append_jsonl(autofix_log.jsonl, {iter:i, diff, ts:now})
        else:
            artifact_next = artifact_i

        # step 3: extract-only + schema gate (无 LLM judge)
        proposals_raw = claudefast_p("""
            extract-only: 从 role_comments 抽 new design → JSON list.
            每条必须有 {title, rationale, impact, affected_roles}.
            impact 必须是 {low|medium|high} 之一 (不接受 minimal/none/n/a).
            这是提取, 不是评审.
        """)
        for d in proposals_raw:
            if not schema_valid(d):
                continue           # schema-gate 淘汰垃圾, 非 LLM 判决
            pid = sha256(task+"|"+d.title+"|"+d.rationale)[:16]
            # 重复 pid 允许 append (下游 main derive_pending 聚合)
            append_jsonl(proposals_appended.jsonl, {
                proposal_id: pid, iter:i, design:d,
                source_roles: d.affected_roles, ts_appended: now
            })

        # ship verdict (同 iter 3)
        ship_verdict = claudefast_p("... 忽略 new design proposals ... 基于 role+autofix 可出货?")
        write_json_atomic(checkpoints_dir/f"iter_{i}.json", {
            iter:i, artifact_next, ship_verdict_prev: ship_verdict, ts:now
        })

        if ship_verdict reads-as "ship/ready/no blockers":
            verdict_tag = "shipped"; artifact_final = artifact_next; break
        if ship_verdict == prior_ship_verdict:
            verdict_tag = ("converged" if previously_shipped else "stuck")
            artifact_final = artifact_next; break
        prior_ship_verdict = ship_verdict
        artifact_i = artifact_next
    else:
        artifact_final = artifact_i

    write_json_atomic(summary.json, {
        verdict_tag, iters_used:i, artifact_final_path,
        pending_hint: derive_pending_count(inbox_dir),
        autofix_count: count_lines(autofix_log.jsonl),
        exit_reason: "normal", ts: now
    })
```

## 覆盖 iter 3 verdict

| iter-3 issue | iter-4 对策 |
|---|---|
| role 并发全写同一 jsonl (R1 违反) | **每 role 独立文件** `role_verdicts/{role}.jsonl`, 每 role 一个 writer, 真正 single-writer |
| effective_status 取 latest 导致 approve 被 defer 覆盖 | **terminal decisions/{pid}.json 单文件单写**; approve/deny 进 terminal 态后 pending 筛选自动 skip; history 字段保留审计 |
| step 3 无质量门 (EXCEPT 3 过度放松) | **schema gate** (非 LLM): 校验 title/rationale/impact/affected_roles 非空, impact ∈ {low/med/high}, title ≥ 5 char, rationale ≥ 20 char |

`schema gate` 不是 ship/revise 判决, 不是打分, 不是语义 LLM judge — 仅结构校验。符合 user 的 "LLM-as-judge EXCEPT 3" (LLM 不做 3 的质量判决, 但 schema 这种结构性 filter 是程序逻辑, 不在该约束范围内)。

## 仍然开放 (不影响 ship)

- ROLE_CONCURRENCY=2 magic number (v5 自适应 token budget)
- checkpoints/ 目录无自动清理 (N=5, 最多 5 个 json)
- decisions/{pid}.json 在极端情况下 (几万 proposals) 目录膨胀 — v5 可考虑归档旧 approved 到 decisions.archive.jsonl
```

### judge prompt (iter 4) — abbreviated

```text
You are an open-ended design reviewer.

TASK (verbatim user request):
design a for loop to 1. ask roles for comments 2. auto-fix the bugs if have 3. draft new designs from role comments and ask users to approve or deny with ask user question tool. use claudefast -p to offer LLM-as-judge EXCEPT 3 please. we also design this loop in opus subagents and in main session only report 3. 3 should NOT work as a stuck point and should by default ignore it and add a "user complaints inbox" to store them and report to main session.

PRIOR VERDICTS trajectory:
- iter 1: 6 concrete issues (AskUserQuestion timeout, dedup, checkpoint, concrete paths, N, polling)
- iter 2: earlier 6 partially fixed + 10 new (inbox starve, dirty jsonl, .tmp orphans, race, escape hatch, spam, bg return, dedup race, role tokens, dead-letter)
- iter 3: 7/10 iter-2 issues resolved + 3 unresolved (role parallel R1 violation, approve→defer override, step 3 no quality gate)

CURRENT ARTIFACT (iter 4):
---BEGIN_ARTIFACT---
# self-verify-loop plan (iter 4, per-role files + terminal decisions + schema gate)

- task: design a for-loop (ask roles → auto-fix → distill designs → main-only AskUserQuestion); inner loop in opus subagent; step 3 never blocks; user complaints inbox; claudefast LLM-judge for step 1 / step 2 / ship verdict; step 3 = extract-only + schema validation (no LLM judge on content).
- project: demo_insights_share
- N: 5

## 设计原则 (iter 4 变更)

**R1 single-writer**: 每个文件路径只被一个 writer 进程写入。并发 roles 现在各写自己的文件; decisions per-pid 各写自己的文件。
**R2 append-only for logs, single-file-per-key for decisions**:
   - logs (role_verdicts, autofix_log, proposals_appended) = append-only jsonl
   - decisions = `decisions/{pid}.json` 单文件单写
**R3 "EXCEPT 3" 严守 (LLM judge)**, 但 step 3 加**结构性 schema gate** (非 LLM)
**R4 dead-letter 检测** (同 iter 3)
**R5 bounded concurrency** ROLE_CONCURRENCY=2 (每 role 独立文件, 无需串行)

## 决策语义 (iter 4 新增)

一个 proposal 的**生命周期状态机**:

```
    appended ──┐
               ↓
         [pending] ←─┐  (init state, 无 decision file)
            │ Defer  │
            ↓        │
         [deferred N=1..K-1] ──┐
            │ Defer            │
...
(full artifact embedded above; full prompt preserved in /tmp/svl_iter4_prompt_final.txt at run time)
```

### judge verdict (iter 4)

```text
## iter 4 审查结论

**(a) per-role files → R1 合规**

`role_verdicts/{pm,jsonl, oncall,jsonl, ...}` 每 role 独立文件，无共享写入路径。R1 真正解决。✓

**(b) decisions/{pid}.json + terminal 检查 → approve→defer 覆盖修复**

- `effective_status(pid)` 读 `decisions/{pid}.json` 单源，无 "取 latest jsonl 行" 歧义。✓
- main_inbox_drain pending 筛选：只取 `effective_status == "pending" || ("deferred" && defer_count < K)`，approved/denied 自动排除。✓
- 写前防御 `if prev.get("status") in ("approved","denied"): continue`：即使 filter 漏过也不回退。✓
- history 字段提供审计链。✓

approve→defer 覆盖 **已真正修复**。

**(c) schema gate → step 3 spam + EXCEPT 3 合规**

schema gate 是程序逻辑（结构字段校验），不是 LLM 语义判决。"EXCEPT 3" 的约束对象是 **LLM-as-judge**，schema validation 不在该约束范围内。

spam 过滤效果：空字符串 / None / "minimal" / "none" / "n/a" impact → reject；title < 5 char / rationale < 20 char → reject。这对防止垃圾 proposal 进入 inbox 有实质效果。

**两项 claim 均成立，无 overreach。**

---

## 剩余开放项（均非 blocker）

| 项 | 性质 | 备注 |
|---|---|---|
| `claudefast_p` 调用无 JSON parse 错误处理 | 潜在 dirty jsonl | v4 可加 try/except json.loads，parse 失败 append error log 而非 crash |
| `proposals_appended.jsonl` append 时无文件锁 | 理论 race | subagent 内串行，main 单进程，无并发写同一文件风险；v5 可加 flock |
| checkpoints/ 无 .tmp 清理 | 轻微磁盘浪费 | N=5，5 个文件，上限极小，可忽略 |
| decisions/ 目录无归档 | 长期膨胀 | v5 归档已 approved 到 archive |
| DEFER_AFTER_K=3 magic number | 已知待调 | v5 自适应 |

---

## verdict

**ship-ready。** iter 4 解决了 iter 3 全部 3 个未决 issue（R1、approve→defer、step 3 spam），无新 blocker引入。```

## final artifact

见 iter 4 artifact block 上方.

## final judge verdict

```text
## iter 4 审查结论

**(a) per-role files → R1 合规**

`role_verdicts/{pm,jsonl, oncall,jsonl, ...}` 每 role 独立文件，无共享写入路径。R1 真正解决。✓

**(b) decisions/{pid}.json + terminal 检查 → approve→defer 覆盖修复**

- `effective_status(pid)` 读 `decisions/{pid}.json` 单源，无 "取 latest jsonl 行" 歧义。✓
- main_inbox_drain pending 筛选：只取 `effective_status == "pending" || ("deferred" && defer_count < K)`，approved/denied 自动排除。✓
- 写前防御 `if prev.get("status") in ("approved","denied"): continue`：即使 filter 漏过也不回退。✓
- history 字段提供审计链。✓

approve→defer 覆盖 **已真正修复**。

**(c) schema gate → step 3 spam + EXCEPT 3 合规**

schema gate 是程序逻辑（结构字段校验），不是 LLM 语义判决。"EXCEPT 3" 的约束对象是 **LLM-as-judge**，schema validation 不在该约束范围内。

spam 过滤效果：空字符串 / None / "minimal" / "none" / "n/a" impact → reject；title < 5 char / rationale < 20 char → reject。这对防止垃圾 proposal 进入 inbox 有实质效果。

**两项 claim 均成立，无 overreach。**

---

## 剩余开放项（均非 blocker）

| 项 | 性质 | 备注 |
|---|---|---|
| `claudefast_p` 调用无 JSON parse 错误处理 | 潜在 dirty jsonl | v4 可加 try/except json.loads，parse 失败 append error log 而非 crash |
| `proposals_appended.jsonl` append 时无文件锁 | 理论 race | subagent 内串行，main 单进程，无并发写同一文件风险；v5 可加 flock |
| checkpoints/ 无 .tmp 清理 | 轻微磁盘浪费 | N=5，5 个文件，上限极小，可忽略 |
| decisions/ 目录无归档 | 长期膨胀 | v5 归档已 approved 到 archive |
| DEFER_AFTER_K=3 magic number | 已知待调 | v5 自适应 |

---

## verdict

**ship-ready。** iter 4 解决了 iter 3 全部 3 个未决 issue（R1、approve→defer、step 3 spam），无新 blocker引入。```

## loop summary

- iter 1: 6 issues → revise
- iter 2: 6 partial + 10 new → revise
- iter 3: 7/10 resolved + 3 new → revise
- iter 4: all 3 resolved, no new blockers → **ship-ready**

终止理由: iter 4 ship_verdict 自由文本明确写 "ship-ready. iter 4 解决了 iter 3 全部 3 个未决 issue, 无新 blocker引入" → verdict_tag = shipped.
