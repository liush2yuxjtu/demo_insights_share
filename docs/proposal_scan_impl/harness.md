# Harness

**Generated:** 2026-04-21 13:23:05
**Claude Root:** `/Users/m1/.claude`

## Source Coverage

- History file: `/Users/m1/.claude/history.jsonl`
- Project transcripts root: `/Users/m1/.claude/projects`
- Scanned recent project transcript files: 60
- Matched snippets collected: 40

## Keyword Summary

- `skill`: 513
- `agents.md`: 490
- `loop`: 288
- `agent team`: 218
- `claude.md`: 214
- `codex`: 207
- `agent teams`: 199
- `claude code`: 196
- `hook`: 177
- `remote`: 158
- `workflow`: 156
- `plan.md`: 140

## Candidate Harness Patterns

- 采用 research.md → plan.md → report.md 的文档链路，并把每轮产物放进 docs/<topic>/。
- 在工作流结束点追加确定性的后处理钩子，而不是依赖人工补记。
- 把长期约束写进 AGENTS.md / CLAUDE.md，把一次性执行细节留给 skill。
- 并行 worker 只写各自中间产物，主线程最后做融合与总报告。
- 把重复出现的 workflow / harness 指令沉淀为可复用 skill 与 helper scripts。
- 把会话状态落到文件系统工件中，让下一轮和外部编排器可扫描、可恢复。

## Recommended Reusable Hooks

- 结束后自动生成 review.md，检查 plan/report 一致性。
- 结束后自动生成 harness.md，把会话里高频编排方式沉淀成规则。
- 若下一轮需要复盘，优先读取 review.md 与 harness.md，而不是只看 report.md。

## Evidence Snippets

- `2026-04-21T05:21:25.871Z` `/Users/m1/.claude/projects/-Users-m1-projects-demo-insights-share/71e70425-c7ec-4367-93cb-d2aa4e449478.jsonl`
  你是规则落地裁判。请判断下面这段响应是否体现了 CLAUDE.md 里 'start bootstrap 指令' 规则的意图（bootstrap 读四文件 + proposal/INDEX.md + 全量扫描全部 proposal + 识别新增/未落地 proposal + 只对这些项逐条实现 + self-verify + PASS/FAIL 收尾）。 响应: <<< 裸消息 `start` 触发 bootstrap 流程： 1. **读四文件** — `proposal.md` / `README.md` / `validation_AB.md` / `validation.md` 2. **读 proposal 目录** — 
- `2026-04-21T05:21:04.608Z` `/Users/m1/.claude/projects/-Users-m1-projects-demo-insights-share/7bdeb3f3-7346-4918-aeb8-de93fc1e906e.jsonl`
  你是规则落地裁判。请判断下面这段响应是否体现了 CLAUDE.md 里 'start bootstrap 指令' 规则的意图（bootstrap 读四文件 + proposal/INDEX.md + 全量扫描全部 proposal + 识别新增/未落地 proposal + 只对这些项逐条实现 + self-verify + PASS/FAIL 收尾）。 响应: <<< 裸消息 触发 bootstrap 流程： 1. **读四文件** — / / / 2. **读 proposal 目录** — + 全部 3. **全量扫描** — 输出每个 proposal 状态（已落地 / 新增 / 未落地）+ 关键交付物 4. **实现** 
- `2026-04-21T05:20:42.701Z` `/Users/m1/.claude/projects/-Users-m1-projects-demo-insights-share/9144e5d3-5e79-4a72-8bef-8f1a0135fe3a.jsonl`
  裸消息 `start` 触发 bootstrap 流程： 1. **读四文件** — `proposal.md` / `README.md` / `validation_AB.md` / `validation.md` 2. **读 proposal 目录** — `proposal/INDEX.md` + 全部 `proposal_*.md` 3. **全量扫描** — 输出每个 proposal 状态（已落地 / 新增 / 未落地）+ 关键交付物 4. **实现** — 只对新增/未落地项逐条落地，已落地项跳过 5. **自验证** — 改 CLAUDE.md/proposal 后跑 `claudefast -p` 双探针状态灯
- `2026-04-21T05:20:38.113Z` `/Users/m1/.claude/projects/-Users-m1-projects-demo-insights-share/9144e5d3-5e79-4a72-8bef-8f1a0135fe3a.jsonl`
  1 # `start` Bootstrap 指令 2 3 ## 规则 4 5 在本项目里用户对 Claude Code CLI 发送 **裸消息 `start`** 时，agent 必须把它当作项目引导指令，而非普通对话，按下面固定流程执行。该流程要求 **先全量扫描现有 proposal 集合，再从中识别新增或未落地 proposal，并只对这些项进入实现**；已落地项必须显式标记，不得重复返工。 6 7 ## 触发条件 8 9 - 用户向本项目里的 Claude Code CLI 发送消息 `start`（或 `START` / `Start` 大小写不敏感） 10 - 消息只有这一个 token，无附加语义 11 12 ## 
- `2026-04-21T05:20:38.110Z` `/Users/m1/.claude/projects/-Users-m1-projects-demo-insights-share/9144e5d3-5e79-4a72-8bef-8f1a0135fe3a.jsonl`
  1 # Proposal 设计文档索引 2 3 本目录存放 proposal 正式设计文档。任何任务开始前 agent 必须先读完本 INDEX 及所列全部 md。 4 5 ## 文档清单 6 7 | 文件 | 类型 | 说明 | 8 |------|------|------| 9 | [proposal_conflict_design.md](proposal_conflict_design.md) | 正式数据模型（权威） | Topic 中心 Good/Bad 并列共存：同一 Topic 下多人多场景决策并列展示；good=此场景选了此方案，bad=此场景拒绝此方案；不挑最优、不合并、不做冲突检测 | 10 | [propo
- `2026-04-21T05:20:28.421Z` `/Users/m1/.claude/projects/-Users-m1-projects-demo-insights-share/9144e5d3-5e79-4a72-8bef-8f1a0135fe3a.jsonl`
  what would happen if we say to claude code CLI in this project 'start'
- `2026-04-21T05:19:48.426Z` `/Users/m1/.claude/projects/-Users-m1-projects-demo-insights-share/fdb4560b-a93a-4c20-b04a-50a6387991a7.jsonl`
  你是规则落地裁判。请判断下面这段响应是否体现了 CLAUDE.md 里 'start bootstrap 指令' 规则的意图（bootstrap 读四文件 + proposal/INDEX.md + 全量扫描全部 proposal + 识别新增/未落地 proposal + 只对这些项逐条实现 + self-verify + PASS/FAIL 收尾）。 响应: <<< "start" 是 bootstrap 指令。触发固定流程： 1. 读 `proposal.md` / `README.md` / `validation_AB.md` / `validation.md` 2. 读 `proposal/INDEX.md` + 全部 
- `2026-04-21T05:19:42.668Z` `/Users/m1/.claude/projects/-Users-m1-projects-demo-insights-share/2bc2c885-83de-4156-902d-2e66c5fcdab4.jsonl`
  "start" 是 bootstrap 指令。触发固定流程： 1. 读 `proposal.md` / `README.md` / `validation_AB.md` / `validation.md` 2. 读 `proposal/INDEX.md` + 全部 `proposal_*.md` 3. 全量扫描，输出每个 proposal 状态（已落地 / 新增 / 未落地） 4. 只实现 `新增` / `未落地` 的 proposal，已落地的不重复返工 5. 每次改 CLAUDE.md/proposal 后跑 `claudefast -p` 状态灯自验证 6. 输出 `PASS` / `FAIL` + 状态清单 + commit
- `2026-04-21T05:19:37.656Z` `/Users/m1/.claude/projects/-Users-m1-projects-demo-insights-share/2bc2c885-83de-4156-902d-2e66c5fcdab4.jsonl`
  1 # `start` Bootstrap 指令 2 3 ## 规则 4 5 在本项目里用户对 Claude Code CLI 发送 **裸消息 `start`** 时，agent 必须把它当作项目引导指令，而非普通对话，按下面固定流程执行。该流程要求 **先全量扫描现有 proposal 集合，再从中识别新增或未落地 proposal，并只对这些项进入实现**；已落地项必须显式标记，不得重复返工。 6 7 ## 触发条件 8 9 - 用户向本项目里的 Claude Code CLI 发送消息 `start`（或 `START` / `Start` 大小写不敏感） 10 - 消息只有这一个 token，无附加语义 11 12 ## 
- `2026-04-21T05:19:37.467Z` `/Users/m1/.claude/projects/-Users-m1-projects-demo-insights-share/2bc2c885-83de-4156-902d-2e66c5fcdab4.jsonl`
  Looking at CLAUDE.md, there's a `start bootstrap 指令` rule. Let me read the detail.
- `2026-04-21T05:19:31.067Z` `/Users/m1/.claude/projects/-Users-m1-projects-demo-insights-share/2bc2c885-83de-4156-902d-2e66c5fcdab4.jsonl`
  what would happen if we say to claude code CLI in this project 'start'
- `2026-04-21T05:00:53.927Z` `/Users/m1/.claude/projects/-Users-m1-projects-demo-insights-share/ce753193-a398-4dc7-99cf-d6942085a80e.jsonl`
  你是严格裁判。判断下面 F 节是否只保留：1. 极短核心说明；2. 可直接 copy-paste 的代码块。 如果还残留长解释、原则宣讲、非必要小标题，判 REFINE。 只输出 JSON：{"verdict":"PASS|REFINE|FAIL","reason":"..."} 待判内容： <<< <section id="sec-f"> <div class="section-tag">F · CORE</div> <h2>self-verify 双探针 cookbook</h2> <p> 只留核心：probe 真回答，judge 只吐 JSON；下面两段都可以直接复制执行。 </p> <div class="code-wrap
- `2026-04-21T04:59:43.041Z` `/Users/m1/.claude/projects/-Users-m1-projects-paperclip-demo/912f2700-cd24-44b2-9474-331175093159.jsonl`
  **Paperclip AI running.** - **UI**: http://127.0.0.1:3100 - **API**: http://127.0.0.1:3100/api - **Version**: 2026.416.0 - **Mode**: embedded-postgres, local_trusted (loopback only) Open in browser:
- `2026-04-21T04:59:35.896Z` `/Users/m1/.claude/projects/-Users-m1-projects-paperclip-demo/912f2700-cd24-44b2-9474-331175093159.jsonl`
  ┌ paperclipai run │ │ Home: /Users/m1/.paperclip │ │ Instance: default │ │ Config: /Users/m1/.paperclip/instances/default/config.json │ ◇ Running doctor checks... ██████╗ █████╗ ██████╗ ███████╗██████╗ ██████╗██╗ ██╗██████╗ ██╔══██╗██╔══██╗██╔══██╗██╔════╝██╔══██╗██╔════╝██║ ██║██╔══██╗ ██████╔╝███████║██████╔╝█████╗ █
- `2026-04-21T04:59:14.517Z` `/Users/m1/.claude/projects/-Users-m1-projects-paperclip-demo/912f2700-cd24-44b2-9474-331175093159.jsonl`
  > paperclip-demo@1.0.0 test > echo "Error: no test specified" && exit 1 Error: no test specified ┌ paperclipai run │ │ Home: /Users/m1/.paperclip │ │ Instance: default │ │ Config: /Users/m1/.paperclip/instances/default/config.json │ ◇ Running doctor checks... ██████╗ █████╗ ██████╗ ███████╗██████╗ ██████╗██╗ ██╗██████╗
- `2026-04-21T04:58:53.494Z` `/Users/m1/.claude/projects/-Users-m1-projects-paperclip-demo/912f2700-cd24-44b2-9474-331175093159.jsonl`
  1 2 ██████╗ █████╗ ██████╗ ███████╗██████╗ ██████╗██╗ ██╗██████╗ 3 ██╔══██╗██╔══██╗██╔══██╗██╔════╝██╔══██╗██╔════╝██║ ██║██╔══██╗ 4 ██████╔╝███████║██████╔╝█████╗ ██████╔╝██║ ██║ ██║██████╔╝ 5 ██╔═══╝ ██╔══██║██╔═══╝ ██╔══╝ ██╔══██╗██║ ██║ ██║██╔═══╝ 6 ██║ ██║ ██║██║ ███████╗██║ ██║╚██████╗███████╗██║██║ 7 ╚═╝ ╚═╝ ╚═╝
- `2026-04-21T04:58:53.486Z` `/Users/m1/.claude/projects/-Users-m1-projects-paperclip-demo/912f2700-cd24-44b2-9474-331175093159.jsonl`
  1 ┌ paperclipai run 2 │ 3 │ Home: /Users/m1/.paperclip 4 │ 5 │ Instance: default 6 │ 7 │ Config: /Users/m1/.paperclip/instances/default/config.json 8 │ 9 ◇ Running doctor checks... 10 11 ██████╗ █████╗ ██████╗ ███████╗██████╗ ██████╗██╗ ██╗██████╗ 12 ██╔══██╗██╔══██╗██╔══██╗██╔════╝██╔══██╗██╔════╝██║ ██║██╔══██╗ 13 ██
- `2026-04-21T04:37:22.779Z` `/Users/m1/.claude/projects/-Users-m1-projects-demo-insights-share/7e8b859d-6814-45f9-8df5-a52157125373.jsonl`
  When you send bare `start` message, agent follow fixed bootstrap sequence: 1. Read four required files (proposal.md / README.md / validation_AB.md / validation.md) 2. Read proposal/INDEX.md + ALL proposal_*.md (including your new plugin proposal with for loop) 3. List todos derived from all proposals 4. Implement each 
- `2026-04-21T04:37:12.820Z` `/Users/m1/.claude/projects/-Users-m1-projects-demo-insights-share/7e8b859d-6814-45f9-8df5-a52157125373.jsonl`
  what would do when we say 'start' ? JUST EXPLAIN . we just upload the for loop of the plugin proposal , will we start the work ? JUST EXPLAIN
- `2026-04-21T04:00:13.532Z` `/Users/m1/.claude/projects/-Users-m1-projects-demo-insights-share/8f4a9a18-c359-4bee-a5e0-622a2b133991.jsonl`
  你是严格裁判。判断下面这份纯文本分享稿是否同时覆盖： 1. 如何用 claudefast 做 fast self-verify 2. 如何手工设计 self-verify 3. 今天 raw jsonl with subagents 的具体绝对路径与父子关系 4. 结尾是否有一行传播话术 只输出 JSON：{"verdict":"PASS|REFINE|FAIL","reason":"...","missing":["..."]} 待判文本： <<< ================================================================ claudefast Self-Verify 手册 用
