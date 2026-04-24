<!-- /autoplan restore point: /Users/m1/.gstack/projects/demo_insights_share/main-autoplan-restore-20260423-152915.md -->
# TODOS

> 本文件维护 `/plan-eng-review` 结果中 user 决策为 "添到 TODOS.md" 的条目，提交者是 m1。新增条目格式参考 `.claude/skills/review/TODOS-format.md`（若存在）。

---

## Open — surfaced at final gate

### [UC-1] plugin bundle self-containment：先切断 repo 绑定，再让 demo 走真实 `claude plugin install`

- **What**：把 `plugins/insights-share/hooks/user-prompt-submit.sh`、`hooks/session-start.sh`、`scripts/self_check.sh` 对 repo checkout 和 `demo_codes/.venv` 的回跳依赖改成 bundle-local 或 runtime-packaged 资源；目标是 clean-machine 上只装 plugin / publish 仓也能跑通 first search / prefetch / self-check。
- **Why**：两路 Eng outside voices 都指出当前 `SB-1` 不是“真实 install parity”，而是“表面 install + 实际 repo fallback”。现状下就算 `start.demo.sh` 改成 `claude plugin install`，hook 仍会回跳到 repo 内 `insights-share/demo_codes`，hero surface 还是假的。
- **Pros**：把 `SB-1` 从 chore 变成真实分发合同；plugin 仓才有资格代表 teammate install 路径；clean-machine 失败会更早暴露。
- **Cons**：会牵动 hook bootstrap、Python 运行时、publish 仓内容和 self-check；不是“两行 shell 替换 cp”。
- **Context**：证据见 `plugins/insights-share/hooks/user-prompt-submit.sh`、`plugins/insights-share/hooks/session-start.sh`、`plugins/insights-share/scripts/self_check.sh`。
- **Depends on / blocked by**：建议并入 `SB-1` 重写；否则 `SB-1` 落地后仍会保留 repo 绑定。
- **Estimate**：human ~0.5-1 day / CC ~1-2h。
- **Source**：/autoplan Eng dual voices 2026-04-23。

### [UC-2] trust / audit boundary：不要只 grep secret，还要给写接口和 raw_log 注入画边界

- **What**：为 daemon 的 `POST /insights`、`/topics`、`/topics/{id}/examples`、`/insights/{id}/relabel`、`DELETE /insights/{id}` 加 loopback / token / role policy，并给 `raw_log` 与 `additionalContext` 注入链路补显式 allowlist / redact / 测试。
- **Why**：当前只有 `/_events` 和 `/api/cli/tmux/input` 做了 loopback/token 限制；同时 `insights_prefetch.py` 会静默把卡片内容注入回答上下文，`FEATURES.md` 又明确 `raw_log` 是明文存储。只做 Stage 0 secret grep 仍然是在补错层。
- **Pros**：把“trust”从 demo hygiene 拉回真实数据边界；也让 sponsor / teammate install 风险更可解释。
- **Cons**：会触到 daemon API 契约、plugin hooks 和缓存行为，scope 比单纯 grep 大。
- **Context**：证据见 `insights-share/demo_codes/insightsd/server.py`、`insights-share/demo_codes/hooks/insights_prefetch.py`、`FEATURES.md`。
- **Depends on / blocked by**：不阻塞 dry-run；是否升 ship-blocker 需要 final gate 决策。
- **Estimate**：human ~0.5-1 day / CC ~1-2h。
- **Source**：/autoplan Eng dual voices 2026-04-23。

---

## Closed / Deferred

### [DONE] [SB-1] start.demo.sh 主入口改走 `claude plugin install`

- **What**：`start.demo.sh` Stage 3 已在 sandbox HOME 内执行 `claude plugin marketplace add` + `claude plugin install insights-share@insights-share`，不再靠旧式手动 copy skill 作为 hero install path。
- **Evidence**：`bash start.demo.sh --dry-run`、live `bash start.demo.sh`、`bash insights-share/validation/run_ci_gate.sh` 均已通过；右 pane 自检显示 sandbox plugin cache 与 `plugin self-check: ALL GREEN`。
- **Follow-up still open**：`UC-1` 仍保留，因为 plugin runtime self-containment 是更大的分发契约，不等同于 hero surface 改用 plugin install。
- **Source**：2026-04-24 E2E recovery。

### [DONE] [AP-1] clean-machine adoption proof

- **What**：新增 `bash insights-share/validation/run_adoption_proof.sh`，用隔离 `HOME` 与临时 wiki store 验证 clean-machine install、first relevant hit、first publish、day-2 return。
- **Evidence**：`insights-share/validation/reports/deliverables/adoption_proof_latest.json` 记录 `pass=true`，四个 signals 均为 ok；`run_contract_tests.sh` 已把 `test_adoption_proof.py` 纳入默认合同。
- **Source**：2026-04-24 AP-1 gate。

### [DONE] [FL-1] CI/pre-commit gate

- **What**：新增 `bash insights-share/validation/run_ci_gate.sh` 与 `.github/workflows/e2e-gates.yml`，监视 start/plugin/demo_codes/validation/release 相关改动。
- **Evidence**：本机 `bash insights-share/validation/run_ci_gate.sh` 已跑通 contract tests、adoption proof、`start.demo.sh --dry-run`；合同测试扩到 23 项。
- **Source**：2026-04-24 CI gate。

### [DONE] [FL-2] corpus secret 自检升级为 start.demo.sh Stage 0

- **What**：`start.demo.sh` 已在 Stage 0 扫描 `insights-share/demo_codes/wiki_tree/**/raw/` 中的常见 token/secret pattern，命中即阻断 demo。
- **Evidence**：`bash start.demo.sh --dry-run` 与 `run_ci_gate.sh` 输出 `Stage 0 secret gate passed`。
- **Source**：2026-04-24 E2E recovery。

### [DONE] [SB-2] start.demo.sh 新增 `--dry-run` seam

- **What**：`start.demo.sh` 已支持 `DRY_RUN=1` / `--dry-run`，会跳过 Stage 5 daemon 启动和 tmux attach，并 dump `LEFT_SH` / `RIGHT_SH` / redacted `ENV_FILE` / cleanup 归档路径。
- **Evidence**：代码在 `start.demo.sh:40-51` 和 `start.demo.sh:392-416`；实测 `bash start.demo.sh --dry-run` 于 2026-04-23 通过。
- **Follow-up still open**：`insights-share/validation/test_start_scripts.py` 断言仍停留在旧文案，当前 pytest 会 fail；所以后续工作从“补 dry-run 功能”转成“让 regression gate 对齐现状”。
- **Source**：/autoplan CEO phase 2026-04-23 reconciliation。

---

## /autoplan Phase 1 — CEO Review (2026-04-23)

### Plan Summary

当前 plan 不是“从零做产品”，而是“把 `start.demo.sh` 这条 hero surface 和真实 plugin 分发路径重新对齐，再补两道信任门”。这条线有价值，但现在过度偏向 demo-hardening，缺少 adoption proof。

### 0A. Premise Challenge

| Premise | Verdict | Why |
|--------|---------|-----|
| `start.demo.sh` 必须和真实用户 install 路径同构 | `VALID` | `proposal/proposal_plugin_design.md:84-94` 明确把 `plugin install` 放进 MVP 范围；现在 `start.demo.sh:102-123` 仍是 `cp + cp-R` workaround，确实在伤 hero surface 的可信度。 |
| `[SB-2] --dry-run seam` 仍是 open blocker | `INVALID / STALE` | `start.demo.sh:40-51` 和 `start.demo.sh:392-416` 已经支持 `--dry-run`，而且 `bash start.demo.sh --dry-run` 真能跑通。继续把它当 open blocker，只会让 backlog 失真。 |
| demo Stage 0 grep secret 是主要信任控制 | `PARTIAL` | 这是必要 backup，不是 primary control。真正更高优先级的风险是 `FEATURES.md:82-84` 里 `raw_log` 明文存储，加上 silent background fetch/load 的数据边界没有被当前 TODO 主动约束。 |
| 当前 4 个 TODO 足够证明产品方向正确 | `INVALID` | 两个 outside voices 都指出：现在证明的是“脚本更诚实”，不是“共享 insight 真的让 teammate 更快、更准、更稳定”。缺少 adoption proof。 |

### 0B. Existing Code Leverage

| Sub-problem | Existing code / asset | Leverage |
|------------|------------------------|----------|
| demo dry-run | `start.demo.sh:40-51,392-416` | 基础能力已在，不该重复规划；后续只需要把测试和 TODO 状态追平。 |
| plugin packaging | `plugins/insights-share/.claude-plugin/plugin.json`, `marketplace.json`, `plugins/insights-share/scripts/self_check.sh` | `SB-1` 不是“从零建插件”，而是把现有 packaging 接到 demo hero path。 |
| demo self-verify | `start.demo.sh:295-385`, `FEATURES.md` | 已有 canonical manifest + runtime evidence 面板，适合继续当 hero surface。 |
| regression harness | `insights-share/validation/test_start_scripts.py` | 已有 contract test，但现在断言已经漂移，说明 gate 方向对，覆盖面不够。 |
| product design context | `proposal/proposal_plugin_design.md`, `proposal.md`, `FEATURES.md` | 真实 north star 已存在，不需要再写新 vision doc，只需要把 TODO 和 north star 对齐。 |

### 0C. Dream State Mapping

```text
CURRENT
  start.demo.sh 仍靠 cp/settings workaround
  TODO 把已完成的 SB-2 继续当 open blocker
  adoption proof 缺位

THIS PLAN (after CEO correction)
  demo hero path 与 plugin install 同构
  stale TODO 清理，dry-run 改为已落地事实 + regression gate输入
  secret scan 作为 backup gate
  新增 adoption proof 轨道

12-MONTH IDEAL
  clean-machine teammate 5 分钟内完成 install + first success
  shared insight 相比 fresh inference 有明确 outcome lift
  corpus trust / curation / expiry / audit 成为 moat
```

### 0C-bis. Implementation Alternatives

| Option | Summary | Effort | Risk | Completeness | Verdict |
|-------|---------|--------|------|--------------|---------|
| A | 维持当前 TODO，只做 `SB-1/SB-2/FL-1/FL-2` | 低 | 中高，容易继续 demo theater | `6/10` | Rejected |
| B | `SELECTIVE_EXPANSION`：保留 `SB-1`，把 `SB-2` 从 open 移除，补 `Adoption Proof` 轨道，`FL-1/FL-2` 顺延 | 中 | 低 | `9/10` | Recommended |
| C | 把 `plugin install` 从 hero surface 降级成 release gate，只保留 deterministic demo | 中 | 中 | `7/10` | Viable, but surfaced as taste decision because Codex favors it and the design doc does not |

### 0D. Mode-Specific Analysis

Mode 选 `SELECTIVE_EXPANSION`。原因很直接：

- 不需要回到平台大扩 scope，现有代码已经足够支撑下一轮学习。
- 也不能只做 hygiene。否则 6 个月后留下的是一条更干净的 demo，而不是更强的产品信号。
- 最合理的做法是保留 demo truthfulness 主线，但同时补一条 adoption proof 主线，让下一次 ship 学到“用户会不会真回来”。

### 0E. Temporal Interrogation

| 时间窗 | 若按当前 TODO 直接做 | 若按修正版执行 |
|------|----------------------|----------------|
| Hour 1 | 会继续把已完成的 `SB-2` 当 blocker | 先 reconcile TODO 与 repo reality，再动手做真正未完成项 |
| Hour 6 | 获得更真实的 demo install path | 同时拿到更真实的 demo install path + 一组 adoption success criteria |
| Week 2 | 只能说“脚本更稳了” | 可以说“clean-machine install 是否顺、first query 是否有 lift、用户是否回访” |
| 6 months | demo 很诚实，但产品 pull 可能仍不成立 | 至少开始积累 moat 在 corpus/trust/adoption，而不是只在 shell choreography |

### 0F. Mode Selection

`SELECTIVE_EXPANSION`

- 保留：`SB-1`
- 纠偏：`SB-2` 不再作为 open blocker
- 降级：`FL-2` 保留为 trust backup，不升成唯一 trust story
- 新增：`Adoption Proof` 轨道

### CEO Dual Voices

#### CLAUDE SUBAGENT (CEO — strategic independence)

- 核心判断：当前 plan 是 solid demo-hardening，但不是强 product/adoption plan。
- 关键主张：保留 `SB-1`，补 `Adoption Proof` 顶层轨道，把 clean-machine onboarding、query relevance、publish trust、repeat use 拉到 backlog 顶部。
- 关键发现：`SB-2` 在代码里已落地，backlog integrity 已经滑坡。

#### CODEX SAYS (CEO — strategy challenge)

- 核心判断：当前 TODO 把“演示安装路径一致”错当成核心产品问题。
- 关键主张：不要把 `plugin install` 和 hero surface 完全绑死；`start.demo.sh` 追求确定性，`plugin install` 可作为 release gate 单独验证。
- 关键发现：当前 TODO 主要优化 installer / drift gate / grep hygiene，没有回答“为什么不直接再问一次模型”。

### CEO DUAL VOICES — CONSENSUS TABLE

```text
═══════════════════════════════════════════════════════════════
  Dimension                           Claude  Codex  Consensus
  ──────────────────────────────────── ─────── ─────── ─────────
  1. Premises valid?                   No      No      CONFIRMED
  2. Right problem to solve?           No      No      CONFIRMED
  3. Scope calibration correct?        No      No      CONFIRMED
  4. Alternatives sufficiently explored?No     No      CONFIRMED
  5. Competitive/market risks covered? No      No      CONFIRMED
  6. 6-month trajectory sound?         No      No      CONFIRMED
═══════════════════════════════════════════════════════════════
```

### Review Sections

#### Section 1: Architecture Review

我检查了 `start.demo.sh`、plugin manifest、marketplace 和 self-check 链路。CEO 结论不是“再搭新架构”，而是“别让已有架构说一套、hero surface 做一套”。现有系统已经有 plugin packaging、statusline、slash 命令和 self-check，架构层真正的缺口是 demo path 没有证明这些东西真是用户 install path。

#### Section 2: Error & Rescue Map

| Failure | User sees | Current rescue | CEO verdict |
|--------|-----------|----------------|-------------|
| `plugin install` 真实链路坏 | demo 仍可能绿，因为还在 cp workaround | 无 | 这就是 `SB-1` 还该保留的原因 |
| dry-run drift | TODO 说要补，代码里已存在 | `start.demo.sh --dry-run` | 计划必须先 reconcile，再继续扩 |
| secret-like raw content | demo 前可能被 grep 出 | 手动/未来 Stage 0 | 这是 backup，不是 primary trust story |
| start.demo regression | `pytest insights-share/validation/test_start_scripts.py` 已 fail | 现有测试断言陈旧 | 说明 regression gate 思路对，但 coverage 仍不够 |

#### Section 3: Security & Threat Model

当前 TODO 只把 secret grep 显性化了，但没有把 silent background fetch、`raw_log` 明文、权限边界和审计路径抬到同一优先级。CEO 视角下，这意味着你在讲“卫生”，还没讲“trust model”。

#### Section 4: Data Flow & Interaction Edge Cases

我看了 `start.demo.sh` 的 Stage 2/3 手工复制、Stage 5 daemon 启动和 dry-run dump。最明显的 edge case 不是 bash quoting，而是“demo 证明了什么”。现在它证明的是 sandbox + self-check，没证明 clean-machine teammate 真能靠 plugin install 完成同样路径。

#### Section 5: Code Quality Review

代码层最大的 CEO finding 不是复杂度，而是 plan/code drift。`SB-2` 已落地，但 `TODOS.md` 还在把它当 blocker；`pytest` 也因为旧字符串断言失败。这不是实现问题，是 execution artifact 不再可信的问题。

#### Section 6: Test Review

我实际跑了 `pytest -x insights-share/validation/test_start_scripts.py`，当前在 `test_start_demo_script_surfaces_plugin_m5_checks` 失败，原因是断言的旧文案已经不在 `start.demo.sh` 里。说明下一轮测试目标应该是：

- 把 `start.demo.sh --dry-run` 纳入 contract test
- 让 contract test 对齐现在的 6-feature manifest，而不是旧的 “5 命令 + 2 agent + 签名/发布脚本”
- 把 “plugin install hero path” 作为单独可验证 contract

#### Section 7: Performance Review

CEO 层没有新的性能 blocker。当前 next-step plan 更大的问题不是快不快，而是“在更诚实之后，是否更有价值”。性能可以继续跟随现有 latency work，不需要把它塞进本轮 top backlog。

#### Section 8: Observability & Debuggability Review

现有可见信号有 `today_count`、statusline、self-check、deliverables 日志。但这些更多是工程/演示可见性，不是 adoption observability。缺的是：

- clean-machine install success rate
- first query hit quality / relevance
- first publish success
- day-2 return rate

#### Section 9: Deployment & Rollout Review

仓库现在没有 `.github/workflows/`，也没看到 pre-commit 配置。说明 `FL-1` 不是“补一点点 glue”，而是第一次把 next-step plan 接到自动化 gate 上。这个方向对，但它应排在 reconcile stale TODO 之后。

#### Section 10: Long-Term Trajectory Review

长期 moat 不是 `claude plugin install` 本身，而是 corpus 质量、`applies_when` 匹配、来源可信度、过期衰减和 curator 成本。如果 backlog 长时间只围绕 shell choreography，未来看起来会像在产品化外壳，而不是产品化共享知识资产。

#### Section 11: Design & UX Review

Skipped. 当前 plan 没有足够 UI scope，主要是 demo shell / plugin / validation / rollout。

### NOT in scope

- 新增 admin kanban / 新 slash 命令 / 新 agent
- 扩展更多 UI review
- 继续做 statusline 视觉层 polish
- 新 infra / 新 storage 方案

### What already exists

- 真正可跑的 `start.demo.sh --dry-run`
- 真正存在的 plugin manifest / marketplace / self-check
- 真正存在的 canonical feature manifest
- 真正存在的 validation harness

### Error & Rescue Registry

| Area | Rescue |
|------|--------|
| TODO 与代码状态不一致 | 每轮 review 先 reconcile TODO state，再决定 blocker |
| demo 仍是 cp workaround | 把 `plugin install` 真实接入 hero surface 或明确定义为独立 release gate |
| contract test 漂移 | 以 `FEATURES.md` 为真源，重写断言到 dry-run output / manifest |
| trust story 过窄 | secret scan 保留，但补 adoption + audit + trust signal |

### Failure Modes Registry

| Failure mode | Severity | Status |
|-------------|----------|--------|
| hero surface 继续不走真实 install path | Critical | Open |
| plan/code drift 继续存在 | High | Open |
| 把 demo hygiene 当 adoption proof | Critical | Open |
| trust model 只剩 secret grep | High | Open |

### Dream State Delta

当前 plan 离 12-month ideal 还差一条最关键的线：它没有直接测“共享 insight 是否让 teammate 回来第二次”。如果这条不补，未来即使 installer 完美，也还是证明不了产品 pull。

### Completion Summary

| Item | Verdict |
|------|---------|
| Scope hardening direction | Keep, but not alone |
| `SB-1` | Keep in scope |
| `SB-2` | Already implemented, remove from open blockers |
| `FL-1` | Keep, after reconcile |
| `FL-2` | Keep as backup trust gate, not primary trust story |
| New track | Add `Adoption Proof` |
| Mode | `SELECTIVE_EXPANSION` |

## /autoplan Phase 2 — Design Review (2026-04-23)

Phase 2 skipped. 当前 plan 没有独立 UI scope，主要是 demo shell、plugin packaging、validation、docs 和 onboarding 路径；没有足够设计变量值得单独跑 `/plan-design-review`。

## /autoplan Phase 3 — Eng Review (2026-04-23)

### Plan Summary

这轮 Eng review 的结论很硬。当前 TODO 里最像 blocker 的不是“把 `cp -R` 换成 `claude plugin install`”，而是“plugin runtime 到底是不是 self-contained”。如果 runtime 还要回跳 repo checkout 和 `demo_codes/.venv`，那 hero surface 只是换了外壳。

### Step 0: Scope Challenge

| Sub-problem | Actual code / evidence | Verdict |
|------------|------------------------|---------|
| hero-surface install parity | `start.demo.sh:102-122` 仍复制 settings + skill；`plugins/insights-share/hooks/user-prompt-submit.sh:18-35`、`hooks/session-start.sh:20-29,94-104`、`scripts/self_check.sh:66-78` 仍回跳 repo | 当前 `SB-1` 描述偏浅，需要先解决 self-containment |
| regression gate | `pytest -q insights-share/validation/test_start_scripts.py`、`test_plugin_contract.py`、`test_release_package.py` 于 2026-04-23 全部失败 | 当前 `FL-1` 范围过窄，先修 contract 再上 CI |
| trust boundary | `insightsd/server.py:334-407` 仅保护 `/_events` 和 `/api/cli/tmux/input`；`410-594` 的写接口无等价保护 | 当前 `FL-2` 补的是 backup，不是 primary risk |
| silent injection | `insights_prefetch.py:121-149,254-280` 会静默注入 `additionalContext`；`FEATURES.md` 又声明 `raw_log` 明文存储 | trust story 不能只讲 grep |
| adoption proof | `examples/run_human_AB.sh:31-36` 仍用 `insights-wiki` skill/cache 名，A/B harness 已经不是当前产品 | `AP-1` 必须落成可执行 artifact，而不是口号 |
| statusline in-flight | `statusline/insights_share_statusline.sh:32,66-74` 读 `.in_flight`；`today_count.py:147-153` 的 `mark_in_flight()` 仍是 no-op | 现有 “…” 态没有完整生产链路 |

复杂度也不是 bash 行数本身，而是跨四棵树的耦合：`start.demo.sh`、`plugins/insights-share/`、`insights-share/demo_codes/`、`insights-share/validation/`。这就是为什么看起来像文档修补，实测却是一串合同同时失真。

### CLAUDE SUBAGENT (eng — independent review)

- `SB-1` 现在不是真 clean-machine parity，因为 plugin runtime 仍绑 repo checkout 和 demo venv。
- `FL-2` 补错层，真正更大的风险是 daemon 写接口无边界，以及明文 `raw_log` 被静默回灌。
- `FL-1` 太窄，contract suite 已经不止 `test_start_scripts.py` 在红。
- `plugin install` flow 和 daemon/bootstrap 之间有顺序竞态，先后差一步就会绿假象。
- `AP-1` 还太虚，需要挂到 `examples/` / `validation/` 的具体产物。
- cleanup / redaction 复杂度被低估，当前删除/归档口径和 export 文本卡不是一回事。

### CODEX SAYS (eng — architecture challenge)

- Critical：`SB-1` 被写成 hero-path plugin install，但 runtime 根本还不是 self-contained。
- High：`FL-2` 硬化的是错层风险，写接口和 silent load 才是主要 trust boundary。
- High：`AP-1` 太泛，而且现有 A/B harness 已经过时。
- Medium：`FL-1` 不该继续 assert prose，而应 assert 当前 manifest / package / runtime contract。
- Medium：plan 混着两件事，deterministic local demo 和 real teammate install，不拆开就会持续打架。

### ENG DUAL VOICES — CONSENSUS TABLE

```text
═══════════════════════════════════════════════════════════════
  Dimension                           Claude  Codex  Consensus
  ──────────────────────────────────── ─────── ─────── ─────────
  1. Architecture sound?               No      No      CONFIRMED
  2. Test coverage sufficient?         No      No      CONFIRMED
  3. Performance risks addressed?      No      No      CONFIRMED
  4. Security threats covered?         No      No      CONFIRMED
  5. Error paths handled?              No      No      CONFIRMED
  6. Deployment risk manageable?       No      Partial DISAGREE
═══════════════════════════════════════════════════════════════
```

Disagree 的点很具体：Claude 视角认为当前 deploy/install 风险仍然太高，Codex 视角认为如果把 deterministic demo 和 teammate install 拆成两条合同，这件事可管理。这是 taste decision，不是自动拍板。

### Section 1: Architecture Review

```text
                     ┌──────────────────────────────┐
                     │          start.demo.sh        │
                     │  sandbox + self-verify demo   │
                     └──────────────┬───────────────┘
                                    │
               ┌────────────────────┼────────────────────┐
               │                    │                    │
               ▼                    ▼                    ▼
   Stage 2/3 settings+skill   Stage 5 insightsd    validation contracts
   copy / future install      local daemon         test_start_scripts
               │                    │              test_plugin_contract
               │                    │              test_release_package
               ▼                    ▼
   plugins/insights-share      demo_codes/wiki_tree
   commands / agents /         runtime / hooks
   hooks / statusline / mcp          │
               │                     │
               ├──────────────┬──────┘
               ▼              ▼
   user-prompt-submit     session-start
   repo fallback          repo fallback
   demo_codes/.venv       full-fetch script
```

架构上的主要问题不是模块缺失，而是分发边界说不清。`start.demo.sh` 通过 env override 把 plugin 默认 LAN 地址改回 `127.0.0.1`，又通过 repo 内 settings/skill copy 绕过真实 install 路径，这让 demo 能绿，但也把 teammate install 的真实风险藏掉了。

### Section 2: Code Quality Review

- 文档和测试的版本漂移已经成系统性问题。`plugins/insights-share/README.md` 仍混用 `0.6.0-m7` 分发叙事和 `0.5.0-m5` 装后期待，`test_plugin_contract.py` / `test_release_package.py` 仍 assert 旧世界。
- 配置常量散落。`192.168.22.42:7821` 同时出现在 `plugin.json`、`mcp/wiki-server.json`、`statusline`、`session-start`、`share-install`、`share-publish`、`insights_prefetch.py`，现在没有单一真源。
- repo fallback 逻辑重复而脆。`user-prompt-submit.sh`、`session-start.sh`、`self_check.sh` 各自实现一遍 “回 repo 找 demo_codes”。

### Section 3: Test Review

Test plan artifact 已写出：`/Users/m1/.gstack/projects/demo_insights_share/m1-main-eng-review-test-plan-20260423-155547.md`

#### Test Diagram

| Flow / contract | Current coverage | Gap |
|-----------------|------------------|-----|
| `start.demo.sh --dry-run` stdout schema | `test_start_scripts.py` 部分覆盖 | 仍 assert 旧 M5 文案，没 assert plugin-install 真实路径 |
| plugin manifest / marketplace / README 对齐 | `test_plugin_contract.py` 覆盖 | 断言仍锁在 `0.5.0-m5` 和旧 MCP / marketplace 语义 |
| release bundle layout | `test_release_package.py` 覆盖 | 仍盯 `plugin/` 旧目录，不认识双仓 / 当前 layout |
| clean-machine plugin install | 无 | 这是 `SB-1` 真正缺口 |
| plugin-only hook execution | 无 | 当前 hook 只在 repo checkout 里看起来能用 |
| daemon 写接口 auth / loopback | 无 | `/insights` / `/topics` / relabel / delete 没 gate test |
| raw_log / additionalContext trust boundary | 无 | 没有 allowlist / redact / negative test |
| statusline `…` in-flight 生产链路 | 仅 statusline 读路径 | 没有 producer 行为 test |
| adoption proof A/B | `examples/run_human_AB.sh` 存在 | harness 仍用旧 `insights-wiki` 命名，不代表当前产品 |
| day-2 return | 无 | `AP-1` 缺最小 proof artifact |

LLM/prompt 层这轮不需要独立 eval 套件。真正该补的是 install contract、trust contract、adoption contract。

### Section 4: Performance Review

没有发现传统意义上的热点查询问题。当前性能风险集中在 cold-start 和失败路径：

- `session-start.sh` 和 `insights_prefetch.py` 默认都先走固定 LAN 地址，clean-machine / 非局域网场景的真实首轮体验是“先等失败，再 fallback”。
- `start.demo.sh` 用 `INSIGHTS_SHARE_URL=127.0.0.1` 把这层延迟遮住了，所以 demo 比真实 teammate install 更乐观。
- `statusline` 的 60s health cache 没问题，但 `…` 态缺 producer，使“正在工作”这件事在性能上不可见。

### NOT in scope

- 改 daemon 存储模型
- 新增 UI / dashboard 流程
- 重写 statusline 渲染逻辑
- 把所有 examples/legacy harness 一次性清仓

### What already exists

- `start.demo.sh --dry-run` 真能跑
- plugin manifest / commands / agents / statusline / self-check 主体都在
- release builder 能产 zip / manifest / sha256
- `examples/` 和 `validation/` 里已经有 adoption / contract 的骨架

### Failure Modes Registry

| Failure mode | Severity | Status |
|-------------|----------|--------|
| demo 改成 `plugin install` 后仍偷偷依赖 repo checkout | Critical | Open |
| contract suite 持续盯旧版本，CI 只能报假红 | High | Open |
| daemon 写接口继续裸露在 LAN | Critical | Open |
| `raw_log` / additionalContext 无边界继续静默注入 | High | Open |
| adoption proof 继续使用旧 `insights-wiki` harness | High | Open |

### Completion Summary

| Item | Verdict |
|------|---------|
| `SB-1` 原始表述 | Too shallow, should be rewritten around self-containment |
| `FL-1` | Keep, but widen to full contract suite |
| `FL-2` | Keep as backup only |
| `AP-1` | Keep, but convert to concrete artifact + harness |
| New surfaced challenge | `UC-1` plugin self-containment |
| New surfaced challenge | `UC-2` trust / audit boundary |
| Phase result | 5/6 consensus, 1 taste disagreement |

> **Phase 3 complete.** Codex: 5 concerns. Claude subagent: 6 issues.
> Consensus: 5/6 confirmed, 1 disagreement surfaced at gate.
> Passing to Phase 3.5 (DX Review) or Phase 4 (Final Gate).

## /autoplan Phase 3.5 — DX Review (2026-04-23)

### Plan Summary

这轮 plan 明确有 DX scope。`insights-share` 不是单一 shell 脚本，而是给 teammate 装的 Claude Code plugin、daemon、README、slash commands、statusline 和 validation 合同的组合。现在最伤 developer confidence 的不是少一条命令，而是“入口太多、名字太像 install、结果却不一定真 install”。

### Step 0: DX Scope Assessment

| Signal | Evidence | Verdict |
|--------|----------|---------|
| 产品类型 | Claude Code plugin + daemon + docs + validation | 必跑 DX review |
| 主要 persona | 第一次装 `insights-share` 的 teammate / builder，想在 5 分钟内拿到 first hit / first publish | 当前没有单一路径服务这个 persona |
| 当前 TTHW | clean-machine 约 `7-9` 个显式动作，`10-15` 分钟；还要自己判断 source 模式、marketplace 模式、daemon 在哪台机器上 | 明显不达标 |
| 目标 TTHW | `<5` 分钟、`<=3` 个显式命令、一个 canonical quickstart | 应作为 adoption gate |
| 初始 DX 完整度 | `3/10` | 现在更像“熟悉仓库的人能跑”，不是“第一次来的 teammate 能成功” |

### CLAUDE SUBAGENT (DX — independent review)

- Getting started 没有被设计成 `<5` 分钟 happy path，当前 clean-machine 仍需 `7-9` 个手动动作。
- `/share-install` 是命名陷阱。它叫 install，但正文又明写“不把 plugin manifest 写入真实 `~/.claude/`”，实际更像 verify/doctor。
- 命名面不一致。用户面是 `share-*`，但 MCP / examples / 旧 harness 仍泄漏 `wiki-*` / `insights-wiki`。
- 错误处理不是 deliverable。缺统一的 problem / cause / fix / docs-link 输出模板。
- docs drift 严重。仓库根 `README.md` 只有两行，plugin README 同时混着 `v0.6.0-m7` 双仓叙事和 `0.5.0-m5` 装后期待。
- escape hatch 其实存在，但都藏在 env / fallback 里，没有作为用户可发现界面交付。

### CODEX SAYS (DX — developer experience challenge)

- 当前 DX 是碎的，不存在一个 under-5-minute 的 canonical path。developer 必须自己在 `start.demo.sh`、source 模式、marketplace 模式之间猜哪条才算真的。
- `/share-install` 的语义和行为不一致：文案写“一键安装”，命令体却明确说“不写真实 `~/.claude/`”，这会直接污染信任。
- docs / examples / tests 同时漂移。顶层 `README.md` 几乎为空；plugin README 还写 `0.5.0-m5`；`examples/run_human_AB.sh` 仍用 `insights-wiki` skill 和 cache 名。
- 升级路径不安全，因为 validation / release contract 还盯旧 bundle 结构和旧版本号。developer 很难判断“是我装错了，还是仓库自己还没迁完”。
- 固定 LAN URL 和 repo fallback 让 clean-machine 体验先天脆弱。看起来像 local convenience，实际是 onboarding debt。

### DX DUAL VOICES — CONSENSUS TABLE

```text
═══════════════════════════════════════════════════════════════
  Dimension                           Claude  Codex  Consensus
  ──────────────────────────────────── ─────── ─────── ─────────
  1. Getting started < 5 min?          No      No      CONFIRMED
  2. API/CLI naming guessable?         No      No      CONFIRMED
  3. Error messages actionable?        No      No      CONFIRMED
  4. Docs findable & complete?         No      No      CONFIRMED
  5. Upgrade path safe?                No      No      CONFIRMED
  6. Dev environment friction-free?    No      No      CONFIRMED
═══════════════════════════════════════════════════════════════
```

这轮没有 taste 分歧。两路声音都在指向同一件事：现在的 developer story 不是“不够华丽”，而是“不够单一、也不够可信”。

### Developer Journey Map

| Stage | Developer 正在做什么 | 当前摩擦 | 应改成什么 |
|------|----------------------|----------|------------|
| 1 | 发现仓库 | 根 README 只有“insights 共享演示仓库”，看不出安装入口 | 顶层 README 直接给 canonical quickstart |
| 2 | 选择文档入口 | plugin README、proposal、start.demo.sh、examples 同时存在 | 明确一页“第一次安装看这里” |
| 3 | 判断安装模式 | source / marketplace / demo 三条路并存，优先级不清 | 只保留一个对外 happy path，其他都标 internal/dev only |
| 4 | 启 daemon | 需要知道 `192.168.22.42:7821` 或本地 serve，且 docs 分散 | daemon 获取方式写成一步，失败时给 repair path |
| 5 | 安装 plugin | `/share-install` 名字像真安装，实际不写 `~/.claude/` | 要么真 install，要么改名为 `/share-doctor` |
| 6 | 验证装机 | statusline / self-check / healthz 各自能看，但缺统一“装好了”判据 | 统一成 one-shot doctor output |
| 7 | 第一次搜索 | 命中质量、team namespace、LAN/base_url 假设都不透明 | 提供 copy-paste first hit 示例和 expected output |
| 8 | 第一次发布 | publish 路径和签名/摘要能力在，但 docs 没把 happy path 串起来 | quickstart 直接覆盖 first publish |
| 9 | 第二天回来 | 没有 day-2 return 指标，也没有升级/迁移护栏 | AP-1 必须绑定 return signal 和 migration gate |

### Developer Empathy Narrative

如果我是第一次接手这个仓库的 teammate，我会先打开根 README，然后立刻失去方向。接着我会看到 plugin README 里既有 source 模式、又有 marketplace 模式、又有双仓说明，还夹着 `0.5.0-m5` 和 `0.6.0-m7` 两套世界观。到这里我已经在猜你到底要我装什么。

更糟的是，命名在骗我。`/share-install` 说自己是一键安装，但正文又说它不会写真实 `~/.claude/`。所以当我装不起来时，我不知道是命令故意不装，还是我操作错了。developer 一旦失去这种最基本的因果感，后面每个失败都像踩迷雾。

### Section 1: Getting Started Review

Score: `3/10`

当前 onboarding 不是从“零到 first success”设计的，而是从“熟悉代码的人如何绕过坑”长出来的。根 README 没入口，plugin README 给出多条路径，`start.demo.sh` 又单独承载一套 demo-only 契约。

这会直接把 clean-machine TTHW 拉长到 `10-15` 分钟，而且每一步都要 developer 自己判断哪条路径是 canonical。对内部工具来说，这已经足够让一半人放弃第二次尝试。

### Section 2: API / CLI Ergonomics Review

Score: `4/10`

用户面命名已经在朝 `share-*` 统一，但内部面还在泄漏 `wiki-*`、`insights-wiki` 和旧 MCP 命名。最明显的问题是 `/share-install`，这不是“略微不精确”，而是动作名和副作用不一致。

一致性比聪明更重要。现在 developer 需要记住“哪些名字已经改了，哪些还是历史包袱”，这就是不必要的心智税。

### Section 3: Error Handling Review

Score: `4/10`

当前错误更多像 shell / test / path 失败，而不是面向开发者的诊断信息。比如 base URL、repo fallback、旧版本测试断言、旧 release layout 这些问题一旦出现，developer 得自己沿着 README、tests、脚本去反推根因。

这轮 plan 里还没有一条统一规则要求每个失败都给出 problem / cause / fix / docs link。没有这个模板，first failure 基本不可恢复。

### Section 4: Documentation & Learning Review

Score: `3/10`

文档层现在是最明显的 drift 面。根 README 过薄，plugin README 信息量很多，但混着旧 milestone、双仓迁移、source 模式、marketplace 模式和旧验证口径，developer 两分钟内很难找到“我现在到底该跑哪条命令”。

`examples/run_human_AB.sh` 仍保留 `insights-wiki` skill / cache 名，这会让人以为重命名没有做完。文档不是缺内容，是缺 hierarchy 和 truth source。

### Section 5: Upgrade & Migration Review

Score: `2/10`

升级路径现在不安全。README 在讲 `v0.6.0-m7` 双仓，验证测试还断言 `0.5.0-m5` 和旧 release layout，examples 仍跑旧 skill 名。developer 升级时看见的是“每个面都像真的，但彼此对不上”。

这类 drift 最伤的是信任，不只是时间。因为你没法判断哪一面代表真相。

### Section 6: Dev Environment & Local Tooling Review

Score: `4/10`

好消息是工具并不缺。`start.demo.sh --dry-run` 已经存在，statusline、自检、release builder、validation harness 也都有骨架。坏消息是它们没有被收敛成一个 friction-free local workflow。

固定 LAN URL、repo fallback 和双仓同步要求，把“能跑”变成了“知道内幕的人能跑”。这不是好 DX。

### Section 7: Escape Hatches & Overrides Review

Score: `4/10`

escape hatch 不是没有，而是藏得太深。现在很多 override 要么在 env 里，要么在 demo 脚本里，要么靠 fallback 暗中发生。developer 看不到这些旋钮，自然也不知道出了问题时能怎样自救。

真正好的 escape hatch 是显式、可发现、可复制，而不是“读脚本才知道还能这么配”。

### Section 8: Feedback Loops & Trust Review

Score: `3/10`

当前有 statusline、today_count、自检和签名摘要，这些都是好骨架。但 developer-facing feedback loop 还缺关键几项：install success、first hit success、first publish success、day-2 return。

没有这些指标，AP-1 就还只是正确方向，不是可验证 DX 合同。

### DX Scorecard

| Dimension | Score | Why |
|----------|-------|-----|
| Getting started | `3/10` | 没有单一路径，clean-machine 仍要自己拼 happy path |
| API / CLI design | `4/10` | `share-*` 外观在统一，但 `/share-install` 语义错位，旧 `wiki-*` 还在漏 |
| Errors / debugging | `4/10` | 缺统一 problem / cause / fix / docs-link 模板 |
| Docs / learning | `3/10` | 顶层 README 过薄，plugin README 过杂，truth source 不单一 |
| Upgrade / migration | `2/10` | README、tests、examples、release layout 同时漂移 |
| Dev environment / tooling | `4/10` | 工具骨架有了，但 workflow 还不顺滑 |
| Escape hatches / configurability | `4/10` | override 存在，但不可发现 |
| Measurement / feedback loops | `3/10` | 缺 install / first hit / return 的 developer-facing 指标 |

DX overall：`3/10`

### TTHW Assessment

- 当前：clean-machine 大约 `7-9` 个显式动作，`10-15` 分钟，且需要自己判断 daemon/source/marketplace 哪条才算真的。
- 目标：`<5` 分钟，`<=3` 个显式命令，文档只给一个 happy path。
- Gate：没有做到这个目标之前，不应宣称“teammate install path 已经诚实”。

### DX Implementation Checklist

- 写一页 canonical quickstart，从 blank machine 到 first search / first publish 全程 copy-paste 可跑。
- `/share-install` 二选一：要么真执行安装，要么改名成纯 verify / doctor 命令。
- 把 version / bundle layout / install story 的真源统一到 `v0.6.0-m7`，同步 README、tests、release contract、examples。
- 固定 LAN URL、repo fallback、daemon 发现逻辑收敛到一个显式配置入口。
- 把 `examples/run_human_AB.sh` 迁到当前 `insights-share` 命名，产出可复用 adoption proof artifact。
- 所有装机 / 升级 / health check 失败统一输出 problem / cause / fix / docs-link。
- 把 env overrides 和 escape hatches 升到 README / quickstart，不再藏在脚本实现细节里。
- 给 AP-1 增 install success、first hit success、first publish success、day-2 return 四个最小指标。

### Completion Summary

| Item | Verdict |
|------|---------|
| DX scope detected | Yes |
| Current TTHW | Too slow and ambiguous |
| `/share-install` naming | Misleading, must be fixed or renamed |
| Docs / examples drift | Severe |
| Upgrade path | Unsafe until contracts are reconciled |
| AP-1 | Keep, but bind to explicit DX metrics |
| Phase result | `6/6` consensus, no taste disagreement |

> **Phase 3.5 complete.** DX overall: 3/10. TTHW: 10-15 min → <5 min.
> Codex: 5 concerns. Claude subagent: 6 issues.
> Consensus: 6/6 confirmed, 0 disagreements surfaced at gate.
> Passing to Phase 4 (Final Gate).

## Cross-Phase Themes

### Theme 1: reality drift 比 feature 缺失更伤

CEO、Eng、DX 三个 phase 都独立指向同一件事：代码、测试、README、examples、release contract 没有共享同一个 truth source。继续在这个状态上叠新功能，只会放大假绿和假红。

### Theme 2: hero surface 还没有证明“真实 install path”

CEO 看到的是 demo 仍像 theater，Eng 看到的是 runtime 还绑 repo checkout，DX 看到的是 `/share-install` 名字和行为不一致。三相合并后的结论很简单，当前 hero surface 还没拿到 clean-machine credibility。

### Theme 3: adoption proof 不能停留在口号

CEO 把缺口叫 product pull，Eng 把缺口叫过时 harness，DX 把缺口叫缺少 TTHW / first success / return metrics。其实是同一个问题，没有可重复的 learning loop。

### Theme 4: trust story 不能只靠 demo hygiene

CEO 和 Eng 都指出 Stage 0 secret grep 只是 backup，不是 primary control；DX 又补了一刀，developer 现在连失败时该信哪份文档都说不清。trust boundary 和 trust communication 需要一起收口。

<!-- AUTONOMOUS DECISION LOG -->
## Decision Audit Trail

| # | Phase | Decision | Classification | Principle | Rationale | Rejected |
|---|-------|----------|----------------|-----------|-----------|----------|
| 1 | CEO | 选择 `SELECTIVE_EXPANSION`，不做 full scope expansion | Mechanical | P1 + P2 | 当前代码已足够支撑下一轮学习，最大缺的是 adoption proof，不是更多 surface area | Full expansion |
| 2 | CEO | `SB-2` 从 open blocker 语义上判为 stale | Mechanical | P3 + P5 | 代码和 dry-run 实测都表明能力已落地，继续保留 blocker 会污染执行顺序 | Keep as blocker |
| 3 | CEO | `SB-1` 保留在主线范围内 | Taste | P1 | 设计文档明确要求 hero surface 体现 plugin install；Codex 倾向把它拆成独立 release gate，因此记为 taste decision | Drop or fully defer `SB-1` |
| 4 | CEO | `FL-2` 作为 backup trust gate 保留 | Mechanical | P1 + P3 | secret scan 低成本、在 blast radius 内，但不能代替更高优先级 trust/audit story | Delete `FL-2` |
| 5 | CEO | 新增 `Adoption Proof` 顶层轨道 | User Challenge | P1 + P2 | 两个 outside voices 都认为当前 TODO 无法证明产品 pull，需要把 onboarding / query relevance / repeat use 拉进 top backlog | Keep current 4-item TODO as sufficient |
| 6 | Eng | `FL-1` 扩成 contract suite gate，而不是只盯 `test_start_scripts.py` | Mechanical | P1 + P3 | 实测 `test_start_scripts.py`、`test_plugin_contract.py`、`test_release_package.py` 于 2026-04-23 全红，CI 只跑一条已不代表真实产品 | Keep narrow gate |
| 7 | Eng | `SB-1` 需要先补 self-containment，再谈 hero-surface `plugin install` | User Challenge | P1 + P6 | 双声部都确认当前 plugin runtime 仍绑 repo checkout / demo venv；若不先切断，demo install 仍是假 parity | Keep `SB-1` as simple cp→install rewrite |
| 8 | Eng | `FL-2` 不升 primary blocker，但 trust / audit boundary 必须在 gate 上单独 surfaced | User Challenge | P1 + P6 | 两路 outside voice 都指向 daemon 写接口和 silent injection 风险更高；是否升 blocker 影响范围更大，交 final gate | Treat Stage 0 grep as sufficient trust story |
| 9 | Eng | adoption proof 必须绑定当前 `examples/` / `validation/` artifact，而不是口头 success metric | Mechanical | P1 + P5 | 现有 `run_human_AB.sh` 已过时，但骨架还在；最小增量是修 harness，不是另写新 PRD | Leave `AP-1` abstract |
| 10 | DX | 检测到明确 developer-facing scope，执行 Phase 3.5 而不是跳过 | Mechanical | P1 + P6 | plugin、commands、README、install flow 和 examples 都是开发者入口，跳过 DX 会漏掉 onboarding 真问题 | Skip DX review |
| 11 | DX | 把 clean-machine TTHW `<5` 分钟、`<=3` 个显式命令定成 acceptance gate | Mechanical | P1 + P5 | 双声部都认为当前 onboarding 太长且太模糊，必须给单一目标而不是“尽量更顺” | Keep TTHW target vague |
| 12 | DX | `/share-install` 必须二选一：要么真安装，要么改名成 verify / doctor | User Challenge | P1 + P5 | 命名与副作用不一致会直接损伤 developer trust，这不是文案小问题 | Keep current name and semantics |
| 13 | DX | docs / examples / tests / release drift 升级成 migration gate，而不是局部修文案 | Mechanical | P1 + P3 | 漂移横跨四个分发面，继续局部打补丁只会制造更多 false green / false red | Patch docs opportunistically |
| 14 | DX | env override、base URL 和 escape hatch 必须收敛成单一可发现入口 | Mechanical | P1 + P5 | override 现在主要藏在脚本和 fallback 里，developer 无法自助修复首轮失败 | Leave overrides implicit |
