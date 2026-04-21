# Code Review Request: Topic Wiki Implementation

## Commit ID
```
fa73f185944ba09abe08b3b955689b76cf516ac4
```

## Plan Reference
`.claude/plans/ethereal-bubbling-cray.md` — Topic 中心 Good/Bad 示例 Wiki

---

## Changed Files (to review)

### Core Implementation (MODIFIED)
| File | What Changed |
|------|--------------|
| `insights-share/demo_codes/insightsd/store.py` | 新增 `list_topics`/`create_topic`/`list_examples`/`relabel`/`effective_label` 方法；`_write_card` 支持 `raw_log_type`；`_item_to_card`/`_render_item_md` 扩展新字段 |
| `insights-share/demo_codes/insightsd/server.py` | 新增 `GET/POST /topics`、`GET /topics/{id}/examples`、`POST /insights/{id}/relabel` 端点 |
| `insights-share/demo_codes/insights_cli.py` | 新增 `topic-create`/`topic-list`/`topic-show`/`relabel` 子命令 |
| `insights-share/demo_codes/insightsd/dashboard.html` | 新增 Topics tab，含 GOOD/BAD 分组和 admin override 标注 |

### Seeds & Data (MODIFIED)
| File | What Changed |
|------|--------------|
| `insights-share/demo_codes/seeds/alice_pgpool.json` | 新增 `topic_id`/`label`/`raw_log_type` 字段 |
| `insights-share/demo_codes/seeds/alice_celery_retry.json` | 新增 `topic_id`/`label` 字段 |
| `insights-share/demo_codes/seeds/carol_redis_eviction.json` | 新增 `topic_id`/`label` 字段 |

### Wiki Tree (MODIFIED)
| File | What Changed |
|------|--------------|
| `insights-share/demo_codes/wiki_tree/database/postgres_pool.md` | 补齐新字段 |
| `insights-share/demo_codes/wiki_tree/database/raw/alice-pgpool-2026-04-10.jsonl` | raw 文件更新 |
| `insights-share/demo_codes/wiki_tree/wiki_types.json` | 类型配置 |

### Tests (MODIFIED)
| File | What Changed |
|------|--------------|
| `insights-share/validation/test_examples_demo_scripts.py` | 新增 bob id 断言 |

---

## New Files (to review)

### Core Implementation (NEW)
| File | Description |
|------|-------------|
| `insights-share/demo_codes/wiki_tree/topics.json` | 3 个 topic 元数据（pgpool/celery/redis-eviction） |
| `insights-share/demo_codes/seeds/bob_pgpool_bad.json` | Bob bad example，topic_id=postgres-pool-exhaustion |
| `insights-share/validation/test_topic_store.py` | 9 个 Store 层单元测试 |
| `insights-share/validation/test_topic_api.py` | 6 个 HTTP API 测试 |
| `insights-share/validation/migrate_add_topic_fields.py` | 老卡迁移脚本 |
| `examples/run_topic_walkthrough.sh` | Topic 工作流演示脚本 |
| `examples/topic_walkthrough.human.md` | 演示记录模板 |
| `examples/topic_walkthrough.log` | 演示执行日志 |
| `examples/COMMON_PROMPT.txt` | A/B prompt 模板 |

### Docs (NEW)
| File | Description |
|------|-------------|
| `proposal_conflict_design.md` | 用户设计文档 |
| `proposal_wiki_card.md` | Wiki card 冲突合并设计 |
| `docs/designs/` | 设计文档目录 |

---

## Test Results
```
test_topic_store.py: 9 passed
test_topic_api.py:   6 passed
```

---

## Review Focus Areas

1. **Store 层** — `relabel()` 是否正确地只写 .md 不碰 raw/；`raw_log_type=export` 写 .txt，`jsonl` 写 .jsonl
2. **API 层** — 新端点是否正确调用 store 方法，返回格式是否一致
3. **CLI 层** — `topic-show` 是否正确分组 GOOD/BAD；`relabel` 是否显示 effective_label 变化
4. **Dashboard** — Topics tab 是否正确调用 API，是否正确显示 admin override 标注
5. **Seeds** — alice good + bob bad 是否真的在同 topic 下并存
6. **向后兼容** — 老卡（无新字段）是否仍可读

---

## Verification Commands
```bash
cd /Users/m1/projects/demo_insights_share

# Start server
cd insights-share/demo_codes
python insights_cli.py serve --host 0.0.0.0 --port 7821 --store ./wiki_tree --store-mode tree &

# API tests
curl -s http://127.0.0.1:7821/topics | jq .
curl -s 'http://127.0.0.1:7821/topics/postgres-pool-exhaustion/examples?label=good' | jq .
curl -s 'http://127.0.0.1:7821/topics/postgres-pool-exhaustion/examples?label=bad' | jq .

# CLI tests
python insights_cli.py topic-list
python insights_cli.py topic-show postgres-pool-exhaustion
python insights_cli.py relabel bob-pgpool-bad-2026-04-12 --to good --by admin

# Run walkthrough
bash examples/run_topic_walkthrough.sh
```
