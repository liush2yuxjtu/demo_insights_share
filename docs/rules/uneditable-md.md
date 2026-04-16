# 根目录 md 禁止编辑

## 规则

以下文件/目录为只读，Agent 不得对其执行任何写入、编辑或删除操作：

- `proposal.md`
- `README.md`
- `validation_AB.md`
- `validation.md`
- `docs/designs/user_design/`（整个目录，含子文件）

## 禁止操作

- Write / Edit / 覆写上述任意文件
- 通过 Bash（sed、awk、重定向等）修改上述文件
- 重命名或删除上述文件

## 允许操作

- 读取（Read）上述文件以获取上下文
- 引用其内容生成其他产物

## 违规处理

若任务需要更新上述文件，必须先向用户说明原因并获得明确授权，否则终止操作。
