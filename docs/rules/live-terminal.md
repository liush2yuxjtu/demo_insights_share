# 实机测试 session 约定

## 背景

agent 的自动化 eval loop 看不到用户实机（real-machine）测试时遇到的 bug——
因为 agent 进程根本不在那个终端里。解决办法是：用 tmux pipe-pane 把用户实机
操作的终端持续镜像到固定路径，agent 就能直接 Read 到。

## 文件契约

```
~/.claude/live_terminal/CURRENT       单行文本，当前活跃 session 名
~/.claude/live_terminal/<name>.log    tmux pipe-pane 持续镜像（行级写入，不会因滚屏丢失）
```

## 注册方式

用 project-level skill：**register-session**（入口：`.claude/skills/register-session/SKILL.md`）。

| 场景 | 命令 |
|------|------|
| 新建 + 弹 Terminal 窗口 + 注册 | `bash .claude/skills/register-session/register-session.sh <name>` |
| 仅绑定已有 tmux session | `bash .claude/skills/register-session/register-session.sh <name> --existing` |
| 查询当前注册 | `bash .claude/skills/register-session/register-session.sh` |
| 清 CURRENT（不 kill session） | `bash .claude/skills/register-session/register-session.sh --clear` |

用户也可以直接对 agent 说"/register-session bugtest"、"注册一下 session 叫
bugtest"、"把我这个 tmux 绑上"等，skill description 都能命中。

## agent 读日志流程

1. `cat ~/.claude/live_terminal/CURRENT` 拿 name；如为空，告诉用户"尚未注册实机 session"。
2. Read `~/.claude/live_terminal/<name>.log`。
3. 如需 pipe-pane 没覆盖到的滚屏 buffer：`tmux capture-pane -pt <name> -S -5000`。

## Good Example

> **用户**：这个按钮点了没反应，你看看日志。
>
> **Agent**：
> 1. 执行 `cat ~/.claude/live_terminal/CURRENT` → `bugtest_apr17`
> 2. Read `~/.claude/live_terminal/bugtest_apr17.log`，定位到 500 报错
> 3. 回答："日志第 312 行 `POST /api/publish_good` 返回 500，栈指向
>    `runtime_store.py:88` 的 `KeyError: 'author'`，建议补默认值或校验。"

## Bad Example

> **用户**：这个按钮点了没反应。
>
> **Agent**："请把终端输出贴给我。" ← 退化成人肉粘贴，浪费用户时间且可能截断关键行。

## 同模式的工程参照

`insights-share/validation/run_start_tmux_smoke.sh` 已经在用
`tmux pipe-pane -o -t <session> "cat > <file>"` 做自动化测试镜像。本规则只是把
同一模式延伸到人机交互的实机测试场景。
