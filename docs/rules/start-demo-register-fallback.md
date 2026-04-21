# start.demo.sh 找不到已注册 tmux session 时的 fallback

## 核心断言

`start-demo-verify.md` 要求 `start.demo.sh` 在 tmux 里跑实机 self-verify。若触发自验时 `~/.claude/live_terminal/CURRENT` 为空、文件缺失、或所指 session 已失效（`tmux -L <sock> has-session` 失败 / `<name>.log` 不存在），agent 不得退化成「请用户手动贴日志」或直接在非镜像 shell 里跑。必须用项目级 skill **register-session** 先建/绑 session，再按 `live-terminal.md` 契约读日志。

## 触发时机

满足任一即触发 fallback：

- 准备执行 `start.demo.sh` self-verify 时。
- `cat ~/.claude/live_terminal/CURRENT` 返回空或文件不存在。
- `CURRENT` 里的 name 对应的 tmux session 已不存在 / `<name>.log` 丢失。
- 用户报 `start.demo.sh` 跑挂但 agent 读不到任何实机日志。

## 强制动作

1. **检测**：

   ```bash
   CUR=$(cat ~/.claude/live_terminal/CURRENT 2>/dev/null || true)
   ```

   若 `CUR` 空 → 直接进入步骤 2；若非空，再验 `~/.claude/live_terminal/$CUR.log` 是否存在、tmux session 是否活着，任一失败进入步骤 2。

2. **调用 register-session skill**（项目级，入口 `.claude/skills/register-session/SKILL.md`）：

   ```bash
   bash .claude/skills/register-session/register-session.sh start_demo_verify
   ```

   - 默认 name 用 `start_demo_verify`，除非用户指定其它 name。
   - 若用户已有想复用的 tmux session，改用 `--existing`：
     ```bash
     bash .claude/skills/register-session/register-session.sh <name> --existing
     ```

3. **在已注册 session 里跑 demo**：遵循 `tmux-nested.md`，嵌套进入前 `TMUX= tmux ...` 或 `unset TMUX`；确认 pipe-pane 日志写到 `~/.claude/live_terminal/<name>.log`。

4. **按 live-terminal 契约读日志**：`cat CURRENT` → `Read <name>.log`；无 `ERROR` / `Traceback` / `can't find pane` / `sessions should be nested with care` 且退出码 0 才算绿。

5. **失败修复后重跑**：任一步骤 fail，修 root cause 后从步骤 1 重头跑，禁止跳过。

## 完成判定

- `~/.claude/live_terminal/CURRENT` 非空且指向活着的 session。
- `~/.claude/live_terminal/<name>.log` 有完整 `start.demo.sh` 输出。
- 日志全绿，退出码 0。
- 以上满足才进入 `atomic-commits.md` 的 commit 流程。

## 与其它规则的关系

- `start-demo-verify.md`：主规则，要求 tmux 内跑完整 self-verify。
- `live-terminal.md`：日志契约与 `CURRENT`/`<name>.log` 文件路径。
- `tmux-nested.md`：嵌套 tmux 必 `TMUX=` 处理。
- `atomic-commits.md`：绿后立即单一关注点 commit。
