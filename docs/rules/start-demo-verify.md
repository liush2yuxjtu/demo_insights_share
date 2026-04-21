# start.demo.sh 是人类最终可见面

## 核心断言

`start.demo.sh` 是本项目 human-last-visible surface —— 用户真正看到、运行、信任的唯一入口。任何新 feature 若不能从 `start.demo.sh` 走通，等同未交付。

## 触发时机

任何以下操作完成后立即触发：

- 新增 feature（脚本、hook、skill、statusline、proposal 落地实现等）
- 修改已有 feature（行为变化、参数变化、输出变化）
- 修改 `start.demo.sh` 本身或其依赖脚本

## 强制动作

1. **更新 demo**：同步修改 `start.demo.sh`，让新 feature 在 demo 输出里可见、可被用户直接观察到。
2. **tmux 实机 self-verify**：必须在 tmux 会话内执行一次完整 `start.demo.sh`（遵循 `tmux-nested.md`：嵌套 tmux 必 `TMUX= tmux ...` 或先 `unset TMUX`）。
3. **debug 到绿**：观察 tmux pipe-pane 日志，确认 feature 行为、退出码、无 ERROR / Traceback / `can't find pane` / `sessions should be nested with care` 之类异常信号。
4. **修复后重跑**：任何 fail 必须修复后再跑一次完整 `start.demo.sh`，而不是跳过或假装通过。

## 完成判定

- tmux 日志里看到 feature 的实际输出（不是“应该能跑”）。
- 退出码 0。
- 无未预期错误信号。
- `start.demo.sh` 末尾自检（若有）全绿。

以上全部满足才能声称 feature done 并进入 atomic commit。

## 与其它规则的关系

- `tmux-nested.md`：在已注册 tmux 里再起 tmux 必须处理 `$TMUX`。
- `live-terminal.md`：实机日志走 `~/.claude/live_terminal/` 契约，agent 用 `cat CURRENT` + `Read <name>.log` 读输出。
- `atomic-commits.md`：self-verify 通过后按单一关注点立即 commit。
- `meta-self-verify.md`：若本次修改涉及 CLAUDE.md，再跑 agent-judge 双探针。
