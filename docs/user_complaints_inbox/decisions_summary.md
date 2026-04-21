# Inbox Review — Decisions Summary

**Run**: 2026-04-21 | **Artifact**: `prompt_pm.md` | **Iters**: 1 | **Total proposals**: 16

---

## ✅ Approved (11)

### 1. [MEDIUM] 输出加缺省处理分支
**问题**: 插件返回空或全是过期卡片时，PM 手册只说"去写 RFC"，低置信度情况无明确分支。
**建议**: 加显式低置信度分支，说明搜索无结果或全 stale 时的操作路径。
**决定**: **Approve** — agent 自行决定实现方式。

---

### 2. [MEDIUM] summon命令需要错误保护
**问题**: `claudefast -p "$(cat prompt_pm.md)"` 硬编码相对路径，文件不在当前目录直接崩溃，无错误提示。
**建议**: 加路径保护或 fallback。
**决定**: **Approve** — 改用 `/tmp/*.md` 绝对路径，`cat /tmp/prompt_pm.md`。

---

### 3. [MEDIUM] R预期加风险等级维度
**问题**: STAR 格式 R 段有时间/成本/影响面，Tech Lead 无法一眼判断是否需要 escalation。
**建议**: 加第四维：风险等级（低/中/高）。
**决定**: **Approve**。

---

### 4. [LOW] Header命令去掉share-review
**问题**: 手册头部列了 `/share-review`，实际工作流从未使用，新人会跑一个假命令。
**建议**: 删除 header 中的 `/share-review`。
**决定**: **Approve** — 清理假命令。

---

### 5. [MEDIUM] STAR建议引用格式统一
**问题**: STAR A 段引用 `card_id`，与 `/share-diff` 输出的卡片标识格式不一致。
**建议**: 统一引用来源格式。
**决定**: **Approve**。

---

### 6. [MEDIUM] 加plugin未装退化路径
**问题**: PM 手册末尾只提了一句"插件没装就降级"，没说降级后 PM 具体怎么操作。
**建议**: 明确降级路径。
**决定**: **Approve** — 有插件时用 `insights-share` wiki 回答；没有插件时让 agent 自行回答。

---

### 7. [HIGH] TechLead需plugin兜底分支
**问题**: PM 手册有插件挂了的应急措施，Tech Lead 手册没有，插件崩了 Tech Lead 直接卡住。
**建议**: 补 Tech Lead fallback 分支。
**决定**: **Approve** — fallback 走本地 `.cache`，加警告提示并拉取最新内容。

---

### 8. [MEDIUM] 统一summon机制定义
**问题**: 两份手册都默认 `/share-search` `/share-diff` 等命令存在，命令找不到时无任何处理。
**建议**: 定义命令缺失时的统一 summon fallback。
**决定**: **Approve** — 命令不存在时必须自动安装对应 skills/commands。

---

### 9. [LOW] 明确定义sig-fail符号语义
**问题**: `[share 🔒 sig-fail]` 出现在手册中，整个 repo 无任何设计文档解释其含义。
**建议**: 定义语义或删除。
**决定**: **Approve** — 直接删除这个未定义符号。

---

### 10. [MEDIUM] wiki搜索失败分层处理
**问题**: 手册只处理"搜不到"一种失败，实际有三种：插件未装、网络超时、manifest 损坏。
**建议**: 按三种原因分层处理，给不同引导。
**决定**: **Approve** — 加到手册里。

---

### 14. [HIGH] untriggered机制需设计确认
**问题**: 手册里出现 `untriggered` 标记机制，repo 中找不到对应实现，路由可能静默丢失。
**建议**: 实现该机制或删除引用。
**决定**: **Approve** — 从手册里删掉这个未实现的机制。

---

### 16. [LOW] wiki_tree路径约定需规范化
**问题**: `wiki_tree/<type>/<topic>.md` 路径格式只隐含在手册输出格式中，未写入正式设计文档。
**建议**: 上浮到 `proposal_wiki_card.md` 作为规范。
**决定**: **Approve**。

---

## ❌ Denied (5)

### 11. [MEDIUM] stale引用规则可操作化
**问题**: 手册说"别引用过期卡片"，但没定义多旧算过期，AI 可能默默引用 2 年前内容。
**建议**: 在 Hard Constraint 里加显式 stale 标注规则。
**决定**: **Deny** — 根本不应该禁止引用过期卡片。正确做法是给每张卡加时间戳，让读者自己判断。手册设计有问题，后续修手册。

---

### 12. [MEDIUM] RFC触发条件量化时间窗口
**问题**: 手册说搜到"旧卡"就触发 RFC，但"旧"没有定义（90天？1年？stale标？）。
**建议**: 定义时间窗口，如 90 天未更新视为过期。
**决定**: **Deny** — 根本没有"旧卡"这个概念。卡片无所谓新旧，该概念本身就是错误的，不应该存在于手册里。

---

### 13. [LOW] STAR的R段加风险标注模板
**问题**: STAR R 段现在是自由发挥，AI 可以随便写数字。
**建议**: 改为填空模板：`预计 [T+? weeks], 成本 [$?-?k], 影响 [? 个系统/团队]`。
**决定**: **Deny** — 不加模板约束，让 agent 自行决定输出格式。AI 自由发挥更好。

---

### 15. [MEDIUM] share-review命令需协议说明
**问题**: 管理员手册调用 `/share-review`，无文档说明是 slash command 还是 API，担心递归展开。
**建议**: 明确协议定义。
**决定**: **Deny** — `/share-review` 就是 plugin skill / slash command，两种形式都可以，不存在歧义问题。

---

## 统计

| 状态 | 数量 |
|------|------|
| ✅ Approved | 11 |
| ❌ Denied | 5 |
| 🔴 HIGH approved | 2 (7, 14) |
| 🟡 MEDIUM approved | 7 |
| 🟢 LOW approved | 2 |
