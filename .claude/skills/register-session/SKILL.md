---
name: register-session
description: 注册/创建一个 tmux 实机测试 session，建立固定日志镜像，让 agent 能直接读取用户实际操作终端的输出。当用户说 "/register-session"、"/new-session"、"注册一下 session"、"注册实机 session"、"建一个实机 tmux"、"让你能看到我这个终端"、"把我的终端绑上"、"register tmux session"、"pop out a new terminal window" 时触发。
---

# register-session

把实机测试（real-machine testing）时用户操作的 tmux session 注册到固定契约，
agent 的 eval loop 看不到、但用户肉眼看得到的 bug，通过 tmux pipe-pane 镜像到
固定路径后，agent 直接 Read 即可。

## 文件契约

```
~/.claude/live_terminal/CURRENT      单行文本，当前活跃 session 名
~/.claude/live_terminal/<name>.log   tmux pipe-pane 持续镜像（无滚屏丢失）
```

## 如何执行

本 skill 的逻辑全部放在同目录脚本 `register-session.sh`。被触发时：

1. 从用户话语里解析 name 和是否 `--existing`。
2. 执行对应命令：

```
bash .claude/skills/register-session/register-session.sh <name>             # 新建 + pipe-pane + 弹 Terminal + 写 CURRENT
bash .claude/skills/register-session/register-session.sh <name> --existing  # 只绑定已存在 session
bash .claude/skills/register-session/register-session.sh                    # 查询当前 session 状态
bash .claude/skills/register-session/register-session.sh --clear            # 清 CURRENT（不 kill session）
```

3. 把脚本 stdout 原样展示给用户。
4. 如果用户说"注册 session"但没给 name，询问一次想用什么名字；如果用户直接
   说"把当前 tmux session 叫 bugtest 注册上"，直接用 `bugtest`。

## agent 读日志的约定

触发后或之后任何时刻，想知道"用户实机终端正在发生什么"：

```
CUR=$(cat ~/.claude/live_terminal/CURRENT 2>/dev/null)
[ -n "$CUR" ] && Read ~/.claude/live_terminal/${CUR}.log
```

如果需要 pipe-pane 没覆盖到的更老滚屏 buffer：

```
tmux capture-pane -pt <name> -S -5000
```

## 为什么要这个

完整上下文 + 原始会话引用见同目录 `README.md`。
