# shell_env · INDEX

| name | description | trigger when | docs |
|------|-------------|--------------|------|
| 实机日志契约 | 走 ~/.claude/live_terminal/，CURRENT 记当前 session，镜像在 <name>.lo | 需要记录用户实机输出时 | [实机日志契约.md](./实机日志契约.md) |
| 权限检查优化 | 使用 less-permission-prompts skill，扫描 transcript 添加 allowlist | 频繁需要权限确认的任务场景 | [权限检查优化.md](./权限检查优化.md) |
| 沙箱脚本污染 | 禁止 symlink 污染真实 ~/.claude，必须 export HOME=$SANDBOX_HOME | 需要写 sandbox shell 脚本时 | [沙箱脚本污染.md](./沙箱脚本污染.md) |
| tmux嵌套环境变量 | 仅加 -L 独立 socket 不够，必须 TMUX= tmux 或 unset TMUX | 在已注册 tmux 里再启 tmux 时 | [tmux嵌套环境变量.md](./tmux嵌套环境变量.md) |
| worktree_分离开发 | 使用 worktree 而非频繁 checkout，隔离分支状态和 context | 处理多分支并行工作时 | [worktree_分离开发.md](./worktree_分离开发.md) |
