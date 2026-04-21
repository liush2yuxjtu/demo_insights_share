---
name: self-verify-loop
description: 项目级自验收编排 skill。当用户调 `/self-verify-loop` 或在 CLAUDE.md / start.demo.sh / proposal 改动后需要统一跑 agent-judge + tmux 实机双验收时使用。内部 for-loop 伪码由 docs/rules/self-verify-loop.md 定义。
---

# self-verify-loop (project-level)

## 职责

单入口编排两条既有验收 rule：

- **tier_meta**：`docs/rules/meta-self-verify.md` 的 claudefast 双探针 for-loop
- **tier_demo**：`docs/rules/start-demo-verify.md` 的 tmux 实机 start.demo.sh 观察

不发明新逻辑，只做调度。

## 入口

```
.claude/commands/self-verify-loop.md   # slash 命令
.claude/skills/self-verify-loop/SKILL.md  # 本文件
.claude/skills/self-verify-loop/run.sh    # bash 实现（首版 stub，后续补）
```

## For-Loop 伪码（权威）

### 顶层

```python
def main(args):
    scope   = detect_scope(args)         # git diff HEAD → {meta, demo} 子集
    tiers   = build_tiers(scope)
    cfg     = parse_flags(args)
    results = []

    for tier in tiers:
        r = run_tier(tier, cfg)
        log_terminal(tier, r)
        results.append(r)
        if r.verdict == "FAIL" and not cfg.continue_on_fail:
            break

    overall = "PASS" if all(r.verdict == "PASS" for r in results) else "FAIL"
    write_terminal_line(overall)
    exit(0 if overall == "PASS" else 1)
```

### tier_meta（agent-judge 双探针）

```python
def run_tier_meta(cfg):
    rule_intent  = extract_rule_intent_from_diff("CLAUDE.md")
    probe_q      = build_probe_question(rule_intent)
    judge_prompt = build_judge_prompt(rule_intent)    # 强制 JSON schema

    prev_patch, stall = None, 0

    for iter in range(1, cfg.MAX_FAST + 1):
        probe  = shell(f'claudefast -p {q(probe_q)}')
        judge  = shell(f'claudefast -p {q(judge_prompt.replace("{probe_response}", probe))}')
        v      = parse_json_strict(judge)             # {verdict, reason, suggested_patch}
        log("fast", iter, v.verdict, v.reason)

        if v.verdict == "PASS":
            return Result("PASS", tier="meta", iter=iter, reason=v.reason)
        if v.verdict == "FAIL":
            break

        # REFINE
        if cfg.auto_patch and v.suggested_patch:
            apply_patch("CLAUDE.md", v.suggested_patch)
            atomic_commit(f"meta-verify iter={iter}: {v.reason}")

        if prev_patch and similar(prev_patch, v.suggested_patch):
            stall += 1
            if stall >= 2:
                log("fast", iter, "STALL", "force escalate reliable")
                break
        else:
            stall = 0
        prev_patch = v.suggested_patch

    if cfg.fast_only:
        return Result("FAIL", tier="meta", reason="fast-only did not PASS")

    rel = shell(f'claude -p {q(judge_prompt.replace("{probe_response}", probe))}')
    rv  = parse_json_strict(rel)
    log("reliable", 1, rv.verdict, rv.reason)
    return Result(rv.verdict, tier="meta", escalated=True, reason=rv.reason)
```

### tier_demo（tmux 实机观察）

```python
def run_tier_demo(cfg):
    name = read_file("~/.claude/live_terminal/CURRENT").strip()
    if not name:
        if cfg.no_auto_register:
            return Result("FAIL", tier="demo", reason="no live tmux session")
        shell("bash .claude/skills/register-session/register-session.sh demo_verify")
        name = read_file("~/.claude/live_terminal/CURRENT").strip()

    log_path = f"~/.claude/live_terminal/{name}.log"
    mark     = f"__verify_start_{now_iso()}__"

    shell(f'TMUX= tmux send-keys -t {name} {q("echo " + mark)} Enter')
    shell(f'TMUX= tmux send-keys -t {name} {q("bash start.demo.sh; echo __EXIT=$?")} Enter')

    start_offset = file_size(log_path)
    errors, exit_code = [], None
    deadline = now() + cfg.TIMEOUT_SEC

    for tick in range(cfg.TIMEOUT_SEC // cfg.POLL_SEC):
        sleep(cfg.POLL_SEC)
        chunk = read_from(log_path, offset=start_offset)
        start_offset += len(chunk)

        errors += scan(chunk, [
            r"ERROR", r"Traceback", r"can't find pane",
            r"sessions should be nested with care",
        ])

        m = match(chunk, r"__EXIT=(\d+)")
        if m:
            exit_code = int(m.group(1))
            break
        if now() > deadline:
            return Result("FAIL", tier="demo", reason=f"demo timeout >{cfg.TIMEOUT_SEC}s")

    if exit_code != 0:
        return Result("FAIL", tier="demo", reason=f"exit={exit_code}")
    if errors:
        return Result("FAIL", tier="demo", reason=f"errors: {errors[:3]}")
    return Result("PASS", tier="demo", reason="demo clean")
```

## 日志契约

`insights-share/validation/reports/self_verify_loop.log`：

```
[ISO8601] [tier=meta|demo] [kind=fast|reliable] [iter=N] [verdict] [reason]
...
--- terminal --- [tier=meta] [verdict=PASS] [reason=...]
--- terminal --- [tier=demo] [verdict=PASS] [reason=demo clean]
--- OVERALL --- [PASS] [2026-04-21T17:22:03+08:00]
```

## 默认配置

| 变量 | 默认 | 说明 |
|------|------|------|
| `MAX_FAST` | 5 | tier_meta fast loop 上限 |
| `TIMEOUT_SEC` | 300 | tier_demo 等待上限 |
| `POLL_SEC` | 2 | tier_demo 日志轮询间隔 |
| `auto_patch` | off | 首版人审；on 需显式传 `--auto-patch` |
| `fast_only` | off | - |
| `no_auto_register` | off | - |

## 不变量

- judge 输出必须合法 JSON；否则视为 FAIL（禁自由发挥）
- 循环必终止：`MAX_FAST` 硬顶 + reliable 单次 + `TIMEOUT_SEC` 硬顶
- stall 必升级：2 轮同 patch 跳 fast 入 reliable
- 所有 `tmux send-keys` 前加 `TMUX=`（遵循 `tmux-nested.md`）
- REFINE + `auto_patch` 分支立即原子 commit（遵循 `atomic-commits.md`）
- `--override` 必带 reason，写 terminal 行，退出码 3

## 与其它规则的关系

| 规则 | 角色 |
|------|------|
| docs/rules/meta-self-verify.md | tier_meta 被调用的执行器 |
| docs/rules/start-demo-verify.md | tier_demo 被调用的执行器 |
| docs/rules/start-demo-register-fallback.md | tier_demo 前置 auto-register 分支 |
| docs/rules/live-terminal.md | tier_demo 读日志契约 |
| docs/rules/tmux-nested.md | tier_demo 发命令约束 |
| docs/rules/atomic-commits.md | auto_patch 分支 commit 契约 |
| docs/rules/read-before-task.md | slash 命令执行前必读四文件 |

## 首版范围

- ✅ 规则文档、slash 入口、SKILL.md 落盘
- ⏳ `run.sh` 先留 stub，后续 PR 落地完整 bash 实现
- ⏳ JSON 校验用 `jq -e`，失败即 FAIL
- ⏳ apply_patch 选 `git apply` vs `sed -i` 方案，下个 PR 决
