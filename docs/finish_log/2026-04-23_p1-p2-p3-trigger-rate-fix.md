# Finish Log — P1/P2/P3 触发率修复：flat→tree + Jaccard→tag_bonus + threshold 校准

日期：2026-04-23
触发：用户 `do all of 3 please` → 接 `docs/finish_log/2026-04-23_qa-static-plus-demo-verify.md` A5 实测 gap "claude 答 未引用任何 LAN 卡片"
关联：
- `proposal/proposal_conflict_design.md`（topic 中心 Good/Bad）
- `insights-share/validation/trigger_cases/cases.yml`（20 cases dataset）
- `validation.md §1`（触发率门禁）

## 根因 root cause

A5 实测 "未引用任何 LAN 卡片" 根因不是 hook bug，而是两层错配：

1. **数据层错配**：`start.demo.sh` 启 daemon 用 `--store wiki.json --store-mode flat`（200 张 m1-* 卡），但 `cases.yml` 的 expected_card_id 是 `alice-pgpool-2026-04-10` / `alice-celery-retry-2026-04-08` / `carol-redis-eviction-2026-03-27`，这 3 张 canonical 只存在 `wiki_tree/*/raw/` + 对应 `*.md` 里，flat store 根本加载不到。
2. **算法层瑕疵**：`search_cards` 纯 Jaccard `|inter|/|union|` 惩罚长卡过重（alice-pgpool 41 tokens vs m1-project-001 7 tokens），信息更丰富的 canonical 被精简短卡反超；同时 `carol-redis-eviction` 的 `do_not_apply_when` 长句含 `"dedicated Redis or Postgres"` 产生 noise token，carol 会借 coverage 假命中 postgres query。

## P1：数据层 + 算法层 + 门槛校准（三合一）

### P1a：start.demo.sh 切 tree mode（commit `b6d399c`）

```diff
-      --store wiki.json --store-mode flat \
+      --store wiki_tree --store-mode tree \
```

tree mode 加载 `wiki_tree/` 目录 **258 张** md 卡（非 INDEX.md），含 canonical 3 张 + 其他 wiki_type md。

### P1b：search_cards 加 tag_bonus（commit `063cee0` + `test_search_ranking.py`）

```python
# 旧：score = |inter| / |union|  # 长卡惩罚过重
# 新：score = jaccard + 0.15 * tag_hit_count
#   tag_hit_count = |query ∩ _tokenize(card.tags)|
```

保留 Jaccard 对短精准卡的友好度，tag_bonus 用 tags 高信号字段（noise-free）线性加权。丢弃 coverage（会让长 noise 卡伪命中）。

### P1c：trigger_rate.py 默认 threshold 0.02 → 0.05（commit `d27e7a3`）

实测 sweep：
| threshold | train f1 | test f1 | train FP |
|---|---|---|---|
| 0.02 | 0.5333 | 0.75 | 5 |
| **0.05** | **0.6667** | **0.75** | **2** |
| 0.08 | 0.4444 | 0.5714 | 1 |
| 0.10 | 0.4444 | 0.4 | 1 |

0.05 是 precision-recall 最佳平衡点。

### P1d：insights_prefetch.py 优先调 daemon /search（commit `4655457`）

旧 hook：GET `/insights` 全量 cards → 客户端 `_score_card` token 重叠本地打分
新 hook：GET `/search?q=<prompt>&k=3` 先拿 server-side ranking (含 tag_bonus)，失败才回退本地

sandbox 内 UserPromptSubmit 触发时，daemon ranking 直接命中 canonical，跳过客户端 noise。

## P2：trigger_rate 端到端实测（commit `6903043`）

3 份 report 落盘对比：

| stage | report | train f1 | test f1 | train TP | train FN | test TP | test FN |
|---|---|---|---|---|---|---|---|
| **baseline** (flat mode) | `trigger_rate_baseline_qa_2026-04-23.json` | 0.0 | 0.0 | 0 | 6 | 0 | 4 |
| **tree mode only** (P1a 单项) | `trigger_rate_tree_mode_qa_2026-04-23.json` | 0.5333 | 0.75 | 4 | 2 | 3 | 1 |
| **P1 final** (tree + tag_bonus + threshold 0.05) | `trigger_rate_after_P1_2026-04-23.json` | **0.80** | **0.75** | **6** | **0** | 3 | 1 |

关键数字：
- **train recall = 1.0**（6/6 canonical positive 全 TP，无遗漏）
- train f1 从 0.0 飙到 0.80
- test f1 保持 0.75

剩余缺口（可继续优化，超出本轮范围）：
- t10 FN：`session not found for keys written 5 min ago` → 模型抢走 carol-redis-eviction top1（m1-kb-ao-012）
- t12 FP：`git rebase squash` → m1-atomic-commit 假命中（tags 含 commit/rebase 噪声）
- t19 FP：`k6 load test HMAC` → m1-json_文件逐行处理 假命中

## P3：HTTP 端到端 integration test（commit `1eef893`）

`insights-share/demo_codes/test_search_http_integration.py` 起独立端口 7841 tree-mode daemon，覆盖 6 个断言：

| test | 断言 |
|---|---|
| `test_healthz_alive` | /healthz 返 `{ok:true}` |
| `test_insights_returns_canonical_seeds` | /insights 必须含 3 张 canonical id |
| `test_postgres_checkout_query_top1_alice_pgpool` | t01 query → alice-pgpool top1 |
| `test_celery_retry_query_top1_alice_celery` | t05 query → alice-celery-retry top1 |
| `test_redis_eviction_query_top1_carol_redis` | t08 query → carol-redis-eviction top1 |
| `test_unrelated_tailwind_query_no_canonical_top1` | t11 negative → canonical 不得 top1 |

pytest 结果：**6 passed in 1.32s** ✓

加 `test_search_ranking.py` unit test 6 条，覆盖 search_cards 纯函数层。

## 全量测试回归

```
./.venv/bin/python -m pytest insights-share/demo_codes/ -q
→ 46 passed in 1.94s
```

新增 12 test（6 unit + 6 HTTP integration），原 34 test 零回退。

## commit trail

```
6903043 docs(validation): trigger_rate 三份 report baseline/tree-only/P1-final 证据
4655457 feat(insights-share): insights_prefetch.py 优先调 daemon /search
d27e7a3 fix(validation): trigger_rate.py 默认 threshold 0.02 -> 0.05
b6d399c fix(demo): start.demo.sh daemon 切 tree mode
1eef893 test(insightsd): HTTP 端到端 integration test (P3)
063cee0 fix(insightsd): store.py search_cards Jaccard + tag_bonus + unit test
```

## PASS / FAIL 总结

| 目标 | before | after | 证据 |
|---|---|---|---|
| P1 修 hook/prefetch 让 postgres prompt 命中 canonical | "未引用任何 LAN 卡片" | /search top1 = alice-pgpool ✓ | `test_search_http_integration.py::test_postgres_checkout_query_top1_alice_pgpool` |
| P2 真跑 20 触发用例出数 | flat mode f1=0.0 / 0.0 | tree+tag_bonus f1=0.80 / 0.75 | 3 份 report JSON + commit `6903043` |
| P3 回归测 sandbox 必引用 canonical | 无测试 | 6 HTTP + 6 unit passed | commit `1eef893` + `063cee0` |

**裁决：PASS**（三目标全达成 + 零已有测试回退）

## 下一步候选（non-goals of 本轮）

| 优先级 | 动作 |
|---|---|
| 后续 P4 | 攻 t10 FN（redis eviction query 被 m1-kb-ao-012 截胡）：可能需 stem 改进或 stop-word 扩展 |
| 后续 P5 | 攻 t12/t19 FP：tags noise 压制（对 m1-* 系列降权，或引 IDF） |
| 后续 P6 | validation.md §1 加硬 gate：CI/pre-commit 上跑 trigger_rate, f1 < 0.7 拒合并 |

## 复现

```bash
# 用 tree mode 起独立 daemon 验
cd insights-share/demo_codes
.venv/bin/python insights_cli.py serve --host 127.0.0.1 --port 7831 --store wiki_tree --store-mode tree &
sleep 3

# 跑 trigger_rate (应见 train f1=0.80)
cd ../..
./insights-share/demo_codes/.venv/bin/python insights-share/validation/trigger_rate.py --wiki http://127.0.0.1:7831

# 跑回归 test suite
cd insights-share/demo_codes
./.venv/bin/python -m pytest test_search_ranking.py test_search_http_integration.py -v
```
