# `start` Bootstrap 指令

## 规则

在本项目里用户对 Claude Code CLI 发送 **裸消息 `start`** 时，agent 必须把它当作项目引导指令，而非普通对话，按下面固定流程执行。

## 触发条件

- 用户向本项目里的 Claude Code CLI 发送消息 `start`（或 `START` / `Start` 大小写不敏感）
- 消息只有这一个 token，无附加语义

## 固定流程

1. **读上下文四文件**（触发 `任务前必读四文件` 规则）
   - `proposal.md`
   - `README.md`
   - `validation_AB.md`
   - `validation.md`
2. **读 proposal 目录**（触发 `任务前必读 proposal 目录` 规则）
   - `proposal/INDEX.md`
   - `proposal/` 下全部 `proposal_*.md`
3. **列出待实现 proposal**
   - 按 INDEX 顺序，输出 `proposal → 关键交付物` 列表
4. **实现**
   - 逐条 proposal 落地；编辑即原子 commit（触发 `编辑即原子 commit` 规则）
5. **自验证**（触发 `meta self-verify` 规则）
   - 每次改 CLAUDE.md / proposal 后跑 `claudefast -p "..."` 状态灯
6. **收尾**
   - 输出 `PASS` / `FAIL` + commit 列表

## 禁止

- 不得把 `start` 当闲聊回复
- 不得跳过 proposal/INDEX.md 读取
- 不得将多个 proposal 压进同一 commit

## 为什么

agent 进场第一件事应是把全部上下文进内存，再动手。`start` 是显式 bootstrap 入口，避免每次都用户手动粘贴 4 个文件路径。
