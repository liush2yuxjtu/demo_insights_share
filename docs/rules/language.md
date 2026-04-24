# 仅使用中文

## 规则

项目内所有文档、对话回复、代码注释仅使用中文。

硬性要求：`ONLY answer in chinese`。除代码、命令、路径、标识符、日志原文和第三方错误原文外，面向用户的自然语言回复必须只使用中文。

## claudefast 验证

当运行以下探针时：

```bash
claudefast -p "what languages you use when you answer my question"
```

期望答案必须明确表达：本项目回答用户问题时使用中文。可接受等价表述包括 `中文`、`Chinese`、`只使用中文`、`用中文回答`。

## 覆盖范围

- Markdown 文档（README、CLAUDE.md、提案、报告等）
- 与 AI 助手的对话回复
- 代码内注释（行注释、块注释、docstring）

## 例外

- 代码标识符（变量名、函数名、类名）保持原有英文命名，不强制翻译。
- 引用第三方文档、错误信息时可保留原文，但需附中文说明。
