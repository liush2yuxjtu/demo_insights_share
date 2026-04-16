# CLAUDE.md

## 规则

| 规则名 | 描述 | 触发时机 | 详情 |
|--------|------|----------|------|
| 仅使用中文 | 所有文档、对话、代码注释仅使用中文 | 始终 | [language.md](docs/rules/language.md) |
| CLAUDE.md 规则格式 | 新增规则只能用 `\| 名称 \| 描述 \| 触发时机 \| docs/rules/*.md 链接 \|` 一行格式，详情写入对应 md 文件，禁止散文/项目符号/独立段落 | 向 CLAUDE.md 添加任何规则时 | [claude-md-format.md](docs/rules/claude-md-format.md) |
| 根目录 md 禁止编辑 | proposal.md / README.md / validation_AB.md / validation.md 均为只读，Agent 不得对其执行任何写入或修改操作 | 任何涉及根目录 *.md 文件的写入/编辑操作前 | [uneditable-md.md](docs/rules/uneditable-md.md) |
| user_design 目录禁止编辑 | docs/designs/user_design/ 整个目录为只读，Agent 不得写入、编辑或删除其中任何文件 | 任何涉及 docs/designs/user_design/ 的写入/编辑操作前 | [uneditable-md.md](docs/rules/uneditable-md.md) |
| 任务前必读四文件 | 任何任务开始前必须先读取 proposal.md / README.md / validation_AB.md / validation.md，建立完整上下文后再执行 | 每个新任务开始前 | [read-before-task.md](docs/rules/read-before-task.md) |

## 设计文档索引

| 文件 | 类型 | 说明 |
|------|------|------|
| [proposal_conflict_design.md](proposal_conflict_design.md) | 用户设计 | Topic 中心 Good/Bad 示例 Wiki：同一话题下多用户上传实战案例，自行标注 good/bad，含完整 raw_log，管理员可覆盖 label |
| [proposal_wiki_card.md](proposal_wiki_card.md) | Claude 从代码提取 | Wiki 卡片冲突与合并机制：现有 card schema、merge 实现、冲突检测提案 |
| [docs/designs/INDEX.md](docs/designs/INDEX.md) | 索引 | claude_codes_to_design / claude_design / user_design 三目录说明 |
