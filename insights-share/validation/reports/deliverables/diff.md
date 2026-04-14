# WITH vs WITHOUT 对照差异分析

实验时间：2026-04-14 09:51–09:54
实验脚本：`insights-share/validation/tmux_with_without.sh`
固定 prompt：`Our checkout API is timing out, postgres is rejecting new connections during the lunch spike`

两轮均通过 `tmux send-keys` 发起 `claude -p`，等待 60 秒后用 `tee` + `sed` 去 ANSI 落盘。
WITHOUT 轮跑前先把 `~/.claude/skills/insights-wiki` 临时移除；
WITH 轮跑前从 `insights-share/demo_codes/.claude/skills/insights-wiki/` 拷回。

## 体量对比

| 指标 | WITHOUT | WITH | 说明 |
|---|---|---|---|
| 字节 | 3018 | 1962 | WITH 更短 35%（直击要害，不再罗列通用诊断） |
| 行数 | 109 | 64 | WITH 跳过了"先排查再修"的通用模板 |
| 词数 | 291 | 175 | WITH 没有生成无关的多套修复方案 |

## 关键词命中（grep -ci）

| 关键词 | WITHOUT | WITH | 含义 |
|---|---|---|---|
| `alice` | 0 | **3** | WITH 引用了 wiki 卡片作者 |
| `2026-04-10` | 0 | **1** | WITH 命中 wiki 中的具体事故日期 |
| `confidence` | 0 | **1** | WITH 引用了 card 的置信度字段（0.82） |
| `do_not_apply` | 0 | **1** | WITH 显式提醒 card 的反向适用边界 |
| `idle_in_transaction` | 0 | **2** | WITH 直接给出 wiki 中提到的精确超时参数 |
| `pgpool` | 1 | 1 | WITH 是 `alice_pgpool.json`（卡片名），WITHOUT 是泛指 |
| `PgBouncer` | 3 | 3 | 通用关键词，两轮都会涉及 |
| `insight` / `wiki` | 0 | 0 | 模型不会照抄"insight/wiki"字面，要看具体内容 |

## 内容差异定性

**WITHOUT 轮的开场白**：
> 这个项目里没有 checkout 或 PostgreSQL 相关代码。你描述的是一个生产故障场景，我直接给出诊断步骤和修复方案。

— 模型只能给通用 SOP：罗列 `pg_stat_activity` 三段查询、给四种语言/框架的连接池配置示例、最后反问"你需要提供哪些信息"。属于"教科书答案"。

**WITH 轮的开场白**：
> 这个症状和 `alice_pgpool.json` 里记录的 2026-04-10 事故完全吻合——连接槽耗尽 + 午高峰爆发。根因是某个 worker 持有长期 idle-in-transaction 连接没释放，导致连接池被榨干。

— 模型直接定位到本团队历史 card：
1. 引用具体卡片名 `alice_pgpool.json`
2. 引用事故日期 `2026-04-10`
3. 给出 wiki 中记录的具体止血参数 `idle_in_transaction_session_timeout = '30s'`
4. 注明 `confidence 0.82` 与 `do_not_apply_when: session pooling mode` 的反向适用边界
5. 跳过通用诊断，直接给"立即止血 → 根本修复 → 验证恢复"三段式 actionable 方案

## 结论

WITH 轮在**字数减少 35%** 的同时，**信息密度显著上升**：
- 引用了 4 个 WITHOUT 完全不会出现的本地 wiki 专有名词（alice / 2026-04-10 / confidence / do_not_apply）
- 给出的修复方案是"按本团队既往经验"的具体参数，而非通用模板
- 显式声明了反向适用条件，避免在 session pooling 场景下误用

这证明 `insights-wiki` skill 一旦在 `~/.claude/skills/` 注册，Claude Code 会在收到匹配主题的问题时**自动调用**并将本地 card 内容融入回答。Demo 的核心价值（"局域网集体智慧自动注入"）通过本对照实验得到证实。
