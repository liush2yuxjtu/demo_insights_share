---
{
  "id": "m1-live-terminal-2026-04-22",
  "title": "实机日志走 ~/.claude/live_terminal/ 契约",
  "author": "m1",
  "confidence": 0.9,
  "tags": ["live-terminal", "logging", "session", "tmux", "register-session"],
  "status": "active",
  "applies_when": ["用户报告实机 bug", "需要看用户实际终端输出"],
  "do_not_apply_when": ["纯代码推理无需实机验证", "用户已在 session 内直接交互"],
  "topic_id": "delivery-patterns",
  "label": "good",
  "label_note": "CURRENT 文件存当前 session 名，镜像到 <name>.log",
  "raw_log": null
}
---

# 实机日志走 ~/.claude/live_terminal/ 契约

> author: m1 · confidence: 0.9

## 契约内容

- `~/.claude/live_terminal/CURRENT` 存当前 session 名
- 终端镜像写到 `~/.claude/live_terminal/<name>.log`
- 用 `.claude/skills/register-session/register-session.sh <name>` 注册

## Agent 正确读法

```bash
cat CURRENT    # 确认 session 名
Read <name>.log    # 读实际日志
```

## Bad example

```bash
# ❌ 不走 live-terminal 契约，用户问"日志在哪"
echo "check the output"    # 无跟踪路径
```

## Good example

```bash
# ✅ 按契约走
cat ~/.claude/live_terminal/CURRENT
# → live_demo
cat ~/.claude/live_terminal/live_demo.log
```

## Applies when

- 用户报告实机 bug
- 需要看用户实际终端输出

## Do NOT apply when

- 纯代码推理无需实机验证
- 用户已在 session 内直接交互
