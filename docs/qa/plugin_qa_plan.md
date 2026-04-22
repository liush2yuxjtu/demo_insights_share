# Plugin /qa Plan — insights-share

> 本文件只出计划，不执行。user 审阅通过后再按 §6 执行路径开工。

## 0. 背景与范围

gstack 的 `/qa` 设计假定 **web app + URL**：浏览器导航 → 点击 → 截图 → health score。本仓 `insights-share` 是 **Claude Code plugin** + LAN `insightsd` daemon，**没有 web URL**，没有 DOM，浏览器 QA 链路不适配。

因此把 `/qa` 在本项目的语义重新定义为：

> 把 plugin 的 **user-facing surface**（slash / skill / hook / statusline / MCP / agent / daemon / 沙箱 demo / 完工证据）当成"页面"，逐个探针 → 收集证据 → 给 PASS/FAIL → 失败即修 + 原子 commit + 重跑。

本 plan **只列计划与判据**，不写任何新代码、不跑任何探针。

---

## 1. 必读上下文（已完成）

| 文件 | 关键约束 |
|------|----------|
| `proposal.md` | MVP 面向 PM；局域网；SILENT-IN-BACKGROUND；two skills: `insights-wiki-server`（管理员 only）+ `insights-wiki`（带 `--install`）|
| `README.md` | 仓名 `demo_insights_share` |
| `validation_AB.md` | A/B 对照用 `examples/COMMON_PROMPT.txt` 单一真源，prompt 文本必须一致，唯一变量是 skill/daemon 是否存在 |
| `validation.md` | S-T-A-R + tmux + `claude -p`；4 层 wiki 结构 `wiki_type_index → {type}/INDEX.md → wiki_item.md → raw jsonl/txt`；触发默认 `SILENT_AND_JUST_RUN`；MiniMax agentic 搜索 |
| `proposal/INDEX.md` | 7 份正式设计：conflict / wiki_card / statusline / plugin_design / rename_to_insights_share / ceo_next_steps / generation_latency |
| `plugins/insights-share/.claude-plugin/plugin.json` | v0.6.0-m7；M1–M6 完成；M7 部分；M8 pending；daemon 指向 `http://192.168.22.42:7821` |

项目 CLAUDE.md 额外规则（本 plan 必须遵守）：

- 根目录 `proposal.md` / `README.md` / `validation_AB.md` / `validation.md` 只读
- `docs/designs/user_design/` 整目录只读
- `start.demo.sh` = human-last-visible surface；feature 必在其中 self-verify
- `register-session` 建 tmux；`~/.claude/live_terminal/CURRENT` 存当前 session 名，镜像在 `<name>.log`
- tmux nested 必 `TMUX= tmux ...` 或 `unset TMUX`
- 任何 Write/Edit 后原子 commit
- 完工必跑 `claudefast -p "READ ONLY, ..."` finish flag judge
- CLAUDE.md 改动必跑 agent-judge 双探针

---

## 2. Plugin Surface Inventory（探针清单）

共 11 个 surface。每个 surface 一条探针，失败即 BLOCK /qa。

| # | Surface | 物理位置 | 探针契约 | PASS 判据 |
|---|---------|---------|---------|-----------|
| S1 | Plugin manifest | `plugins/insights-share/.claude-plugin/plugin.json` | `python3 -c "import json; m=json.load(open(...)); print(m['name'],m['version'])"` | 输出 `insights-share 0.6.0-m7` |
| S2 | Marketplace entry | `plugins/insights-share/.claude-plugin/marketplace.json` + 仓根 `.claude-plugin/marketplace.json` | 两边 JSON 可解析，含 `insights-share` plugin id | 两个文件都能 `json.load` 且 id 匹配 |
| S3 | Skill `insights-share` | `plugins/insights-share/skills/insights-share/SKILL.md` | SKILL.md 存在 + 前 40 行含 `name:` `description:` | frontmatter 齐全；description 与 plugin.json 一致 |
| S4 | Skill `insights-share-server` | `plugins/insights-share/skills/insights-share-server/SKILL.md` | 同 S3，且 description 含 `--start` `--ui` 两个 flag | flag 文档齐全 |
| S5 | Slash commands（5 个）| `plugins/insights-share/commands/{share-install,search,publish,review,diff}.md` | 5 个 md 都存在；每份头部有 description；每份可以读到完整 workflow | 5/5 可读；任一缺失即 FAIL |
| S6 | Agents（2 个）| `plugins/insights-share/agents/{share-curator,share-validator}.md` | 2 个 md 都存在；share-validator 描述发布前校验；share-curator 描述管理员 CRUD | 2/2 可读，职责清晰 |
| S7 | Hooks | `hooks/user-prompt-submit.sh` + `hooks/session-start.sh` | 两个 sh 都可执行；`bash -n` 语法通过 | chmod +x；`bash -n` exit 0 |
| S8 | Statusline | `statusline/insights_share_statusline.sh` | 在设定 `INSIGHTS_SHARE_URL` 与 `SHARE_STATUSLINE_NO_COLOR=1` 下直接跑；输出符合 `[share ✓ N/today]` 或 `[share 🔒 sig-fail]` 形态 | 非零退出码或乱码即 FAIL |
| S9 | MCP wiki-server | `plugins/insights-share/mcp/wiki-server.json` | JSON 可解析；声明 tools；指向 daemon | `json.load` 通过；tools 列表非空 |
| S10 | LAN daemon（insightsd）| `insights-share/demo_codes/insights_cli.py serve --port 7821` | `curl -sS http://127.0.0.1:7821/healthz` 200；`/insights?topic=database` 返回 `{"cards":[...]}` JSON | HTTP 200 + cards 数组非空可解析 |
| S11 | Sandbox demo（human-last-visible）| `start.demo.sh` | 在 `register-session live_demo` 内按 `TMUX= ` 起；跑完 7 stage；右 pane self-check 5 条全绿 | 左 pane guide 日志推进；右 pane 看到 skills 列表 + statusline preview + `self_check.sh` 所有 OK |

补充探针（由 `plugins/insights-share/scripts/self_check.sh` 覆盖）：

- manifest / marketplace / 两个 skill / UserPromptSubmit hook / SessionStart hook / `session_start_full_fetch.py` / statusline / MCP 配置 / 5 个 slash / 2 个 agent / 签名脚本
- 契约：每行一个组件，一条 `OK` / `MISSING` / `PARSE-FAIL`；只要有任一 MISSING → 非零退出 → /qa FAIL

---

## 3. 端到端回放（Skill 触发 + hook + daemon + statusline 同时验证）

**Scenario**: Bob 在 Claude Code 里提一个 postgres 连接池问题，skill 必须静默回灌命中 LAN 卡片。

| 步骤 | 动作 | 期望 |
|------|------|------|
| E1 | 进 `start.demo.sh` 的右 pane（沙箱 HOME）| 右 pane 完成 self-check，进入 claude REPL |
| E2 | 在 Claude 里发 `examples/COMMON_PROMPT.txt` 第 3 步的 checkout/postgres prompt | UserPromptSubmit hook 触发；`~/.cache/insights-share/manifest.json` 生成；命中卡片 id 注入 |
| E3 | `!cat ~/.cache/insights-share/manifest.json` | JSON 内含 `alice-pgpool-2026-04-10` 或同 topic 的 Good/Bad 卡片 |
| E4 | 观察 statusline | 由 `[share ✓ 0/today]` 递增为 `[share ✓ 1/today]` |
| E5 | Claude 回答里 | 明确引用了命中的卡片 id；未命中时明确写"未引用任何 LAN 卡片" |
| E6 | 左 pane guide 日志 | 按 `guide_loop.sh` 脚本推进到 done |

**A/B 门禁**（复用 `validation_AB.md` 契约）：

- 同一份 `COMMON_PROMPT.txt` 在 A（不装 skill）与 B（装 skill + daemon）两端 export
- 归一化后 prompt 文本必须完全一致 → A/B 差异只能来自 skill/daemon

---

## 4. Slash 命令独立回放

| 命令 | 场景 | PASS 判据 |
|------|------|-----------|
| `/share-install` | 首次安装 plugin | 校验 `.claude-plugin/` 结构；daemon URL 可达；skill 目录落盘 |
| `/share-search postgres pool` | 按关键词检索 LAN daemon | 返回 topic=database 下 Good/Bad 并列 top-k；无合并 |
| `/share-publish` | 发布一条新卡片 | 走 `share-validator` agent 校验 schema + label + topic 存在；daemon POST /insights 落盘 |
| `/share-diff database` | 按 topic 看并列 Good/Bad diff | 展示 applies_when / do_not_apply_when + raw_log 链接 |
| `/share-review database --admin` | 管理员 label_override / archive | 仅管理员 session 触发 share-curator agent；非管理员拒绝 |

每条命令跑完后核验 daemon 侧 wiki_tree 落盘状态（`wiki_tree/{topic}/{uuid}.md` + `raw/{uuid}.jsonl`）。

---

## 5. 前置条件（blocker）

开跑前必须全部满足：

1. **工作树清理**：`git status --porcelain` 为空（当前有 26+ 未提交文件，必须先按"编辑即原子 commit"规则分组原子 commit）
2. **沙箱依赖**：`tmux`、`claude` CLI、`python3`、`insights-share/demo_codes/.venv/bin/python` 存在
3. **端口**：`7821` 可用或已由外部 `insightsd` 占用
4. **认证**：`.env` 有真 `MINIMAX_TOKEN`，或 `~/.claude/.credentials.json` 订阅已登录
5. **register-session**：`~/.claude/live_terminal/CURRENT` 指向一个活 tmux session（若空则先跑 `.claude/skills/register-session/register-session.sh live_demo`）

---

## 6. 执行路径（按 CLAUDE.md 全链）

```text
┌─────────────────────────────────────────────────────────────┐
│ step 0  任务前必读四文件 + proposal/INDEX.md   ← 已完成     │
├─────────────────────────────────────────────────────────────┤
│ step 1  原子 commit 当前 26+ 个未提交文件                   │
│         - 按单一关注点分组（wiki_tree/general/m1-kb-*        │
│           一组；topics.json + database/INDEX.md 一组；...）  │
├─────────────────────────────────────────────────────────────┤
│ step 2  register-session live_demo                           │
│         .claude/skills/register-session/register-session.sh  │
│         → 产生 ~/.claude/live_terminal/live_demo.log 镜像    │
├─────────────────────────────────────────────────────────────┤
│ step 3  跑 S1–S10 文件级探针（非交互，<10 s）                │
│         → 任一 FAIL → 停 → 修 → 原子 commit → 重跑          │
├─────────────────────────────────────────────────────────────┤
│ step 4  在 live_demo tmux 里 TMUX= bash start.demo.sh        │
│         → 捕左 pane guide log + 右 pane self-check           │
│         → self_check.sh 全绿                                 │
├─────────────────────────────────────────────────────────────┤
│ step 5  在 start.demo.sh 右 pane Claude 里回放 §3 E1–E6      │
│         → statusline 递增 + manifest.json 命中 + cite 引用   │
├─────────────────────────────────────────────────────────────┤
│ step 6  逐 slash 回放 §4 的 5 条命令                         │
│         → daemon wiki_tree 落盘核验                          │
├─────────────────────────────────────────────────────────────┤
│ step 7  写 docs/finish_log/2026-04-22_plugin_qa.md           │
│         - 每条 surface PASS/FAIL                             │
│         - 每条回放的截图/日志路径                            │
│         - 收到的 bug → TODOS.md（deferred）或 原子 fix commit│
├─────────────────────────────────────────────────────────────┤
│ step 8  claudefast -p "READ ONLY, tell me what we have done  │
│         in recent commits and based on docs" 当 finish flag  │
│         → PASS / REFINE / FAIL                               │
│         → REFINE/FAIL 修 docs 重跑，最多 3 轮                │
│         → 仍 FAIL 升级 claude -p 托底                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 7. 失败恢复与 bug 回写

- **Surface 探针 FAIL** → 修对应文件 → 原子 commit `fix(qa): <surface> — <reason>` → 重跑该 surface 单探针 → 通过后重跑 self_check.sh
- **Scenario 回放 FAIL** → 保留沙箱日志到 `insights-share/validation/reports/deliverables/`；若 root cause 跨 surface → 进 `/investigate` 流程，不直接在 /qa 里硬修
- **WTF-likelihood 守门**（复用 gstack /qa 的自我调节原则）：每 5 次 fix 评估一次；reverts ≥ 1 或涉及 proposal 层改动 → STOP + 报告给用户
- **bug 回写**：`TODOS.md`（项目根，若无则新建）追加 entry，格式 `- [ ] [severity] <surface> — <repro> — found /qa <date>`

---

## 8. 明确不做

- ❌ 不改 `proposal.md` / `README.md` / `validation_AB.md` / `validation.md`
- ❌ 不改 `docs/designs/user_design/` 任何文件
- ❌ 不装 gstack browse 浏览器链路（无 web URL）
- ❌ 不改 CLAUDE.md（除非 /qa 发现规则本身缺失，否则不碰；若碰必跑 agent-judge 双探针）
- ❌ 不动 `wiki_tree/` 真实卡片（/share-publish 回放用沙箱 daemon 的临时 topic，不污染管理员看板）
- ❌ 不做 gstack `/qa` 的 WTF 自我调节外的其他自动修复（gstack health score、regression test 生成等不适配纯 CLI plugin）

---

## 9. 交付物

| 产物 | 路径 |
|------|------|
| Plan 本文件 | `docs/qa/plugin_qa_plan.md` |
| 探针结果 | `docs/finish_log/2026-04-22_plugin_qa.md`（step 7 产出）|
| start.demo.sh 日志副本 | `insights-share/validation/reports/deliverables/start_demo.latest.txt` |
| bug 列表 | `TODOS.md`（项目根）|
| finish flag judge 结果 | step 8 输出，落入 finish_log |

---

## 10. 审阅 checklist（交给用户）

- [ ] Surface inventory 11 条是否完整？有没有漏的 user-facing 面？
- [ ] §3 的 E1–E6 scenario 是否足够代表"真实 Bob 使用场景"？
- [ ] §4 的 5 条 slash 判据是否需要补强（比如：`/share-publish` 的 agent 校验链路要不要单独画出来）？
- [ ] §5 前置条件里的 26+ 文件原子 commit 策略是否接受？（是否希望先 review 这批未提交变更）
- [ ] §8 明确不做清单里是否有该加的？
- [ ] step 8 的 finish flag judge prompt 文本是否直接沿用 CLAUDE.md 的 `"READ ONLY, tell me what we have done in recent commits and based on docs"` 原句？
