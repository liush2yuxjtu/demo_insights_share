# `start` Bootstrap 指令

## 规则

在本项目里用户对 Claude Code CLI 发送 **裸消息 `start`** 时，agent 必须把它当作项目引导指令，而非普通对话，按下面固定流程执行。该流程要求 **先全量扫描现有 proposal 集合，再从中识别新增或未落地 proposal，并只对这些项进入实现**；已落地项必须显式标记，不得重复返工。

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
3. **全量扫描 proposal 并判定状态**
   - 按 INDEX 顺序，输出 `proposal → 状态（已落地 / 新增 / 未落地）→ 关键交付物` 列表
   - `新增` 指本轮新加入 `proposal/INDEX.md` 的设计文档
   - `未落地` 指文档已存在，但关键交付物尚未在仓库落地或与设计不一致
4. **实现**
   - 只对 `新增` / `未落地` proposal 逐条落地；已落地 proposal 仅记录状态，不重复实现
   - 编辑即原子 commit（触发 `编辑即原子 commit` 规则）
5. **自验证**（触发 `meta self-verify` 规则）
   - 每次改 CLAUDE.md / proposal 后跑 `claudefast -p "..."` 状态灯
6. **收尾**
   - 输出 `PASS` / `FAIL` + proposal 状态清单 + commit 列表

## 最低证据标准

`start` 的执行输出不能只描述规则意图，必须包含最小可验收证据：

1. 四文件读取确认：`proposal.md` / `README.md` / `validation_AB.md` / `validation.md`
2. proposal 状态清单：每条 proposal 都要给出 `已落地` / `新增` / `未落地`
3. 已跳过项：明确哪些 proposal 因“已落地”而未重复实现
4. 实际 commit 列表：本轮真正产生的 commit
5. `PASS` / `FAIL` 收尾：给出终局判定，而不是停在中间过程说明

若缺少以上任一项，视为 bootstrap 证据不足，不能判定为完成。

## 说明性探针与实机执行的区别

- 当用户**真的发送裸消息 `start`** 时，agent 必须按固定流程实机执行，并输出上面的完整证据。
- 当外部探针只是在问“如果发送 `start` 会发生什么”时，允许回答流程与证据要求的摘要。
- 说明性响应至少要明确：四文件、proposal 状态清单、已跳过项、commit 列表、`PASS` / `FAIL` 这五类证据是实际执行时必须出现的。
- 说明性响应不得把步骤摘要冒充为已经完成的实机执行结果。

## 禁止

- 不得把 `start` 当闲聊回复
- 不得跳过 proposal/INDEX.md 读取
- 不得只看最新一个 proposal 就直接开工
- 不得将多个 proposal 压进同一 commit
- 不得把已明确落地且无变更的 proposal 重新实现一遍

## 为什么

agent 进场第一件事应是把全部上下文进内存，再动手。`start` 是显式 bootstrap 入口，避免每次都用户手动粘贴 4 个文件路径；同时通过“先全量扫描、再只实现新增/未落地项”的流程，避免漏掉新 proposal，也避免重复返工已经落地的设计。
