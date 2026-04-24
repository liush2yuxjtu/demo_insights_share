---
{
  "id": "m1-register-fallback-2026-04-22",
  "title": "跑 start.demo.sh 前必须检查 tmux session 注册状态",
  "author": "m1",
  "confidence": 0.9,
  "tags": ["tmux", "register-session", "start.demo.sh", "live-terminal", "session"],
  "status": "active",
  "applies_when": ["跑 start.demo.sh self-verify 前发现未注册 tmux session", "live-terminal/CURRENT 文件空或失效"],
  "do_not_apply_when": ["不在 live terminal 内工作", "已有注册 session 且 CURRENT 指向有效 session"],
  "topic_id": "tmux-patterns",
  "label": "good",
  "label_note": "未注册时必须先跑 register-session 建立契约，再跑 demo 并读日志",
  "raw_log": null
}
---

# 跑 start.demo.sh 前必须检查 tmux session 注册状态

> author: m1 · confidence: 0.9

## 规则

self-verify 触发时若 `~/.claude/live_terminal/CURRENT` 空/失效，agent **不得**让用户手动贴日志。必须先建/绑 session，再跑 `start.demo.sh`。

## 正确流程

1. 检查 `~/.claude/live_terminal/CURRENT` 是否存在且有效
2. 若无效：`.claude/skills/register-session/register-session.sh <name>` 建 session
3. 在 session 内跑 `start.demo.sh`
4. 按 live-terminal 契约读日志：`cat CURRENT` 确认 session 名，再 `Read <name>.log`

## Bad example

```bash
# ❌ 不检查 CURRENT，直接跑 start.demo.sh
./start.demo.sh
# 用户问"日志在哪" → agent 无法回答
```

## Good example

```bash
# ✅ 先确认 live terminal 状态
cat ~/.claude/live_terminal/CURRENT    # session 名在文件内
cat ~/.claude/live_terminal/<session_name>.log    # 读实际日志
```

## Applies when

- 跑 start.demo.sh self-verify 前发现未注册 tmux session
- live-terminal/CURRENT 文件空或失效

## Do NOT apply when

- 不在 live terminal 内工作
- 已有注册 session 且 CURRENT 指向有效 session
