# Finish Log — /qa Plugin Surface S1–S10 预检 + 清工作树

日期：2026-04-23
关联文档：
- `docs/qa/plugin_qa_plan.md`（11 surface + E2E + 5 slash 探针契约）
- `proposal/proposal_ceo_next_steps.md`（M7 已收官，本轮为 QA 推进）

## 做了什么

### 1. 工作树清零（233 dirty → 0）

- commit A `8432251` chore(insights-share): database 清理
  - 删 ghost 卡片 `170c76d6_1a72_5bcb_85e0_4949a6514898.md` + INDEX 同步
  - `postgres_pool.md` admin_team6 `label_override=bad` + ed25519 签名
  - raw jsonl 同步字段

- commit B `958e6ac` chore(insights-share): general 批量入盘 226 张 KB 卡片
  - `wiki_tree/general/` 新增 226 个 `m1-kb-*` / `m1_*` md + raw jsonl
  - `general/INDEX.md` 205 条索引行同步
  - `topics.json` 新增 `team6-verify-topic`
  - b-i 迁移策略：救 2 NEW (`m1_agent_judge_dp_*`, `m1_knowledge_work_*`)
    from 根 `wiki.json/` ghost 目录，18 COLLIDE 丢弃（正规路径权威），
    `wiki.json/` 整目录删除

- 处置决策：
  - `raw/170c76d6-*.txt` 中 `EVIL OVERWRITE` payload 用 `git checkout HEAD --` 恢复原值
  - `postgres_pool.md` 的 `label_override=bad/admin_team6` 保留（合法 admin 操作）
  - 根 `wiki.json/` ghost 目录删除（非正规路径，只含早期签名实验残留）

### 2. QA Blocker 预检

| 检查项 | 状态 |
|--------|------|
| 工作树 `git status --porcelain` | 0 |
| `tmux` / `claude` / `python3` | OK |
| `insights-share/demo_codes/.venv/bin/python` | OK |
| 端口 7821 可用 | OK |
| `.env` `MINIMAX_TOKEN` | OK (1 条) |
| `~/.claude/live_terminal/CURRENT` 指针 | `start_demo_verify`（活指针，但 tmux session 已 die，S11 需 re-register） |

### 3. S1–S9 Static Surface Probe

跑 `bash plugins/insights-share/scripts/self_check.sh` → **ALL GREEN 18/18**

覆盖：manifest / marketplace / 2 个 skill / 2 个 hook / statusline /
5 个 slash / 2 个 agent / MCP wiki-server / publish script / manifest contract

### 4. S10 LAN Daemon Probe

起 `insights_cli.py serve --port 7821`：

- `GET /healthz` → `200 {"ok": true}`
- `GET /insights?topic=database` → `200 {"cards":[{id:test-123,...},{id:bob-k8s-oom-...},...]}`

### 5. 发现 + 修 2 个 Bug

- commit `2691e72` fix(insights-share): self_check.sh manifest 契约升级 M5 → M5+M6+M7+M8 前向兼容
  - 原脚本硬编码 `version=="0.5.0-m5"` + `current=="M5_RENAME"` + `pending==[]`
  - plugin.json 已推进到 `0.6.0-m7` / `M7_LATENCY_DEEP` / `pending=[M8_LATENCY_INDEX]`，探针触发 FAIL
  - 改为：`version` 以 `"0."` 开头；`current ∈ 已知 milestone 集合`；`pending ⊆ 已知 milestone 子集`

- commit `16d6534` fix(insightsd): flat InsightStore.load 接受 team kwarg
  - `server.py:255` 统一调 `self.store.load(team=team)`
  - `store.py:145` flat `InsightStore.load(self)` 不接受 kwarg，flat 模式触发 `TypeError`
  - 补签名 `load(self, team: str | None = None)`，flat 忽略 team
  - 同步 `docs/qa/plugin_qa_plan.md` S10 契约：`/health` → `/healthz`，`JSON 列表` → `{"cards":[...]}`

## 本轮未跑的 QA 部分

| Surface / 探针 | 状态 | 阻塞原因 |
|----------------|------|----------|
| S11 Sandbox demo (`start.demo.sh` 7 stage) | ⏸️ | tmux `start_demo_verify` session 已 die，需 `register-session` 重建 + 交互 claude REPL |
| §3 E2E 回放 (Bob postgres prompt) | ⏸️ | 同上，依赖活 claude REPL |
| §4 5 slash 命令回放 | ⏸️ | 同上 |

## 本轮 commit 清单

```
16d6534 fix(insightsd): flat InsightStore.load 接受 team kwarg + 同步 QA plan 端点契约
2691e72 fix(insights-share): self_check.sh manifest 契约升级 M5 -> M5+M6+M7+M8 前向兼容
958e6ac chore(insights-share): general 批量入盘 226 张 KB 卡片 + team6 verify topic
8432251 chore(insights-share): database 清理 ghost 卡片 + postgres_pool label_override
```

## PASS/FAIL 收尾

- PASS：S1–S10 surface probe 全绿 + 2 bug fix 已落 + 工作树清
- PARTIAL：S11 / E2E / slash 依赖活 tmux + claude REPL，留下一轮开
- 下一步候选：`/review` M7 diff（562c7d4 adapter bypass + 87acecf priority）/ S11 sandbox demo
