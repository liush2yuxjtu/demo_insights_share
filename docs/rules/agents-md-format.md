# AGENTS.md 规则格式

## 规则

向本项目 `AGENTS.md` 添加任何规则时，必须且只能使用以下单行表格格式：

```markdown
| 规则名 | 描述 | 触发时机 | [文件名](docs/rules/文件名.md) |
```

## 要求

- `AGENTS.md` 只保留索引：每条规则仅占表格一行，描述保持简洁。
- 完整说明写入 `docs/rules/*.md`：规则背景、示例、反例、例外都写在对应规则文件中。
- 禁止散文展开：不得在 `AGENTS.md` 中增加项目符号、独立标题、长段解释或内联示例。

## 正确示例

```markdown
| 优秀 HTML 示例需归档 | 用户明确认可的页面示例必须把原始 HTML 归档到 docs/examples/，并在规则文档中记录来源与用途 | 用户要求保存 good example、示例归档或网页模板沉淀时 | [html-example-archive.md](docs/rules/html-example-archive.md) |
```

## 错误示例

```markdown
## 示例归档规则

- 把好页面保存到 docs/examples
- 记得写来源
```

## 原因

- `AGENTS.md` 是项目规则入口，必须短、稳、便于快速装载。
- 细节拆到 `docs/rules/*.md` 后，后续修订不会污染主索引。
