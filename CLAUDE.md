# CLAUDE.md

## 规则

| 规则名 | 描述 | 触发时机 | 详情 |
|--------|------|----------|------|
| 仅使用中文 | 所有文档、对话、代码注释仅使用中文 | 始终 | [language.md](docs/rules/language.md) |
| CLAUDE.md 规则格式 | 新增规则只能用 `\| 名称 \| 描述 \| 触发时机 \| docs/rules/*.md 链接 \|` 一行格式，详情写入对应 md 文件，禁止散文/项目符号/独立段落 | 向 CLAUDE.md 添加任何规则时 | [claude-md-format.md](docs/rules/claude-md-format.md) |
| 根目录 md 禁止编辑 | proposal.md / README.md / validation_AB.md / validation.md 均为只读，Agent 不得对其执行任何写入或修改操作 | 任何涉及根目录 *.md 文件的写入/编辑操作前 | [uneditable-md.md](docs/rules/uneditable-md.md) |
| user_design 目录禁止编辑 | docs/designs/user_design/ 整个目录为只读，Agent 不得写入、编辑或删除其中任何文件 | 任何涉及 docs/designs/user_design/ 的写入/编辑操作前 | [uneditable-md.md](docs/rules/uneditable-md.md) |
| 任务前必读四文件 | 任何任务开始前必须先读取 proposal.md / README.md / validation_AB.md / validation.md，建立完整上下文后再执行 | 每个新任务开始前 | [read-before-task.md](docs/rules/read-before-task.md) |
| 任务前必读 proposal 目录 | 读 proposal.md 后必须跟进读 proposal/INDEX.md 及其所列全部设计 md | 每个新任务开始前 | [read-before-task.md](docs/rules/read-before-task.md) |
| 新增 proposal 设计文档 | 新设计 md 落在 proposal/，同步更新 proposal/INDEX.md + CLAUDE.md 索引表；禁止加回根目录 | 新增 proposal_*.md 时 | [proposal/INDEX.md](proposal/INDEX.md) |
| 实机测试 session | 实机测试日志走 ~/.claude/live_terminal/ 契约：当前 session 名写在 CURRENT，镜像在 <name>.log；用 .claude/skills/register-session/ 注册，agent 先 cat CURRENT 再 Read <name>.log | 用户报告实机 bug / 需要看用户实际终端输出时 | [live-terminal.md](docs/rules/live-terminal.md) |
| tmux 嵌套必 unset $TMUX | 在 register-session 注册的 tmux 里再起 tmux 时，仅加 `-L` 独立 socket 不够；tmux 靠 `$TMUX` 环境变量判断 nested，必须用 `TMUX= tmux ...` 或 `unset TMUX`，否则报 `sessions should be nested with care` 或后续 `can't find pane` | 在 live_demo 等已注册 tmux 里运行 start.demo.sh / start.codex.sh / 任何内部再启 tmux 的脚本时 | [tmux-nested.md](docs/rules/tmux-nested.md) |

## 设计文档索引

| 文件 | 类型 | 说明 |
|------|------|------|
| [proposal/proposal_conflict_design.md](proposal/proposal_conflict_design.md) | 正式数据模型（权威） | Topic 中心 Good/Bad 并列共存：同一 Topic 下多人多场景决策并列展示；good=此场景选了此方案，bad=此场景拒绝此方案；不挑最优、不合并、不做冲突检测 |
| [proposal/proposal_wiki_card.md](proposal/proposal_wiki_card.md) | 现状磁盘形态（参考） | `wiki_tree/` 存储布局、卡片 JSON+markdown 结构、label override 流程、已废弃冲突机制说明 |
| [docs/designs/INDEX.md](docs/designs/INDEX.md) | 索引 | claude_codes_to_design / claude_design / user_design 三目录说明 |
