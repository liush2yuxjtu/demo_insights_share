# docs/designs · INDEX

本目录下有三个子文件夹，含义如下：

| 文件夹 | 含义 | 可编辑方 |
|--------|------|---------|
| `claude_codes_to_design/` | Claude **先写代码**，再从代码中反向提取出设计文档 | Claude 可写 |
| `claude_design/` | Claude **直接输出设计文档**，不依赖已有代码 | Claude 可写 |
| `user_design/` | **用户自己撰写**的设计文档，仅供 Claude 读取参考 | **⛔ UN_EDITABLE** |

---

## ⛔ UN_EDITABLE：`user_design/`

`docs/designs/user_design/` 目录及其所有内容为**只读**。

Agent 规则（等同于 CLAUDE.md 硬门禁）：
- 禁止对该目录下任何文件执行 Write / Edit / Delete / 重命名操作
- 禁止通过 Bash（sed、awk、重定向等）修改该目录下任何文件
- 允许 Read 读取以获取上下文
- 若任务需要修改该目录，必须先向用户说明原因并获得明确授权，否则终止操作
