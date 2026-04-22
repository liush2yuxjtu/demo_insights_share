# Proposal: insight 生成耗时优化 + agent self-verify 设计

> 日期：2026-04-22
> 状态：草稿（M6_LATENCY 候选）
> 对应原始问题：`proposal.md` 现状 #1 — claude /insights 生成耗时过长

## 问题（Situation）

`/insights` 生成走全链路 = `Stop hook → search_agent → adapter → injector`，
当前每次触发的 wall-clock 体验为 5–10s，原因：

1. `search_agent.py` 使用 MiniMax haiku，`max_turns=5`，串行做 4 层 wiki_tree 探索（`wiki_types.json → INDEX.md → <item>.md → raw/*.jsonl`），每层都是一次 SDK 调用；
2. `adapter.py` 再做一次 SDK 调用（`max_turns=2`），与 search 串行；
3. Stop hook 同步阻塞，命中前下一轮回复无法开始；
4. 命中卡片无 cache 反复读盘；
5. SDK 调用没有早退（score≥0.9 仍跑满 turns）；
6. `insightsd` daemon HTTP 7821 一应一答，无 batch / 无 keep-alive 复用；
7. 缺端到端 latency 指标，无法回归判定。

## 现况测量（基线）

> 测量口径：在 `start.demo.sh` 沙箱里跑 5 次同一 query，wall-clock 取 p50/p95，stage 拆分用 `insightsd.emitter` 已有事件流 + 新增 `latency_ms` 字段。

| Stage | 当前 p50 | 当前 p95 | 说明 |
|-------|----------|----------|------|
| `prefetch_hook` | ~50ms | ~150ms | 命中本地 cache 时极快 |
| `search_agent` | ~3500ms | ~6000ms | 占 wall-clock 60%–70%，是 1 号瓶颈 |
| `adapter` | ~1200ms | ~2200ms | 单次 SDK，turns=2 |
| `inject` | ~30ms | ~80ms | 文件 IO + statusline 更新 |
| **end-to-end** | **~5000ms** | **~9000ms** | 用户感知值 |

> 基线值会在 M6_LATENCY M0 阶段实测落盘到 `proposal/baselines/latency_baseline.json`，本表数字为设计估计。

## 目标

| 维度 | 当前 | 目标（M6 验收线） |
|------|------|-------------------|
| end-to-end p50 | 5000ms | **≤ 1500ms**（cache-hit）/ ≤ 3500ms（cache-miss） |
| end-to-end p95 | 9000ms | ≤ 3000ms（cache-hit）/ ≤ 6000ms（cache-miss） |
| `search_agent` p95 | 6000ms | ≤ 2500ms |
| `adapter` p95 | 2200ms | ≤ 1500ms |
| Stop hook 阻塞 | 同步 | 改为可配 async（默认 async） |

## 优化方案（按 ROI 排序）

| # | 方案 | 命中模块 | 预期省时 | 复杂度 |
|---|------|----------|----------|--------|
| O1 | **结果级 cache**：`hash(query+wiki_index_sha) → hits.json`，TTL 5min；命中跳 search_agent | `search_agent.py` 入口 | ~3500ms（cache-hit） | 低 |
| O2 | **layer-skip**：用 `topics.json` + `topic_id → item_path` 直接定位 layer-3，跳 `INDEX.md` 解析 | `search_agent.py` PROMPT | ~1500ms | 中 |
| O3 | **early exit**：Assistant 输出 SEARCH_HITS 围栏后立刻中止剩余 turns | `search_agent._run_async` | ~800ms | 低 |
| O4 | **search 与 adapter 并行**：search 拿到 top hit 立刻 stream 给 adapter，不等 ResultMessage | `insights_stop_hook.main` | ~1000ms | 中 |
| O5 | **async Stop hook**：fire-and-forget 后台跑，结果通过 `additionalContext` 注入下一轮（已是 SILENT_AND_JUST_RUN 语义自然吻合） | `insights_stop_hook` | 用户感知 → 0ms | 中 |
| O6 | **prefetch keep-warm**：SessionStart hook 拉 `topics.json` 进内存 + warm SDK 连接 | `hooks/session-start.sh` | ~300ms 首轮 | 低 |
| O7 | **embedding 预索引**：离线对所有 layer-3 卡片构建 embedding（MiniMax embedding API 或本地 BGE-small），search_agent 改用余弦 top-k 候选再让 haiku 二次精排 | 新文件 `embedder.py` | ~2000ms | 高 |
| O8 | **HTTP keep-alive + batch**：`insightsd` 7821 启用 connection reuse；卡片批拉 | `insightsd/server.py` | ~200ms | 低 |

> M6 MVP 必做：O1 + O3 + O5。M7 加 O2 + O4 + O6。M8 评估 O7 + O8。

## Self-verify 设计

### 1. 指标采集（`metrics`）

每条 stage 事件统一加字段：

```json
{"stage":"search","status":"ok","latency_ms":3421,"cache":"miss","turns":3}
```

落地：
- 文件：`~/.cache/insights-share/metrics/<YYYY-MM-DD>.jsonl`
- emitter：扩展 `insightsd.emitter.emit_from_env`，新增 `latency_ms / cache / turns / model` 字段
- 不打断既有事件契约，新字段全部 optional

### 2. 三层验证门（`gates`）

| Gate 名 | 检查内容 | PASS 条件 |
|---------|----------|-----------|
| `gate_baseline_recorded` | M6 MVP 之前必须先抓 5 轮基线写入 `baselines/latency_baseline.json` | 文件存在 + 含 ≥5 samples |
| `gate_p95_budget` | 优化后 p95 ≤ 目标线（按 cache-hit / cache-miss 两栏分别校验） | 全部目标线达标 |
| `gate_no_regression` | 与上一轮基线对比，任何 stage p95 不得上涨 > 10% | 全 stage 通过 |

Gate 实现：脚本 `plugins/insights-share/scripts/latency_gate.py`，输入 `metrics/<date>.jsonl` + `baselines/latency_baseline.json`，输出 PASS/FAIL JSON。

### 3. Agent-judge 双探针循环

对齐 `docs/rules/meta-self-verify.md` 的 fast-judge 模式：

```python
DESIGN_DOC = "proposal/proposal_generation_latency.md"
TARGET_BUDGET = {"p50_cache_hit_ms": 1500, "p95_cache_hit_ms": 3000,
                 "p50_cache_miss_ms": 3500, "p95_cache_miss_ms": 6000}
MAX_FAST_ROUNDS = 5

def iteration(round_idx: int) -> Verdict:
    # 1. probe：跑 N 轮真实 query（5 cache-miss + 5 cache-hit），收 metrics
    metrics = run_probe_queries(n_miss=5, n_hit=5)

    # 2. gate：本地脚本判 budget + regression
    gate = subprocess.run(["python", "scripts/latency_gate.py",
                           "--metrics", metrics, "--budget", json.dumps(TARGET_BUDGET)])
    if gate.returncode != 0:
        return Verdict("FAIL", reason=gate.stderr)

    # 3. judge：用 claudefast -p 当裁判，读 metrics + baseline + design doc
    probe_msg  = f"读取 {DESIGN_DOC}、metrics、baseline，判断 latency 优化是否真生效，输出 PASS/REFINE/FAIL JSON"
    verdict_json = run_claudefast_judge(probe_msg)
    return Verdict.from_json(verdict_json)

def main():
    for r in range(MAX_FAST_ROUNDS):
        v = iteration(r)
        if v.status == "PASS":
            return commit_and_record(v)
        if v.status == "FAIL":
            escalate_to_full_claude(v)   # 升级到 `claude -p`
            break
        # REFINE：调一个优化项再来
        apply_next_optimization()
    abort("M6_LATENCY 未达标，停止推进")
```

约束：
- **禁止硬编码关键词匹配**判 PASS，必须靠 `latency_gate.py` 的数值 + judge agent 的 JSON
- 连续 5 轮 fast 不收敛，自动升级 `claude -p` 托底（与 meta-self-verify.md 一致）
- 任何 round 后端到端 p95 上涨 > 10% 立刻 FAIL，回滚最近一项优化

### 4. 实机回归（与 start-demo-verify 对齐）

`start.demo.sh` 在 self-verify 段追加：

1. 跑 `latency_gate.py` 一次，把 PASS/FAIL 打印到 guide.log
2. statusline 增态 `[share ⏱ p95=Xms]`，hover/log 时给 PM 看一眼
3. 若 FAIL，guide.log 红字提示，但**不**自动回滚——把决策权留给开发者

### 5. 与既有规则对齐

| 既有规则 | 关系 |
|----------|------|
| `docs/rules/meta-self-verify.md` | 本文档复用其双探针约束；新增"数值 gate"作为前置门 |
| `docs/rules/start-demo-verify.md` | 本方案在 `start.demo.sh` self-verify 段插入新 gate |
| `proposal_statusline.md` | 复用三态契约，仅追加 `⏱` 数值徽章作为非阻塞补充信息 |
| `proposal_plugin_design.md` | M6_LATENCY 加入其 milestone 推进 for-loop |

## 里程碑

| milestone | 范围 | 验收 |
|-----------|------|------|
| `M6_LATENCY_BASELINE` | 落 `baselines/latency_baseline.json`、emitter 扩 `latency_ms` 字段、`latency_gate.py` 骨架 | `gate_baseline_recorded` PASS |
| `M6_LATENCY_MVP` | 实施 O1 + O3 + O5 | `gate_p95_budget`（cache-hit 线）+ `gate_no_regression` 双绿 |
| `M7_LATENCY_DEEP` | 实施 O2 + O4 + O6 | `gate_p95_budget`（cache-miss 线）达标 |
| `M8_LATENCY_INDEX` | 评估 O7 + O8，按 ROI 决定是否做 | 评估报告归档；不强制实施 |

## 风险与约束

| 风险 | 对策 |
|------|------|
| Cache 污染：旧卡片被反复命中 | cache key 含 `wiki_index_sha`，wiki 更新自动失效 |
| Async Stop hook 把命中卡片送到下一轮可能滞后一轮 | 在 statusline 加 `[share … N/today]` 中间态，明示 in-flight |
| Early exit 提前截断有效 turns，导致漏检 | gate 增加 recall 抽查：随机 10% 关掉 cache + early exit 跑完整路径，比对命中差异 |
| Embedding 预索引 (O7) 引入新依赖 | M8 评估阶段才决定是否落地，不进入 MVP |
| 指标文件无限增长 | `metrics/*.jsonl` 按日切，`latency_gate.py` 仅读最近 7 天 |
| CLAUDE.md / proposal/INDEX.md 改动 | 跑 `meta-self-verify.md` agent-judge 状态灯收尾 |

## 不做什么

- 不引入预测式预生成（除非 M8 决定做 embedding）
- 不动数据模型（`proposal_conflict_design.md` Topic-Good/Bad 并列契约保留）
- 不动 daemon 监听契约（保持 `0.0.0.0:7821`）
- 不在生产开 verbose log，避免 latency 副作用

## 验证

- 沙箱 `start.demo.sh` 跑完显示 `[share ✓ N/today] [share ⏱ p95=<X>ms]` 双徽章绿
- `python plugins/insights-share/scripts/latency_gate.py --metrics ... --budget ...` 退出码 0
- `claudefast -p` judge 探针返回 `{"verdict":"PASS"}`
- 仓库新增：`baselines/latency_baseline.json` + `metrics/<date>.jsonl` + `scripts/latency_gate.py`

## 推进进度

| 项 | commit | 状态 | 备注 |
|----|--------|------|------|
| baseline 骨架 | `d1f9ddc` | PASS | schema v1 + 预算 + tolerance |
| latency_gate.py | `974888e` | PASS | 3 gates + p95 + 退出码 |
| 首轮真 baseline（5-sample） | `53e112e` | PASS | search_agent p95=11908ms（pre-optimization） |
| O1 latency_cache 模块 | `0809e1c` | PASS | 13 tests 全绿；wiki_sha 失效 + TTL 300s |
| O3 search_agent early_exit | `1b7b689` | PASS | SEARCH_HITS 围栏一出即 break；metrics.early_exit=true/false |
| O5 async hook + cache 集成 | `bb59ff6` | PASS | fork+setsid 非阻塞；metrics 三行 jsonl；INSIGHTS_STOP_HOOK_ASYNC=0 可降级同步 |
| MVP gate PASS（cache-hit） | — | TODO | 实施完重跑 baseline |
