---
description: 统一自验收入口：tier_meta (CLAUDE.md agent-judge) + tier_demo (start.demo.sh tmux)
allowed-tools: Bash, Read, Edit, Write, Grep, Glob
---

# /self-verify-loop

触发**项目自验收 for-loop pipeline**。规则详情见 `docs/rules/self-verify-loop.md`。

## 参数解析

`$ARGUMENTS` 可能形态：

| 形态 | 含义 |
|------|------|
| 空 | auto：`git diff HEAD` 决定跑哪些 tier |
| `claude-md` | 只跑 tier_meta |
| `feature` | 只跑 tier_demo |
| `all` | 两个都跑 |
| `--override "<reason>"` | 跳 gate，日志必写 reason，退 3 |
| `--fast-only` / `--auto-patch` / `--max-fast N` / `--timeout-sec N` / `--dry-run` / `--no-auto-register` | 见规则 Flag 表 |

## 执行步骤

1. **读规则**：`docs/rules/self-verify-loop.md`（完整 for-loop 伪码 + 不变量）；
   并按 `docs/rules/read-before-task.md` 要求读 proposal.md / README.md / validation_AB.md / validation.md。
2. **加载 skill**：`.claude/skills/self-verify-loop/SKILL.md`；若 `run.sh` 已落地，直接 `bash .claude/skills/self-verify-loop/run.sh $ARGUMENTS`。
3. **未落地 run.sh 时**：按 SKILL.md 的伪码逐步执行（tier_meta 双探针循环 + tier_demo tmux 观察）。
4. **日志**：每轮写一行到 `insights-share/validation/reports/self_verify_loop.log`，格式见规则。
5. **收尾**：按退出码语义汇报 PASS / FAIL / override，并在 `--- OVERALL ---` 行落盘。

## 不变量提醒

- judge 响应必须是合法 JSON；否则视为 FAIL
- `tmux send-keys` 前必加 `TMUX=` 前缀（遵循 `tmux-nested.md`）
- tier_demo 缺 session → 跑 `.claude/skills/register-session/register-session.sh demo_verify` 自动注册（除非 `--no-auto-register`）
- REFINE + `--auto-patch` 分支必须立即原子 commit（遵循 `atomic-commits.md`）
- fast 循环封顶 `--max-fast`（默认 5），stall 2 轮强制 reliable

## 示例

```
/self-verify-loop                     # auto
/self-verify-loop all                 # 两 tier 都跑
/self-verify-loop claude-md --fast-only
/self-verify-loop feature --timeout-sec 600
/self-verify-loop --override "临时绕过：CI 破损修复中"
```
