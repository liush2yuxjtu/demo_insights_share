# tmux 嵌套启动约定

## 背景

`register-session` 把用户实机终端绑到一个 tmux session（如 `live_demo`），镜像到
`~/.claude/live_terminal/live_demo.log`。但项目里有些脚本（`start.demo.sh`、
`start.codex.sh` 等）内部又要起新的 tmux 做双 pane demo —— 这就是 **tmux-in-tmux
（nested）** 场景。tmux 默认拒绝 nested，容易翻车。

## 现象

在 live_demo 里 `./start.demo.sh`，`~/.claude/live_terminal/live_demo.log` 会
出现两类失败：

| 错误信息 | 触发点 |
|---------|--------|
| `sessions should be nested with care, unset $TMUX to force` | 内层 `tmux attach` 被 nested 防呆拦截 |
| `can't find pane: 1` | 外层脚本把命令塞进 `split-window` 字符串导致解析失败，pane 创建后立即退出，下一步 `select-pane` 找不到 pane |

## 根因

tmux 判断是否 nested **只看 `$TMUX` 环境变量**，不看 socket 路径。

```bash
tmux -L my_sock attach -t foo    # ❌ 仍会被拦 —— $TMUX 还在
TMUX= tmux -L my_sock attach -t foo    # ✅ 清掉 $TMUX 才行
```

换独立 socket（`-L`）只是避免 server 冲突，**不能**绕过 nested 检查。很多脚本
的注释里把两者混为一谈（"-L 指向独立 socket = 独立 server，和外层 `$TMUX`
完全无关" 这种说法是错的）。

## Good Example

```bash
SOCK="demo-${TS}-$$"
tm() { TMUX= tmux -L "$SOCK" "$@"; }    # ← 每次调用都清 $TMUX

tm new-session -d -s "$SESSION" ...
tm split-window -h -t "$SESSION:0.0" ...
tm attach -t "$SESSION"                  # ← nested 也不会被拦
```

或者只在 attach 行清：

```bash
TMUX= tmux -L "$SOCK" attach -t "$SESSION"
```

## Bad Example

```bash
# ❌ 以为 -L 就够了，结果在 live_demo tmux 里启动时被拦
tmux -L demo_sock attach -t demo-$$
```

```bash
# ❌ split-window 塞多行带嵌套引号的命令字符串，pane 立即退出
tmux split-window -h "bash -lc \"cd $DIR && source $ENV && exec claude\""
# 修法：把命令写进独立脚本文件，再 `split-window "bash $RIGHT_SH"`
```

## 自检命令

在 live_demo 里跑 demo 之前，可以先验证：

```bash
# 外层 tmux 里
echo "$TMUX"                     # 非空：确认在 tmux 内
tmux -L ping_sock new -d -s ping sleep 10
TMUX= tmux -L ping_sock attach -t ping    # 能 attach 就说明嵌套路径通了
```

## 相关文件

| 文件 | 关注点 |
|------|--------|
| `start.demo.sh` | L148~L227 的 `tm()` wrapper 与 `tm attach`；需要在 `tm()` 里加 `TMUX=` 或在 attach 行前置 `TMUX=` |
| `start.codex.sh` | 同样模式，同样易踩 |
| `insights-share/validation/run_start_tmux_smoke.sh` | 自动化烟雾测试路径，建议覆盖 nested 场景 |
| `docs/rules/live-terminal.md` | 实机测试 session 注册契约（`register-session` 源） |
