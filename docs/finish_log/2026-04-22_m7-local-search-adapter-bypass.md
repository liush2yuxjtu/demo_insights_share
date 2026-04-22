# Finish Log — M7 local_search 短路 + adapter bypass + 多主题优先级收官

日期：2026-04-22
关联 proposal：
- `proposal/proposal_generation_latency.md`（M7 gate 二轮，PARTIAL → PASS）
- `proposal/proposal_ceo_next_steps.md`（第 3 项多主题优先级，❓ → ✅ PASS）

## 改了什么

1. `insights-share/demo_codes/local_search.py`（新）
   - Jaccard token overlap（ASCII + CJK bigram）
   - `topics.json` + `<type>/INDEX.md` 候选合并去重
   - 排序：`score desc → priority desc → created_at asc`
   - 阈值 0.12：top 分数 ≥ 即 `source=local`（caller 短路），否则 `source=local_low`（退回 MiniMax）

2. `insights-share/demo_codes/search_agent.py`
   - 新 `_local_first`：本地预检索短路；命中发 `metrics stage=search / source=local`
   - `_sort_topics_by_priority`：`priority desc → created_at asc` 稳定排序
   - `_load_topics_payload`：注入时带 `priority` 字段；缺省 0；非法值归零

3. `insights-share/demo_codes/adapter.py`
   - 新 `_local_bypass`：card `source=local` 且 score ≥ 0.12 时不跑 SDK，
     合成 `AdapterResult(adopt)`，confidence = min(0.9, score+0.1)
   - ENV `INSIGHTS_ADAPTER_LOCAL_BYPASS=0` 可关

4. 测试：
   - `test_local_search.py`（13 tests）：token 切分、Jaccard、priority tiebreak、
     稳定性、10ms 延迟断言
   - `test_search_agent_priority.py`（3 tests + 重载保护）：
     payload 按 priority 排序、缺省 0、5 次连跑 identical

5. `proposal/baselines/latency_baseline.json` 新字段 `samples_post_m7_v2`：
   - cache-miss n=5 p50=24ms / p95=1059ms（budget 6000ms，18% 预算）
   - cache-hit  n=5 p50=11ms / p95=15ms（budget 3000ms，0.5% 预算）

6. `insights-share/demo_codes/capture_m7_post_local_search.py`（新）
   - 5+5 基线采样：先清一次 cache，5 个不同 query 天然 miss，
     cache 累积后再跑 hit round

## 证据

```bash
./.venv/bin/python -m pytest test_local_search.py test_search_agent_priority.py \
    test_latency_cache.py hooks/test_insights_stop_hook_latency.py -q
# 30 passed in 0.24s

./plugins/insights-share/scripts/latency_gate.py \
    --metrics /tmp/m7_metrics_v2.jsonl \
    --baseline proposal/baselines/latency_baseline.json
# verdict: PASS
# gates:
#   gate_baseline_recorded  PASS  (baseline has 5 samples)
#   gate_p95_budget         PASS  (adapter 0ms / inject 4ms / e2e_hit 15ms / e2e_miss 1059ms)
#   gate_no_regression      SKIP  (no previous baseline)
```

## 数值对比

| 指标 | 优化前 | 优化后 | 预算 |
|------|--------|--------|------|
| end_to_end cache-miss p95 | 12314ms | 1059ms | 6000ms |
| end_to_end cache-hit p95 | 1ms | 15ms | 3000ms |
| search_total miss p95 | 11908ms | 26ms | 2500ms |
| adapter miss p95 | ~9000ms | 0ms | 1500ms |
| inject miss p95 | <10ms | 4ms | 120ms |

12× 延迟下降（e2e miss）；两条关键 SDK 调用被 local 短路消灭。

## Proposal 状态

| proposal | 状态 |
|----------|------|
| `proposal_conflict_design.md` | ✅ 已落地 |
| `proposal_wiki_card.md` | 📝 现状文档（非目标） |
| `proposal_statusline.md` | ✅ 已落地 |
| `proposal_plugin_design.md` | ✅ M1–M5 全部 PASS |
| `proposal_rename_to_insights_share.md` | ✅ 已落地 |
| `proposal_ceo_next_steps.md` | ✅ 三项全部 PASS（本次收尾第 3 项） |
| `proposal_generation_latency.md` | ✅ MVP + M7 全部 PASS（本次收尾 M7） |

## Commits

- `87acecf` — feat: M7 local_search 短路 + topics priority 固化
- `562c7d4` — feat: M7 adapter bypass + gate PASS + CEO 多主题优先级收官
- `0b5835f` — test: fix order-dependency in test_search_agent_priority
