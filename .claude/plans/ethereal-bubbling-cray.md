# Plan：Topic 中心 Good/Bad 示例 Wiki（proposal_conflict_design.md 落地）

## Context

`proposal_conflict_design.md`（用户设计）把 wiki 的组织轴从"insight card"改为"Topic 下的 Example"，每个 Example 由上传者自行标 `good` / `bad`，同一 Topic 下多条 Example 并存，不走 merge。这是对现有"冲突卡片 merge"思路（`proposal_wiki_card.md`）的替代，核心价值是：让 Alice 的成功经验和 Bob 的反面教材以对等方式共存，消费者能同时看到两份带完整 raw_log 的实战证据，而不是被系统合并/覆盖掉一份。

用户四个关键决策：
1. **schema 扩展**：在现有 card 基础上加字段，不替换旧 API（兼容 seeds/wiki_tree）。
2. **raw_log 独立文件 + 路径引用**：`raw/<example_id>.txt` 或 `.jsonl`，不 inline 到 .md。
3. **全量 MVP**：后端 + dashboard + 新 A/B demo。
4. **无认证，CLI relabel**：`label` 由上传者定，管理员用 CLI 命令改；**没有 label merge**。

交付成果：一条 Alice good + Bob bad 的同 Topic 并存示例，能被 server 列出、检索、relabel、在 dashboard 按 label 分组显示，并通过新 A/B demo 在 B 轮把两份 Example 一起注入缓存。

---

## 设计决策摘要

| 维度 | 决策 |
|------|------|
| Topic 粒度 | 作为**逻辑聚合维度**，不替换 `wiki_type` 物理目录；Topic 用字段 `topic_id`（slug）+ 独立 `topics.json` 元数据 |
| Example | 复用现有 card dict，**新增字段** `topic_id` / `label` / `label_note` / `label_override_*` / `raw_log_type` |
| 物理布局 | 继续 `wiki_tree/<wiki_type>/<slug>.md`，raw 文件继续放 `wiki_tree/<wiki_type>/raw/`，**扩展名按 raw_log_type**（`.txt` 或 `.jsonl`） |
| API | 在现有 `/insights*` 端点旁新增 `/topics` 系列；旧端点保持兼容 |
| Relabel | 走 HTTP `POST /insights/{id}/relabel`，只由 CLI 调用；无 auth 检查（与其他 POST 一致） |
| Seeds | 把现有 3 张卡补齐新字段，再新增 1 张 `bob-pgpool-bad-*`（bad Example）构成并存对照 |
| Demo | `run_human_AB.sh` B 轮预热 2 张 pgpool Example；新增 `examples/run_topic_walkthrough.sh` 展示 relabel CLI 流程 |

---

## Schema 扩展

### Example（即 card）新增字段

```json
{
  "id":                "alice-pgpool-2026-04-10",
  "topic_id":          "postgres-pool-exhaustion",    // NEW：必填
  "label":             "good",                         // NEW：good | bad
  "label_note":        "在 PgBouncer transaction mode 下彻底解决",  // NEW：可空
  "label_override":    null,                           // NEW：admin 改后写这里
  "label_override_by": null,                           // NEW
  "label_override_at": null,                           // NEW (ISO8601)
  "raw_log_type":      "export",                       // NEW：export | jsonl
  "raw_log":           "./raw/alice-pgpool-2026-04-10.txt"  // 路径随 type 变
  // 其余字段（title/author/tags/context/symptom/root_cause/fix/...）保持不变
}
```

**有效 label（检索侧用）**：`effective_label = label_override or label`。

### Topic 元数据（新增独立文件）

`insights-share/demo_codes/wiki_tree/topics.json`：
```json
{
  "topics": [
    {
      "id": "postgres-pool-exhaustion",
      "title": "PostgreSQL 连接池耗尽",
      "tags": ["postgres", "connection-pool", "latency"],
      "created_by": "alice",
      "created_at": "2026-04-10T08:00:00Z",
      "wiki_type": "database"
    }
  ]
}
```

不建 `topics/` 子目录——只加一层 JSON 索引即可；Example 与 Topic 通过 `topic_id` 关联。

---

## Store 层改动（`insights-share/demo_codes/insightsd/store.py`）

### 新增方法 `TreeInsightStore`

| 方法 | 行为 |
|------|------|
| `_load_topics()` / `_save_topics()` | 读写 `wiki_tree/topics.json` |
| `create_topic(topic: dict)` | append 到 `topics.json`，`id` 去重 |
| `list_topics()` | 返回全部 topic 元数据 |
| `list_examples(topic_id, label=None)` | 按 `topic_id` + 可选 `effective_label` 过滤 `load()` 结果 |
| `relabel(card_id, new_label, override_by)` | 写 `label_override` / `label_override_by` / `label_override_at`，回写 .md 和 raw；**不动 raw_log 内容** |

### 修改现有逻辑

- `_write_card()`（store.py:408）：
  - 识别 `raw_log_type`；`export` → 写 `raw/<id>.txt`（整段 /export 文本），`jsonl` → 写 `raw/<id>.jsonl`（复制原始 .jsonl 内容，而非 card dict 序列化）
  - `card["raw_log"]` 记录相对路径，扩展名随 type
  - 保留原来 `.jsonl` 精简 card 备份的**兼容读取**，但新写入全部按新规则
- `_item_to_card()`（store.py:311）：frontmatter 里读取新字段，若缺失则用默认值 `label="good"`、`topic_id=""`（保证老卡可读）
- `_render_item_md()`：在 frontmatter 追加新字段；正文新增 `## Raw log` 章节，仅写一句"see {raw_log}"指向文件，不 inline
- `search()`：把 `effective_label` 写入结果项，便于 UI 过滤；不改 Jaccard 逻辑
- `migrate` 辅助函数（新增，仅给 CLI/测试用）：把老 card 自动补 `topic_id = slug.replace("_","-")`、`label = "good"`、`raw_log_type = "jsonl"`

### 迁移现有 raw 文件

写一个一次性脚本 `insights-share/validation/migrate_add_topic_fields.py`：遍历 `wiki_tree/<type>/*.md`，给缺失字段补默认值；不动已有 `raw/*.jsonl`（老格式继续被读取）。新 Example 用新路径格式写入。

---

## Server API 改动（`insights-share/demo_codes/insightsd/server.py`）

### 新增端点

| 方法 | 路径 | Body / Query | 返回 |
|------|------|--------------|------|
| `GET` | `/topics` | — | `{"topics": [...]}` |
| `POST` | `/topics` | `{id, title, tags, wiki_type}` | `{"id": "..."}` |
| `GET` | `/topics/{topic_id}/examples?label=good` | label 可选 | `{"examples": [cards]}` |
| `POST` | `/insights/{id}/relabel` | `{label: "bad", override_by: "admin"}` | `{"id": "...", "effective_label": "bad"}` |

**不新增** `/topics/{topic_id}/examples` POST 端点——复用现有 `POST /insights`，只要 body 带 `topic_id` / `label` / `raw_log_type` 即可（提案原写法是 POST /topics/{id}/examples，但用户选了 schema 扩展路径，统一走 /insights 更一致）。

### 现有端点保持

`GET /insights` / `GET /search` / `POST /insights` / `POST /insights/merge` / `POST /insights/{id}/edit` 全部不动。`GET /search` 结果自动带上 `effective_label` 字段；消费者（adapter）无需改动即可工作。

### 关于 merge

用户明确"there is no label merge"。**保留** `/insights/merge` 端点（它合的是 context/fix 文本，跟 label 无关），但 dashboard 的 Topic 视图不暴露 merge 按钮，避免误导。

---

## CLI 改动（`insights-share/demo_codes/insights_cli.py`）

新增子命令：

```
# Topic 管理
insights_cli topic-create <topic_id> --title <T> --tags a b c --wiki-type database
insights_cli topic-list
insights_cli topic-show <topic_id>                    # 列所有 Example，按 label 分组

# Example 发布（复用 publish，card JSON 带新字段即可；无需新 CLI）
insights_cli publish seeds/bob_pgpool_bad.json

# 管理员 relabel（本次重点）
insights_cli relabel <card_id> --to good|bad --by <name>
```

实现位置：在 `cmd_publish` / `cmd_merge` 之间新增 `cmd_topic_create` / `cmd_topic_list` / `cmd_topic_show` / `cmd_relabel`，全部用现有 `_http_get` / `_http_post_json` 即可，无新依赖。`build_parser()` 里注册对应 `sub.add_parser(...)`。

---

## Seeds 与数据

### 改动现有 seeds

补齐新字段（不改原有语义）：
- `seeds/alice_pgpool.json` → 加 `topic_id: "postgres-pool-exhaustion"`, `label: "good"`, `raw_log_type: "jsonl"`
- `seeds/alice_celery_retry.json` → `topic_id: "celery-retry-storm"`, `label: "good"`
- `seeds/carol_redis_eviction.json` → `topic_id: "redis-allkeys-lru-evicts-session"`, `label: "bad"`（原本就是反例）

### 新增 seed

`seeds/bob_pgpool_bad.json`：
- `id: "bob-pgpool-bad-2026-04-12"`
- `topic_id: "postgres-pool-exhaustion"`（与 alice 同 Topic）
- `label: "bad"`
- `label_note: "直接把 pool size ×5 在我们 32 核机器上反而拖垮 IO"`
- `raw_log_type: "export"`，raw 文件内容使用 `export_template.txt` 格式的简短对话
- 其余 context/symptom/fix 写成"增 pool size 失败"的反面故事

### topics.json 初始内容

3 个 topic（pgpool / celery / redis-eviction），从上述 seeds 推导出。

---

## Dashboard UI 改动（`insights-share/demo_codes/insightsd/dashboard.html`）

单页 HTML，新增一个"Topics"视图 tab：
- 调用 `GET /topics` 列左侧 Topic 列表
- 点击 Topic → 调用 `GET /topics/{id}/examples` 分成两列：**GOOD** 和 **BAD**
- 每张 Example 卡片显示 id/author/label_note/raw_log 路径链接
- 提供只读 `effective_label` 角标（如果被 override 过，显示"admin override: bad ← good"）
- **不加 relabel 按钮**（用户要求只能 CLI 改）

原有卡片视图保留不动，通过顶部 tab 切换。

---

## 新 Demo 流程

### `examples/run_human_AB.sh` 小改

B 轮启动 server 后，除了 `publish alice_pgpool.json`，再 publish `bob_pgpool_bad.json` + `topic-create postgres-pool-exhaustion`。`insights_prefetch.py` hook 现有逻辑（`GET /insights`）会自动把 2 张卡一起拉到缓存，B 导出里应该能同时看到 alice 和 bob 两张 id 的引用。

`COMMON_PROMPT.txt` 保持不变（A/B equality gate 不能碰），但期望 B 回答里出现"两种策略并存"的表述。

### 新增 `examples/run_topic_walkthrough.sh`

线性演示 Topic 工作流：
```
1. 启动 server（tree mode）
2. insights_cli topic-create postgres-pool-exhaustion ...
3. insights_cli publish alice_pgpool.json     # good
4. insights_cli publish bob_pgpool_bad.json   # bad
5. insights_cli topic-show postgres-pool-exhaustion   # 看到 1 good + 1 bad
6. insights_cli relabel bob-pgpool-bad-2026-04-12 --to good --by admin
7. insights_cli topic-show postgres-pool-exhaustion   # bob 现在显示 override: good ← bad
8. curl dashboard /topics → 截图存 examples/topic_dashboard.png
```

产物：`examples/topic_walkthrough.log` + `examples/topic_walkthrough.human.md`（用 `claude_session_export.py` 风格的简单 txt）。

---

## 测试

### 单元（pytest，放在 `insights-share/validation/`）

新建 `test_topic_store.py`：
- `test_topic_create_and_list`
- `test_publish_example_with_topic_id_persists_label`
- `test_list_examples_by_label_filters_correctly`
- `test_relabel_sets_override_fields_preserves_raw_log`
- `test_effective_label_in_search_results`
- `test_raw_log_txt_written_for_export_type`
- `test_raw_log_jsonl_copied_verbatim_for_jsonl_type`
- `test_legacy_card_without_new_fields_still_readable`（迁移兼容）

新建 `test_topic_api.py`：
- 起一个 `TreeInsightStore` + `ThreadingHTTPServer`（参考现有 test 模式），对新端点做 HTTP 级别断言

### 现有测试更新

`insights-share/validation/test_examples_demo_scripts.py`：
- 增加断言：`B_with.human.md` 中同时出现 `alice-pgpool-2026-04-10` 和 `bob-pgpool-bad-2026-04-12`
- 不改现有 A/B prompt equality gate（validation_AB.md 的硬门禁）

### 跑法

```bash
cd /Users/m1/projects/demo_insights_share
.venv/bin/pytest insights-share/validation/test_topic_store.py -v
.venv/bin/pytest insights-share/validation/test_topic_api.py -v
.venv/bin/pytest insights-share/validation/test_examples_demo_scripts.py -v
```

---

## 端到端验证步骤

```bash
# 1. 启动 tree-mode server
cd insights-share/demo_codes
.venv/bin/python insights_cli.py serve --host 0.0.0.0 --port 7821 \
    --store ./wiki_tree --store-mode tree &

# 2. Topic + Example 发布
.venv/bin/python insights_cli.py topic-create postgres-pool-exhaustion \
    --title "PostgreSQL 连接池耗尽" --tags postgres connection-pool --wiki-type database
.venv/bin/python insights_cli.py publish seeds/alice_pgpool.json
.venv/bin/python insights_cli.py publish seeds/bob_pgpool_bad.json

# 3. 读端验证
curl -s http://127.0.0.1:7821/topics | jq
curl -s 'http://127.0.0.1:7821/topics/postgres-pool-exhaustion/examples?label=good' | jq
curl -s 'http://127.0.0.1:7821/topics/postgres-pool-exhaustion/examples?label=bad' | jq
curl -s 'http://127.0.0.1:7821/search?q=postgres+pool&k=3' | jq '.hits[].effective_label'

# 4. Relabel CLI 流
.venv/bin/python insights_cli.py relabel bob-pgpool-bad-2026-04-12 --to good --by admin
.venv/bin/python insights_cli.py topic-show postgres-pool-exhaustion
# 预期：bob 显示 label_override=good, label=bad

# 5. raw_log 完整性
cat wiki_tree/database/raw/alice-pgpool-2026-04-10.jsonl | head
cat wiki_tree/database/raw/bob-pgpool-bad-2026-04-12.txt | head
# 预期：relabel 前后，raw_log 文件哈希不变

# 6. Dashboard 验收
open http://127.0.0.1:7821/
# 在 Topics tab 下看到 1 个 Topic、GOOD/BAD 各 1 张

# 7. 新 A/B demo
bash examples/run_topic_walkthrough.sh
bash examples/run_human_AB.sh    # 仅当 claude CLI 在 PATH 时
```

每步都要在终端 log 里看到 `[green] ok`，`examples/topic_walkthrough.log` 里 grep `effective_label` 应同时出现 good 和 bad。

---

## 关键修改文件清单

**新增**
- `insights-share/demo_codes/wiki_tree/topics.json`
- `insights-share/demo_codes/seeds/bob_pgpool_bad.json`
- `insights-share/validation/test_topic_store.py`
- `insights-share/validation/test_topic_api.py`
- `insights-share/validation/migrate_add_topic_fields.py`
- `examples/run_topic_walkthrough.sh`
- `examples/topic_walkthrough.human.md`（由脚本产出）

**修改**
- `insights-share/demo_codes/insightsd/store.py`（新增方法 + `_write_card` / `_item_to_card` / `_render_item_md` / `search` 扩展）
- `insights-share/demo_codes/insightsd/server.py`（`do_GET` 加 `/topics`、`do_POST` 加 `/topics` + `/insights/{id}/relabel`）
- `insights-share/demo_codes/insightsd/dashboard.html`（新增 Topics tab）
- `insights-share/demo_codes/insights_cli.py`（新增 4 个子命令）
- `insights-share/demo_codes/seeds/alice_pgpool.json`、`alice_celery_retry.json`、`carol_redis_eviction.json`（补 `topic_id` / `label`）
- `insights-share/validation/test_examples_demo_scripts.py`（加 bob id 断言）
- `examples/run_human_AB.sh`（B 轮多 publish bob）

**严禁修改**
- `proposal.md` / `README.md` / `validation_AB.md` / `validation.md`（CLAUDE.md 明文禁止）
- `docs/designs/user_design/` 目录
- `examples/COMMON_PROMPT.txt`（会破坏 A/B equality gate）

---

## 风险与缓解

| 风险 | 缓解 |
|------|------|
| 老 card 缺字段导致 `_item_to_card` 崩 | `_item_to_card` 用 `.get()` + 默认值；`test_legacy_card_without_new_fields_still_readable` 兜底 |
| raw/ 目录下混存 `.jsonl`（旧）和 `.txt`（新）引起混淆 | `raw_log_type` 字段决定扩展名；store 读写时严格按 type 分派 |
| B/WITH 导出里 bob 卡片命中 search 但 alice 不命中，破坏 A/B 预期 | 发布顺序先 alice 后 bob；Jaccard 分数受 context 文本影响，验证时仅断言 B 导出里同时出现两个 id，不强制排序 |
| relabel 写盘时 raw_log 文件被误覆盖 | `relabel()` 只改 card dict + 重写 .md，**不触碰** `raw/` 目录；加断言 |
| A/B equality gate 因新字段打印额外内容而失败 | 新字段只在响应 JSON 和 dashboard 出现，不进 claude 消费侧 prompt；`COMMON_PROMPT.txt` 零改动 |
