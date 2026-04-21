# /self-verify-loop: 统一自验收入口

## 核心断言

`/self-verify-loop` 是本项目**唯一**的自验收编排器。它不发明新规则，只把三条既有 rule 串成一个 for-loop pipeline：

- `meta-self-verify.md` → tier_meta 执行器（CLAUDE.md 改动验收）
- `start-demo-verify.md` → tier_demo 执行器（feature 改动验收）
- `live-terminal.md` + `start-demo-register-fallback.md` + `tmux-nested.md` → tier_demo 读日志契约

等价替换：以前手工跑两遍的「meta 双探针 + demo tmux 自检」，现在一条命令。

## 调用

```
/self-verify-loop                     # auto：用 git diff HEAD 决定跑哪些 tier
/self-verify-loop claude-md           # 只跑 tier_meta
/self-verify-loop feature             # 只跑 tier_demo
/self-verify-loop all                 # 两个都跑
/self-verify-loop --override "<原因>"  # 跳过，日志必须写原因
```

## Flag（与默认值）

| flag | 默认 | 作用 |
|------|------|------|
| `--max-fast N` | 5 | tier_meta fast loop 上限 |
| `--fast-only` | off | 禁 reliable 升级（省 token） |
| `--auto-patch` | **off** | REFINE 时是否自动 apply `suggested_patch` 并 commit；首版人审 |
| `--timeout-sec N` | 300 | tier_demo 日志等待上限 |
| `--dry-run` | off | 打印计划不执行 |
| `--override "<r>"` | - | 跳 gate，写 log reason，退 3 |
| `--no-auto-register` | off | tier_demo 缺 tmux session 不自动注册，直接 FAIL |

## 退出码

| code | 含义 |
|------|------|
| 0 | overall PASS |
| 1 | overall FAIL（用户必须看） |
| 2 | 环境缺件 / tmux 注册失败 |
| 3 | `--override` 人工跳过 |

## 顶层 for-loop 伪码

```python
def main(args):
    scope   = detect_scope(args)         # git diff HEAD → {meta, demo} 子集
    tiers   = build_tiers(scope)         # 顺序执行
    cfg     = parse_flags(args)
    results = []

    for tier in tiers:                   # 顶层 for：逐 tier
        r = run_tier(tier, cfg)
        log_terminal(tier, r)
        results.append(r)
        if r.verdict == "FAIL" and not cfg.continue_on_fail:
            break

    overall = "PASS" if all(r.verdict == "PASS" for r in results) else "FAIL"
    write_terminal_line(overall)
    exit(0 if overall == "PASS" else 1)
```

## tier_meta — agent-judge 双探针 for-loop

```python
def run_tier_meta(cfg):
    rule_intent  = extract_rule_intent("CLAUDE.md")   # 从 git diff 抽出意图问
    probe_q      = build_probe_question(rule_intent)
    judge_prompt = build_judge_prompt(rule_intent)    # 带 JSON schema

    prev_patch = None
    stall      = 0

    for iter in range(1, cfg.MAX_FAST + 1):
        probe_resp  = shell(f'claudefast -p {q(probe_q)}')
        judge_input = judge_prompt.replace("{probe_response}", probe_resp)
        judge_resp  = shell(f'claudefast -p {q(judge_input)}')

        v = parse_json_strict(judge_resp)             # {verdict, reason, suggested_patch}
        log("fast", iter, v.verdict, v.reason)

        if v.verdict == "PASS":
            return Result("PASS", tier="meta", iter=iter, reason=v.reason)

        if v.verdict == "FAIL":
            break                                     # 升 reliable

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

    # reliable 托底，仅一次
    if cfg.fast_only:
        return Result("FAIL", tier="meta", reason="fast-only did not PASS")

    rel_resp = shell(f'claude -p {q(judge_input)}')
    rv       = parse_json_strict(rel_resp)
    log("reliable", 1, rv.verdict, rv.reason)
    return Result(rv.verdict, tier="meta", escalated=True, reason=rv.reason)
```

## tier_demo — tmux 实机 for-loop

```python
def run_tier_demo(cfg):
    # 前置：确保 tmux session 注册
    name = read_file("~/.claude/live_terminal/CURRENT").strip()
    if not name:
        if cfg.no_auto_register:
            return Result("FAIL", tier="demo", reason="no live tmux session")
        shell("bash .claude/skills/register-session/register-session.sh demo_verify")
        name = read_file("~/.claude/live_terminal/CURRENT").strip()

    log_path = f"~/.claude/live_terminal/{name}.log"
    mark     = f"__verify_start_{now_iso()}__"

    # 发命令进 tmux，必加 TMUX= 避免 nested 炸
    shell(f'TMUX= tmux send-keys -t {name} {q("echo " + mark)} Enter')
    shell(f'TMUX= tmux send-keys -t {name} {q("bash start.demo.sh; echo __EXIT=$?")} Enter')

    start_offset = file_size(log_path)
    errors       = []
    exit_code    = None
    deadline     = now() + cfg.TIMEOUT_SEC

    for tick in range(cfg.TIMEOUT_SEC // cfg.POLL_SEC):
        sleep(cfg.POLL_SEC)
        chunk = read_from(log_path, offset=start_offset)
        start_offset += len(chunk)

        errors += scan(chunk, patterns=[
            r"ERROR", r"Traceback", r"can't find pane",
            r"sessions should be nested with care"
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

追加 `insights-share/validation/reports/self_verify_loop.log`：

```
[ISO8601] [scope=meta|demo] [tier=fast|reliable] [iter=N] [verdict] [reason]
...
--- terminal --- [tier=meta] [verdict=PASS] [reason=...]
--- terminal --- [tier=demo] [verdict=PASS] [reason=demo clean]
--- OVERALL --- [PASS] [2026-04-21T17:22:03+08:00]
```

## 不变量

| 不变量 | 保证 |
|--------|------|
| judge 仅输出合法 JSON | `parse_json_strict` 失败 → 直接 FAIL，禁止自由发挥 |
| 循环必终止 | `MAX_FAST` 硬顶 + reliable 单次 + demo `TIMEOUT_SEC` 硬顶 |
| stall 必升级 | 2 轮同 patch → break fast，强制 reliable |
| tmux 不递归炸 | 所有 `tmux send-keys` 前 `TMUX=`（遵循 tmux-nested.md） |
| 日志不丢 | pipe-pane 行级落盘，按 offset 增量读 |
| override 必审 | `--override` 必须带 reason，写 terminal 行，退 3 |

## 与现有 rule 映射

| 既有 rule | `/self-verify-loop` 做的事 |
|-----------|----------------------------|
| meta-self-verify.md | tier_meta 执行器，就是它 |
| start-demo-verify.md | tier_demo 执行器，就是它 |
| start-demo-register-fallback.md | tier_demo 前置：auto-register |
| live-terminal.md | tier_demo 读日志契约 |
| tmux-nested.md | tier_demo 发 tmux 命令前 `TMUX=` |
| atomic-commits.md | REFINE + auto-patch 分支立即 commit |

## 非目标

- 不替代人工 code review
- 不发明新验收逻辑，只编排既有 rule
- 不跑测试套件（测试由 `validation/run_all_validations.sh` 负责）
- 不判「规则设计得好不好」，只判「CLI 真的吃到规则没 + demo 真的跑通没」

## 实现落盘路径

| 文件 | 角色 |
|------|------|
| `docs/rules/self-verify-loop.md` | 本文件，规则详情 |
| `.claude/commands/self-verify-loop.md` | slash 入口 |
| `.claude/skills/self-verify-loop/SKILL.md` | skill 逻辑文档 |
| `.claude/skills/self-verify-loop/run.sh` | bash 实现（后续 PR 落地） |
| `insights-share/validation/reports/self_verify_loop.log` | 运行日志 |
