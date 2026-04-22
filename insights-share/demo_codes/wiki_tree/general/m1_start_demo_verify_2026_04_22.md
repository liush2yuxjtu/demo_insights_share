---
{
  "id": "m1-start-demo-verify-2026-04-22",
  "title": "feature 交付前必须跑 start.demo.sh 实机验证",
  "author": "m1",
  "confidence": 0.92,
  "tags": ["start.demo.sh", "self-verify", "tmux", "feature-delivery"],
  "status": "active",
  "applies_when": ["新增 feature", "修改已有 feature（行为/参数/输出变化）", "修改 start.demo.sh 本身"],
  "do_not_apply_when": ["纯文档修改不涉及脚本行为", "仅影响 API 不影响 CLI 输出"],
  "topic_id": "delivery-patterns",
  "label": "good",
  "label_note": "start.demo.sh 是 human-last-visible surface，必须 tmux 内跑通",
  "raw_log": null
}
---

# feature 交付前必须跑 start.demo.sh 实机验证

> author: m1 · confidence: 0.92

## 核心断言

`start.demo.sh` 是本项目 human-last-visible surface —— 用户真正看到、运行、信任的唯一入口。任何新 feature 若不能从 `start.demo.sh` 走通，等同未交付。

## 强制动作

1. **更新 demo**：同步修改 `start.demo.sh`，让新 feature 在 demo 输出里可见
2. **tmux 实机 self-verify**：在 tmux 会话内执行完整 `start.demo.sh`（嵌套 tmux 必 `TMUX=` 或 `unset TMUX`）
3. **debug 到绿**：确认 feature 行为、退出码 0、无 ERROR/Traceback/异常信号
4. **修复后重跑**：任何 fail 必须修复后再跑，不是跳过或假装通过

## 完成判定

- tmux 日志里看到 feature 实际输出
- 退出码 0
- 无未预期错误信号
- `start.demo.sh` 末尾自检全绿

## Applies when

- 新增 feature
- 修改已有 feature（行为/参数/输出变化）
- 修改 start.demo.sh 本身

## Do NOT apply when

- 纯文档修改不涉及脚本行为
- 仅影响 API 不影响 CLI 输出
