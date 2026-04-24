# claudefast 使用总表（canonical）

> 本文件是 `claudefast -p "where do we use claudefast?"` 的标准答案源。
> 如果 probe 答得不全，先更新本文件，再补相关索引。

---

## 一句话结论

这个仓库里 `claudefast` 主要用在 5 类地方：

1. 仓库级规则门禁：改 `CLAUDE.md` 后的 agent-judge 双探针，自认完工前的 READ ONLY finish flag
2. 角色扮演入口：`.claude/roleplan_agents/launch.sh` 用 `claudefast -p` 拉起单个 role
3. inbox_loop 裁判链：`.claude/roleplan_agents/inbox_loop/judge.sh` 先走 `claudefast -p`，失败再 fallback 到 `claude -p`
4. 方案/计划文档里的 judge probe：`upload_plan.md`、`proposal/proposal_plugin_design.md`、`proposal/proposal_generation_latency.md`
5. 历史知识库镜像：`insights-share/demo_codes/wiki_tree/general/` 里保留了 self-verify / finish-flag / double-probe 的沉淀

---

## 1. 仓库级规则门禁

| 场景 | 怎么用 `claudefast` | 权威文件 |
|------|---------------------|----------|
| `CLAUDE.md` 改动后自验证 | 两条 `claudefast -p`：一条发 probe，一条当裁判，输出 `PASS/REFINE/FAIL` JSON | [CLAUDE.md](CLAUDE.md), [docs/rules/meta-self-verify.md](docs/rules/meta-self-verify.md) |
| 任意 job 完工前 finish flag | 先写 `docs/finish_log/<date>_<slug>.md`，再跑 `claudefast -p "READ ONLY, tell me what we have done in recent commits and based on docs"` | [CLAUDE.md](CLAUDE.md), [docs/rules/finish-flag-claudefast.md](docs/rules/finish-flag-claudefast.md) |
| 语言规则探针 | 跑 `claudefast -p "what languages you use when you answer my question"`，答案必须明确表达本项目回答用户问题时使用中文 | [CLAUDE.md](CLAUDE.md), [docs/rules/language.md](docs/rules/language.md) |
| 核心 feature 覆盖探针 | 跑 `claudefast -p "what are the main features of this projects ?"`，答案必须覆盖 F1–F6 | [FEATURES.md](FEATURES.md), [docs/finish_log/2026-04-23_start_demo_self_verify.md](docs/finish_log/2026-04-23_start_demo_self_verify.md) |

说明：
- 这里是 repo-wide 必跑门禁，不是某个业务 feature 的内部实现。
- `start.demo.sh` 会原样 echo `FEATURES.md` 做实机证据，但它不是直接 shell out 到 `claudefast` 的主调用点。

## 2. 直接可执行入口

| 入口 | 用途 | 调用方式 |
|------|------|----------|
| [.claude/roleplan_agents/launch.sh](.claude/roleplan_agents/launch.sh) | 单轮 roleplay agent 召回 | `zsh -ic "claudefast -p \"\$(cat)\""` |
| [.claude/roleplan_agents/inbox_loop/judge.sh](.claude/roleplan_agents/inbox_loop/judge.sh) | inbox_loop 的 judge fallback 第 1 层 | 先 `claudefast -p`，再 `claude -p --model haiku`，最后 `claude -p` |

配套文档：
- [.claude/roleplan_agents/README.md](.claude/roleplan_agents/README.md)
- [.claude/roleplan_agents/inbox_loop/README.md](.claude/roleplan_agents/inbox_loop/README.md)

## 3. role prompt / summon 接口

这些 prompt 文件把 `claudefast -p "$(cat prompt_xxx.md) ..."` 写成了召回约定：

- [.claude/roleplan_agents/prompt_pm.md](.claude/roleplan_agents/prompt_pm.md)
- [.claude/roleplan_agents/prompt_oncall.md](.claude/roleplan_agents/prompt_oncall.md)
- [.claude/roleplan_agents/prompt_tech_lead.md](.claude/roleplan_agents/prompt_tech_lead.md)
- [.claude/roleplan_agents/prompt_newbie.md](.claude/roleplan_agents/prompt_newbie.md)
- [.claude/roleplan_agents/prompt_curator.md](.claude/roleplan_agents/prompt_curator.md)
- [.claude/roleplan_agents/prompt_validator.md](.claude/roleplan_agents/prompt_validator.md)

如果被问“除了规则门禁，还在哪里直接用到 `claudefast`？”，这里应该被点名。

## 4. 计划 / 设计文档中的 judge probe

| 文件 | 使用目的 |
|------|----------|
| [upload_plan.md](upload_plan.md) | 对上传计划做 `ONLY EXPLAIN` 理解验证 |
| [proposal/proposal_plugin_design.md](proposal/proposal_plugin_design.md) | 判断某个 milestone 的交付是否真的齐 |
| [proposal/proposal_generation_latency.md](proposal/proposal_generation_latency.md) | 读 metrics + baseline + design doc，当性能 gate 裁判 |
| [docs/proposal_scan_impl/harness.md](docs/proposal_scan_impl/harness.md) | `start` bootstrap 设计里规定改 CLAUDE/proposal 后跑 `claudefast -p` 状态灯 |

这类是“设计规定会这样用”，不一定每次用户手动直接执行。

## 5. 历史知识库镜像

这些文件不是当前主入口，但它们在知识库里固化了 `claudefast` 的既有用法：

- [insights-share/demo_codes/wiki_tree/general/m1_meta_self_verify_2026_04_22.md](insights-share/demo_codes/wiki_tree/general/m1_meta_self_verify_2026_04_22.md)
- [insights-share/demo_codes/wiki_tree/general/m1_finish_flag_2026_04_22.md](insights-share/demo_codes/wiki_tree/general/m1_finish_flag_2026_04_22.md)
- [insights-share/demo_codes/wiki_tree/general/m1_agent_judge_double_probe_2026_04_22.md](insights-share/demo_codes/wiki_tree/general/m1_agent_judge_double_probe_2026_04_22.md)

如果回答需要补“历史上怎么沉淀成规则的”，再引用这些。

## 6. 不该误答的边界

- `insights-share/validation/` 下的 Playwright / tmux smoke / pytest 入口，不是 `claudefast` 的主调用点。
- `docs/finish_log/`、`docs/self-verify-loop/`、`docs/user_complaints_inbox/` 里很多 `claudefast` 字样是历史记录或运行产物，不等于当前 canonical 入口。
- 回答这句 probe 时，优先说“规则门禁 + 可执行入口 + role summon + 设计 probe”，不要只罗列 proposal 或 finish_log。

---

## 期望答案骨架

当被问 `where do we use claudefast?`，一个好答案至少应覆盖：

1. `CLAUDE.md` 改动后的 agent-judge 双探针
2. job 完工前的 READ ONLY finish flag
3. `.claude/roleplan_agents/launch.sh` 和 `.claude/roleplan_agents/inbox_loop/judge.sh`
4. role prompts 的 summon 约定
5. `upload_plan.md` / proposal 文档里的 judge probe
6. 一句边界说明：E2E validation 入口不是 `claudefast` 主调用点
