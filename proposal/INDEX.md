# Proposal 设计文档索引

本目录存放 proposal 正式设计文档。任何任务开始前 agent 必须先读完本 INDEX 及所列全部 md。

## 文档清单

| 文件 | 类型 | 说明 |
|------|------|------|
| [proposal_conflict_design.md](proposal_conflict_design.md) | 正式数据模型（权威） | Topic 中心 Good/Bad 并列共存：同一 Topic 下多人多场景决策并列展示；good=此场景选了此方案，bad=此场景拒绝此方案；不挑最优、不合并、不做冲突检测 |
| [proposal_wiki_card.md](proposal_wiki_card.md) | 现状磁盘形态（参考） | `wiki_tree/` 存储布局、卡片 JSON+markdown 结构、label override 流程、已废弃冲突机制说明 |
| [proposal_statusline.md](proposal_statusline.md) | 反馈机制 | statusline 右侧常驻 `[share ✓ N/today]`：展示 insights-share 运行状态 + 今日触发计数，给用户/client 实时信任感信号（M5 前徽章为 `[wiki ...]`） |
| [proposal_plugin_design.md](proposal_plugin_design.md) | 分发形态设计 | 将 insights-share 封装为 Claude Code plugin：skill + hook + statusline + MCP + agent + slash 命令一键装；含 MVP 范围、M1–M5 迁移路径、签名与团队 namespace 扩展 |
| [proposal_rename_to_insights_share.md](proposal_rename_to_insights_share.md) | 命名迁移（M5_RENAME） | 把 plugin 深度重命名为 `insights-share`：`insights-share/plugin/` → `plugins/insights-share/`、skill / command / agent / statusline / cache 全系换名；新增 `gate_no_wiki_leak` + `gate_marketplace_subdir` 两道验证门 |
| [proposal_ceo_next_steps.md](proposal_ceo_next_steps.md) | CEO 级执行摘要 | 只保留下一步推进重点与 CEO 级验收口径：兜底稳定性、状态清晰度、多主题决策一致性、端到端可演示 |
| [proposal_generation_latency.md](proposal_generation_latency.md) | 性能优化（M6_LATENCY 候选） | 攻 proposal.md 现状 #1 生成耗时：基线 + 8 条优化杠杆（cache/layer-skip/early-exit/async-hook/warm/embedding）+ 数值 gate + agent-judge 双探针自测闭环 |

## 新增规则

新增 proposal md 文件时：

1. 文件落盘在 `proposal/` 目录内，命名 `proposal_<topic>.md`
2. 在本 INDEX 表格新增一行：`| [文件名](文件名) | 类型 | 说明 |`
3. 在根 `CLAUDE.md` → "设计文档索引" 同步新增一行
4. 根 `proposal.md` 的 `Proposal 设计文档目录` 节只指向本 INDEX，无需每次改 proposal.md
