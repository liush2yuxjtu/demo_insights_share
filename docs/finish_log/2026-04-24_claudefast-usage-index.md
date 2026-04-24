# Finish Log — claudefast 使用总表与 probe 对齐

日期：2026-04-24
触发：用户要求“update docs until `claudefast -p "where do we use claudefast?"` return good answers”
关联：
- [CLAUDEFAST_USAGE.md](../../CLAUDEFAST_USAGE.md)
- [CLAUDE.md](../../CLAUDE.md)
- [docs/rules/meta-self-verify.md](../rules/meta-self-verify.md)
- [docs/rules/finish-flag-claudefast.md](../rules/finish-flag-claudefast.md)

## 本轮改动

| 文件 | 改动 | 目的 |
|---|---|---|
| [CLAUDEFAST_USAGE.md](../../CLAUDEFAST_USAGE.md) | 新增顶层 canonical 文档 | 给 `where do we use claudefast?` 提供单一真源，显式分桶 |
| [CLAUDE.md](../../CLAUDE.md) | 在设计文档索引新增一行 | 让 probe 更容易先命中这份总表 |

## canonical 分桶

`CLAUDEFAST_USAGE.md` 现在把 `claudefast` 的使用分成 6 块：

1. 仓库级规则门禁：`CLAUDE.md` 改动后的 agent-judge 双探针、job 完工前 READ ONLY finish flag、feature 覆盖探针
2. 直接可执行入口：`.claude/roleplan_agents/launch.sh`、`.claude/roleplan_agents/inbox_loop/judge.sh`
3. role prompt summon 约定：`prompt_pm.md` / `prompt_oncall.md` / `prompt_tech_lead.md` / `prompt_newbie.md` / `prompt_curator.md` / `prompt_validator.md`
4. 计划 / 设计文档中的 judge probe：`upload_plan.md`、`proposal/proposal_plugin_design.md`、`proposal/proposal_generation_latency.md`、`docs/proposal_scan_impl/harness.md`
5. 历史知识库镜像：`insights-share/demo_codes/wiki_tree/general/` 下的 self-verify / finish-flag / double-probe 卡片
6. 不该误答的边界：`insights-share/validation/` 的 Playwright / tmux smoke / pytest 入口不是 `claudefast` 主调用点

## probe 验证

### A. 直接 probe

命令：

```bash
claudefast -p "where do we use claudefast?"
```

结果：回答已覆盖以下要点

- 仓库级规则门禁
- `.claude/roleplan_agents/launch.sh`
- `.claude/roleplan_agents/inbox_loop/judge.sh`
- role prompt summon 约定
- `upload_plan.md` / proposal judge probe
- E2E validation 不是主调用点

### B. agent-judge 自验证

因本轮编辑了 `CLAUDE.md`，按规则追加跑双探针校验。judge 返回：

```json
{"verdict":"PASS","reason":"六项 Required Buckets 全部命中：① CLAUDE.md edit -> agent-judge 双探针 ② job finish -> READ ONLY finish flag ③ .claude/roleplan_agents/launch.sh 和 inbox_loop/judge.sh 可执行入口 ④ role prompt summon 约定 ⑤ proposal/upload_plan.md 等 judge probe ⑥ E2E validation 非主调用点边界说明","missing":[]}
```

## 结论

本轮目标已达成：`claudefast -p "where do we use claudefast?"` 不再只回 proposal/finish-log 碎片，而是先按 canonical 文档输出“规则门禁 + 可执行入口 + summon + 设计 probe + 边界说明”。
