# docs_rules · INDEX

| name | description | trigger when | docs |
|------|-------------|--------------|------|
| 根目录md只读 | proposal/README/validation_AB/validation.md 禁止编辑 | 任何涉及根目录 *.md 文件的写入操作 | [根目录md只读.md](./根目录md只读.md) |
| skill_触发条件 | skill 触发条件写入 description，发现不稳定时补 .codex/skills 镜像 | 新建或修改 skill 或需要自动触发时 | [skill_触发条件.md](./skill_触发条件.md) |
| 错误消息格式 | 错误消息包含: what (发生了什么) / why (为什么) / how to fix (怎么修) | 向用户报告错误时 | [错误消息格式.md](./错误消息格式.md) |
| claude_md_规则格式 | 仅能用表格格式，禁止散文/项目符号，详情写入 docs/rules/*.md | 向 CLAUDE.md 添加新规则时 | [claude_md_规则格式.md](./claude_md_规则格式.md) |
| 错误信号判断 | 区分 soft error (可重试) 和 fatal error (停止)，选择应对策略 | bash/tool 返回非零 exit code 时 | [错误信号判断.md](./错误信号判断.md) |
| 编码风格 | 遵循不可变性/KISS/DRY/YAGNI原则，重视文件组织/命名/错误处理 | 编写或修改代码时 | [编码风格.md](./编码风格.md) |
| git_非破坏操作 | 避免破坏操作，寻找安全替代方案，非用户显式请求不执行 | 需要 git reset --hard 或 push --force 时 | [git_非破坏操作.md](./git_非破坏操作.md) |
| 代码注释中文化 | 所有代码注释仅使用中文，遵循项目 language.md 规则 | demo_insights_share 项目开发时 | [代码注释中文化.md](./代码注释中文化.md) |
| 默认脱敏 | 引用 settings.json/token/日志时只展示安全摘要 | 引用配置/日志/token 时 | [默认脱敏.md](./默认脱敏.md) |
| 可视化优先 | 适合可视化的任务先输出到 /tmp/TOPIC.html | 任务结果可展示时 | [可视化优先.md](./可视化优先.md) |
| user_design目录禁止编辑 | 整个目录为只读，禁止写入/编辑/删除文件 | 任何涉及 docs/designs/user_design/ 的写入操作 | [user_design目录禁止编辑.md](./user_design目录禁止编辑.md) |
| 缓存与无状态 | 优先无状态设计，需要缓存时明确声明 TTL 和淘汰策略 | 设计可复用 tool 时 | [缓存与无状态.md](./缓存与无状态.md) |
| 前文档版本记录 | 修改前先用 Edit/Read 记录旧内容，便于追溯 | 修改已存在的 *.md 文件时 | [前文档版本记录.md](./前文档版本记录.md) |
| 单一职责原则 | 一个 skill/函数只做一件事，避免多功能耦合 | 设计 skill 或函数时 | [单一职责原则.md](./单一职责原则.md) |
