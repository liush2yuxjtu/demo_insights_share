# register-session skill

项目级 skill：注册用户实机测试的 tmux session，把 pipe-pane 镜像到固定路径，
让 agent 的 Read 工具能直接看到用户终端上正在发生的一切。

## 为什么要这个 skill（pain point）

agent 的自动化 self-eval loop 和 `insights-share/validation/run_start_tmux_smoke.sh`
之类的脚本都跑通了，但用户肉眼做实机测试时仍然会碰到 agent 从没见过的 bug。
问题在于：**agent 进程根本看不到用户那个终端的输出**——不是输出丢了，而是
没有任何通道把用户终端的内容交给对话里的 agent。

本 skill 把"哪个 tmux session 是用户在操作的"这件事变成一个**可 Read 的文件契约**，
消灭"我看到了你看不到"的不对称。

### 原始对话证据（grounding）

同目录 `raw/` 下是触发本 skill 诞生的三段原始 Claude Code 会话（从
`~/.claude/projects/-Users-m1-projects-demo-insights-share/` 复制而来，保留
jsonl 原格式）：

| 文件 | 出处 | 关键内容 |
|------|------|----------|
| [`raw/session-pain-point-20260417-1338.jsonl`](raw/session-pain-point-20260417-1338.jsonl) | 源 session `3ae6c68f-7ca0-4378-a405-abdecdeb5861` | 用户首次描述痛点并请求 skill 设计，是本 skill 的直接触发会话 |
| [`raw/session-tmux-smoke-20260417-1331.jsonl`](raw/session-tmux-smoke-20260417-1331.jsonl) | 源 session `7a4bcb58-b6c2-44b7-9f14-be1a54f9cb9c` | 里面 tmux/pipe-pane 出现 95 次，是本项目早已用在自动化测试里的同一模式 |
| [`raw/session-tmux-context-20260417-1320.jsonl`](raw/session-tmux-context-20260417-1320.jsonl) | 源 session `a00e632f-17e7-49d6-a0f6-c0b5959ba170` | 更早一轮 tmux 测试上下文，说明"把终端镜像到文件"并非新发明 |

直接引用源 session 里用户原话（`raw/session-pain-point-20260417-1338.jsonl` 第 28 行，`"type":"last-prompt"`）：

> do we have tools to monitor the 实机测试？ the agent self eval loop didn't
> see bugs but in our real run we found it. i found it is not even aviable
> to tell agents to read from my bugs ( the bugs are NOT readable to
> agents!) how should we do this ?

以及下一轮追问（同文件第 44 行 `"type":"queue-operation"`）要求把本 skill 落盘：

> create a project level skill /register-session maybe ? … we run or say
> /new-session to create a tmux window and pop out for me. then the
> CLAUDE.md or local fixed texts know which tmux window we are using.

这两条原话定义了本 skill 的目标：**让 agent 永远知道哪个 tmux session 是"真"
在被用户操作的那个**。

## 契约（与 CLAUDE.md 对齐）

```
~/.claude/live_terminal/CURRENT      单行文本，当前活跃 session 名
~/.claude/live_terminal/<name>.log   tmux pipe-pane 持续镜像（行级写入，无滚屏丢失）
```

- 注册侧：`register-session.sh` 负责 tmux new / pipe-pane / 写 CURRENT / 弹 Terminal。
- 读取侧：任何 agent 先 `cat CURRENT` 拿 name，再 `Read <name>.log`。

## 用法速查

```bash
# 场景 1：开始新一次实机测试
bash .claude/skills/register-session/register-session.sh bugtest_apr17
# → 新 tmux session bugtest_apr17 + pipe-pane → ~/.claude/live_terminal/bugtest_apr17.log
# → 弹出 Terminal 窗口直接 attach
# → CURRENT 写入 bugtest_apr17

# 场景 2：已经有 tmux session 正在跑，要绑上
bash .claude/skills/register-session/register-session.sh demo_session --existing

# 场景 3：agent 想知道当前在监控谁
bash .claude/skills/register-session/register-session.sh
# → 打印 CURRENT、日志路径、tmux 状态、最近 10 行

# 场景 4：结束测试（不 kill tmux，只清 CURRENT）
bash .claude/skills/register-session/register-session.sh --clear
```

## skill 触发方式

见 [`SKILL.md`](SKILL.md)。简化 description 里覆盖了中英文多种说法
（`/register-session` / "注册实机 session" / "pop out a new terminal window" 等）。

## 文件结构

```
.claude/skills/register-session/
├── README.md                 本文件：上下文 + jsonl 引用
├── SKILL.md                  Claude Code skill 入口（description + 执行流程）
├── register-session.sh       可执行脚本，真正做事
└── raw/
    ├── session-pain-point-20260417-1338.jsonl
    ├── session-tmux-smoke-20260417-1331.jsonl
    └── session-tmux-context-20260417-1320.jsonl
```

## 相关文件

- 项目规则行：[`/Users/m1/projects/demo_insights_share/CLAUDE.md`](../../../CLAUDE.md)
- 规则详情：[`/Users/m1/projects/demo_insights_share/docs/rules/live-terminal.md`](../../../docs/rules/live-terminal.md)
- 同模式的自动化范例：[`insights-share/validation/run_start_tmux_smoke.sh`](../../../insights-share/validation/run_start_tmux_smoke.sh)
  （这份自动化脚本已经在用 `tmux pipe-pane -o -t <session> "cat > <file>"`；
  本 skill 是把同一模式延伸到人机交互的实机测试。）
