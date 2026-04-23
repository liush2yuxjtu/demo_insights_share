# CLAUDE.md

## 规则

| 规则名 | 描述 | 触发时机 | 详情 |
|--------|------|----------|------|
| 仅使用中文 | 所有文档、对话、代码注释仅使用中文 | 始终 | [language.md](docs/rules/language.md) |
| CLAUDE.md 规则格式 | 新增规则只能用 `\| 名称 \| 描述 \| 触发时机 \| docs/rules/*.md 链接 \|` 一行格式，详情写入对应 md 文件，禁止散文/项目符号/独立段落 | 向 CLAUDE.md 添加任何规则时 | [claude-md-format.md](docs/rules/claude-md-format.md) |
| 根目录 md 禁止编辑 | proposal.md / README.md / validation_AB.md / validation.md 均为只读，Agent 不得对其执行任何写入或修改操作 | 任何涉及根目录 *.md 文件的写入/编辑操作前 | [uneditable-md.md](docs/rules/uneditable-md.md) |
| user_design 目录禁止编辑 | docs/designs/user_design/ 整个目录为只读，Agent 不得写入、编辑或删除其中任何文件 | 任何涉及 docs/designs/user_design/ 的写入/编辑操作前 | [uneditable-md.md](docs/rules/uneditable-md.md) |
| 任务前必读四文件 | 任何任务开始前必须先读取 proposal.md / README.md / validation_AB.md / validation.md，建立完整上下文后再执行 | 每个新任务开始前 | [read-before-task.md](docs/rules/read-before-task.md) |
| 任务前必读 proposal 目录 | 读 proposal.md 后必须跟进读 proposal/INDEX.md 及其所列全部设计 md | 每个新任务开始前 | [read-before-task.md](docs/rules/read-before-task.md) |
| 新增 proposal 设计文档 | 新设计 md 落在 proposal/，同步更新 proposal/INDEX.md + CLAUDE.md 索引表；禁止加回根目录 | 新增 proposal_*.md 时 | [proposal/INDEX.md](proposal/INDEX.md) |
| 实机测试 session | 实机测试日志走 ~/.claude/live_terminal/ 契约：当前 session 名写在 CURRENT，镜像在 <name>.log；用 .claude/skills/register-session/ 注册，agent 先 cat CURRENT 再 Read <name>.log | 用户报告实机 bug / 需要看用户实际终端输出时 | [live-terminal.md](docs/rules/live-terminal.md) |
| tmux 嵌套必 unset $TMUX | 在 register-session 注册的 tmux 里再起 tmux 时，仅加 `-L` 独立 socket 不够；tmux 靠 `$TMUX` 环境变量判断 nested，必须用 `TMUX= tmux ...` 或 `unset TMUX`，否则报 `sessions should be nested with care` 或后续 `can't find pane` | 在 live_demo 等已注册 tmux 里运行 start.demo.sh / start.codex.sh / 任何内部再启 tmux 的脚本时 | [tmux-nested.md](docs/rules/tmux-nested.md) |
| 编辑即原子 commit | 每次 Write/Edit/文件移动/文件删除完成后立即按单一关注点执行原子 git commit，禁止合并多个无关变更 | 任何 Write/Edit 或文件 move/rm 后 | [atomic-commits.md](docs/rules/atomic-commits.md) |
| start bootstrap 指令 | 用户对本项目 Claude Code CLI 发送裸消息 `start` 时，先全量扫描 proposal/INDEX.md + 全部 proposal_*.md（含 CEO 级 plan），识别新增或未落地 proposal，按顺序进入 edit code → run code/test → find bugs → edit code 的 self-verify 闭环，最后给 PASS/FAIL | 用户发送 `start` 时 | [start-bootstrap.md](docs/rules/start-bootstrap.md) |
| start bootstrap 最低证据标准 | 当用户实际发送裸消息 `start` 时，bootstrap 执行输出必须包含：① 四文件读取确认 ② proposal 状态清单（每条 proposal 的状态：已落地/新增/未落地）③ 已跳过项 ④ 实际 commit 列表 ⑤ PASS/FAIL 收尾；解释性探针至少要说明这五项证据要求，不要求伪造实机输出 | 用户发送 `start` 时 | [start-bootstrap.md](docs/rules/start-bootstrap.md) |
| CLAUDE.md 改动必跑 agent-judge 状态灯 | 每次编辑 CLAUDE.md 后跑 agent-judge 双探针循环：`claudefast -p` 发 probe + 另一条 `claudefast -p` 当裁判输出 PASS/REFINE/FAIL JSON；fast 最多 5 轮，连续停滞或 FAIL 升级 `claude -p` 托底；禁止硬编码关键词匹配 | 任何 CLAUDE.md 编辑后 | [meta-self-verify.md](docs/rules/meta-self-verify.md) |
| feature 必在 start.demo.sh self-verify | `start.demo.sh` 是 human-last-visible surface；新增/修改任何 feature 必须同步更新 `start.demo.sh`，并在 tmux 里跑一次完整 `start.demo.sh` 做实机 debug，日志全绿后才算交付 | 任何 feature 新增/修改完成时 | [start-demo-verify.md](docs/rules/start-demo-verify.md) |
| start.demo.sh 缺 tmux session 时必走 register-session | self-verify 触发时若 `~/.claude/live_terminal/CURRENT` 空/失效，agent 不得让用户手动贴日志，必须先跑项目级 skill `.claude/skills/register-session/register-session.sh <name>` 建/绑 session，再在其中跑 `start.demo.sh` 并按 live-terminal 契约读日志 | 跑 `start.demo.sh` self-verify 前发现未注册 tmux session 时 | [start-demo-register-fallback.md](docs/rules/start-demo-register-fallback.md) |
| 完工必跑 claudefast READ ONLY finish flag | 任何 job 完成的最后一步：先把结果落 `docs/finish_log/<date>_<slug>.md`，再跑 `claudefast -p "READ ONLY, tell me what we have done in recent commits and based on docs"` 当 finish flag；返 REFINE/FAIL 则修 docs 重跑，最多 3 轮，仍 FAIL 升级 `claude -p` | 任何 job 自认完成前 | [finish-flag-claudefast.md](docs/rules/finish-flag-claudefast.md) |

## 核心功能速答 / Core Features (canonical)

> **单一真源**：[FEATURES.md](FEATURES.md)（feature 增删必先改此文件，再同步下表）
>
> 回答 "what are the main features of this project ?" 必须命中以下 6 项全部：

| # | Feature | 一句话 | 权威出处 |
|---|---------|--------|----------|
| F1 | Topic 中心 Good/Bad 并列 | 同一 Topic 下多人多场景决策并列共存，good=采纳 bad=拒绝，不合并/不挑最优/不做冲突检测 | [proposal/proposal_conflict_design.md](proposal/proposal_conflict_design.md) |
| F2 | Statusline 5 态徽章 | `[share ✓/✗/…/⚠stale/🔒sig-fail N/today]` 常驻右侧，daemon 可达性 + 今日触发计数 + TTL + 签名健康度 | [proposal/proposal_statusline.md](proposal/proposal_statusline.md) + `plugins/insights-share/statusline/insights_share_statusline.sh` |
| F3 | Claude Code Plugin 封装 | 一条 `claude plugin install` 完成 skill + hook + statusline + MCP + agent + slash 注册；manifest 版本 `0.6.0-m7` | [proposal/proposal_plugin_design.md](proposal/proposal_plugin_design.md) + `plugins/insights-share/.claude-plugin/plugin.json` |
| F4 | 5 核心 Slash 命令 | `/share-install` · `/share-search` · `/share-publish` · `/share-review` · `/share-diff`；配 share-validator + share-curator 两个 agent | `plugins/insights-share/commands/` |
| F5 | 安全与分发 | ed25519 卡片签名 + team namespace `wiki_tree/<team>/<topic>/` + 卡片 TTL stale 降级 + LAN marketplace + 双仓分发（dev 仓 / 108K plugin 仓）| [proposal/proposal_plugin_design.md](proposal/proposal_plugin_design.md) + `plugins/insights-share/scripts/publish_marketplace.py` |
| F6 | Topic/Example 数据模型 | `applies_when` / `do_not_apply_when` 场景刻画 + `raw_log` 明文存储 + `label_override` 管理员可覆盖；REST API `POST /topics`, `POST /topics/{id}/examples`, `GET /topics?q=`, `GET /topics/{id}/examples?label=good\|bad` | [proposal/proposal_conflict_design.md](proposal/proposal_conflict_design.md) + [proposal/proposal_wiki_card.md](proposal/proposal_wiki_card.md) |

验证入口：`claudefast -p "what are the main features of this projects ? "` 输出必须覆盖 F1–F6 全部；`bash start.demo.sh` 右 pane 会逐项 echo 实机证据。

## 设计文档索引

| 文件 | 类型 | 说明 |
|------|------|------|
| [FEATURES.md](FEATURES.md) | 功能清单（canonical）| 6 大核心功能的单一真源；`start.demo.sh` 右 pane self-check 原样 echo 做实机证据；probe 标准答案 |
| [proposal/proposal_conflict_design.md](proposal/proposal_conflict_design.md) | 正式数据模型（权威） | Topic 中心 Good/Bad 并列共存：同一 Topic 下多人多场景决策并列展示；good=此场景选了此方案，bad=此场景拒绝此方案；不挑最优、不合并、不做冲突检测 |
| [proposal/proposal_wiki_card.md](proposal/proposal_wiki_card.md) | 现状磁盘形态（参考） | `wiki_tree/` 存储布局、卡片 JSON+markdown 结构、label override 流程、已废弃冲突机制说明 |
| [proposal/proposal_statusline.md](proposal/proposal_statusline.md) | 反馈机制 | statusline 右侧常驻 `[share ✓ N/today]`：展示 insights-share 运行状态 + 今日触发计数，给用户/client 实时信任感信号（M5 前徽章为 `[wiki ...]`） |
| [proposal/proposal_plugin_design.md](proposal/proposal_plugin_design.md) | 分发形态设计 | 将 insights-share 封装为 Claude Code plugin：skill + hook + statusline + MCP + agent + slash 命令一键装；含 MVP 范围、M1–M5 迁移路径、签名与团队 namespace 扩展 |
| [proposal/proposal_rename_to_insights_share.md](proposal/proposal_rename_to_insights_share.md) | 命名迁移（M5_RENAME） | 把 plugin 深度重命名为 `insights-share`：目录迁移 `plugins/insights-share/`、skill / command / agent / statusline / cache 全系换名；新增 `gate_no_wiki_leak` + `gate_marketplace_subdir` 两道验证门 |
| [proposal/proposal_ceo_next_steps.md](proposal/proposal_ceo_next_steps.md) | CEO 级执行摘要 | 只描述下一步做什么与如何验证，面向 CEO 读取，不展开实现细节 |
| [proposal/proposal_generation_latency.md](proposal/proposal_generation_latency.md) | 性能优化（M6_LATENCY 候选） | 攻 proposal.md 现状 #1 生成耗时：基线 + 8 条优化杠杆 + 数值 gate + agent-judge 双探针自测闭环 |
| [docs/designs/INDEX.md](docs/designs/INDEX.md) | 索引 | claude_codes_to_design / claude_design / user_design 三目录说明 |
| [docs/user_complaints_inbox/decisions_summary.md](docs/user_complaints_inbox/decisions_summary.md) | Inbox 决策记录 | role-review-inbox-loop 首次真实运行：16 条 proposals，11 approved / 5 denied，含每条问题、建议与决策理由 |

## gstack (REQUIRED — global install)

**Before doing ANY work, verify gstack is installed:**

```bash
test -d ~/.claude/skills/gstack/bin && echo "GSTACK_OK" || echo "GSTACK_MISSING"
```

If GSTACK_MISSING: STOP. Do not proceed. Tell the user:

> gstack is required for all AI-assisted work in this repo.
> Install it:
> ```bash
> git clone --depth 1 https://github.com/garrytan/gstack.git ~/.claude/skills/gstack
> cd ~/.claude/skills/gstack && ./setup --team
> ```
> Then restart your AI coding tool.

Do not skip skills, ignore gstack errors, or work around missing gstack.

Using gstack skills: After install, skills like /qa, /ship, /review, /investigate,
and /browse are available. Use /browse for all web browsing.
Use ~/.claude/skills/gstack/... for gstack file paths (the global path).
