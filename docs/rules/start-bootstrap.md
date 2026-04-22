# `start` Bootstrap 指令

## 规则

在本项目里用户对 Claude Code CLI 发送 **裸消息 `start`** 时，agent 必须把它当作项目引导指令，而非普通对话，按下面固定流程执行。该流程要求 **先全量扫描现有 proposal 集合，再从中识别新增或未落地 proposal，并只对这些项进入实现**；已落地项必须显式标记，不得重复返工。

这里的 proposal 集合包含设计类 proposal，也包含执行摘要 / 计划类 proposal。只要它被挂进 `proposal/INDEX.md`，就必须进入 `start` 的扫描与落地闭环，不能因为“这是 CEO 计划”就只读不做。

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
   - 不得把某份 proposal 只“隐含包含”在“扫描全部 proposal”这类泛化表述里；必须按文件名逐条列出
   - 若某份 proposal 属于执行摘要 / 计划类文档（例如 CEO 级 next steps），仍必须进入状态清单，并把其中的行动项翻译成待落地范围，而不是只当背景材料跳过
4. **实现**
   - 只对 `新增` / `未落地` proposal 逐条落地；已落地 proposal 仅记录状态，不重复实现
   - 对每个 `新增` / `未落地` proposal，都必须进入同一套 self-verify 闭环：`edit code → run code/test → find bugs/regressions → edit code`
   - 该闭环要持续到对应 proposal 达到可交付状态，或明确收敛为 `FAIL`
   - 计划类 proposal 不得停在“复述计划”；必须把计划翻译成具体改动与验证动作后再进入闭环
   - 编辑即原子 commit（触发 `编辑即原子 commit` 规则）
5. **自验证**（触发 `meta self-verify` 规则）
   - 每次改 CLAUDE.md / proposal 后跑 `claudefast -p "..."` 状态灯
   - 每轮代码改动后都要运行对应命令 / 测试 / demo 路径，主动找 bug，而不是等用户报错
6. **收尾**
   - 输出 `PASS` / `FAIL` + proposal 状态清单 + commit 列表

## 最低证据标准

`start` 的执行输出不能只描述规则意图，必须包含最小可验收证据：

1. 四文件读取确认：`proposal.md` / `README.md` / `validation_AB.md` / `validation.md`
2. proposal 状态清单：每条 proposal 都要给出 `已落地` / `新增` / `未落地`
3. 已跳过项：明确哪些 proposal 因“已落地”而未重复实现
4. 实际 commit 列表：本轮真正产生的 commit
5. `PASS` / `FAIL` 收尾：给出终局判定，而不是停在中间过程说明
6. 逐文件可见性：不能只说“已扫描全部 proposal”，必须能看见每个文件名；计划类 proposal 还要附其被翻译出的行动项
7. 闭环证据：至少能看见一轮 `改代码 → 运行 → 找 bug/回归 → 再改代码` 的执行痕迹；若无需再改，也要说明为何直接 PASS

若缺少以上任一项，视为 bootstrap 证据不足，不能判定为完成。

## 说明性探针与实机执行的区别

- 当用户**真的发送裸消息 `start`** 时，agent 必须按固定流程实机执行，并输出上面的完整证据。
- 当外部探针只是在问“如果发送 `start` 会发生什么”时，允许回答流程与证据要求的摘要。
- 说明性响应至少要明确：四文件、proposal 状态清单、已跳过项、commit 列表、`PASS` / `FAIL` 这五类证据是实际执行时必须出现的。
- 若仓库中存在执行摘要 / 计划类 proposal，说明性响应也应明确它不会被跳过，而会在真实 `start` 中被逐文件列出并转成行动项。
- 说明性响应也应明确：真实 `start` 不是“读完就结束”，而是要进入 `edit code → run code/test → find bugs → edit code` 的闭环。
- 说明性响应不得把步骤摘要冒充为已经完成的实机执行结果。

## CEO 级 plan 的纳入方式

若 `proposal/INDEX.md` 中存在 CEO 级执行摘要（例如 `proposal_ceo_next_steps.md`），`start` 必须：

1. 在 proposal 状态清单里明确列出该文件名
2. 把其中的“下一步做什么”拆成待落地行动项
3. 对这些行动项进入代码落地与验证闭环，而不是只在 stand-up 里复述

例如当前 CEO plan 至少会被翻译成这三条执行范围：

1. 命令失灵时的兜底链路稳定性
2. 本地状态与提示规则的清晰度
3. 多主题命中时的固定优先级

## 禁止

- 不得把 `start` 当闲聊回复
- 不得跳过 proposal/INDEX.md 读取
- 不得只看最新一个 proposal 就直接开工
- 不得将多个 proposal 压进同一 commit
- 不得把已明确落地且无变更的 proposal 重新实现一遍

## 为什么

agent 进场第一件事应是把全部上下文进内存，再动手。`start` 是显式 bootstrap 入口，避免每次都用户手动粘贴 4 个文件路径；同时通过“先全量扫描、再只实现新增/未落地项”的流程，避免漏掉新 proposal，也避免重复返工已经落地的设计。
