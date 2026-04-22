---
{
  "id": "m1-tmux-nested-2026-04-22",
  "title": "tmux 嵌套必清 $TMUX 环境变量",
  "author": "m1",
  "confidence": 0.95,
  "tags": ["tmux", "nested", "TMUX=", "session", "shell"],
  "status": "active",
  "applies_when": ["在已注册的 tmux session 里再起 tmux", "run start.demo.sh in live_demo tmux", "任何 -L 独立 socket 场景"],
  "do_not_apply_when": ["最外层宿主终端（非 tmux）", "单纯起独立 tmux server 无 attach 需求"],
  "topic_id": "tmux-patterns",
  "label": "good",
  "label_note": "内层 tmux attach 前加 TMUX= 前缀清环境变量，绕过 nested 检查",
  "raw_log": null
}
---

# tmux 嵌套必清 $TMUX 环境变量

> author: m1 · confidence: 0.95

## Description

tmux 判断是否 nested只看 `$TMUX` 环境变量，不看 socket 路径。加 `-L` 独立 socket 只避免 server 冲突，**不绕过** nested 检查。

## Good example

```bash
# 方法1：每次调用都清
SOCK="demo-${TS}-$$"
tm() { TMUX= tmux -L "$SOCK" "$@"; }
tm new-session -d -s "$SESSION" ...
tm attach -t "$SESSION"    # ← nested 也不会被拦

# 方法2：只在 attach 行清
TMUX= tmux -L "$SOCK" attach -t "$SESSION"
```

## Bad example

```bash
# ❌ 以为 -L 就够了，结果在 live_demo tmux 里被拦
tmux -L demo_sock attach -t demo-$$
```

错误信号：
- `sessions should be nested with care, unset $TMUX to force`
- `can't find pane: 1`（pane 创建后立即退出）

## 自检命令

```bash
echo "$TMUX"    # 非空：确认在 tmux 内
TMUX= tmux -L ping_sock attach -t ping    # 能 attach 就说明嵌套路径通了
```

## Applies when

- 在已注册的 tmux session 里再起 tmux
- run start.demo.sh in live_demo tmux
- 任何 -L 独立 socket 场景

## Do NOT apply when

- 最外层宿主终端（非 tmux）
- 单纯起独立 tmux server 无 attach 需求
