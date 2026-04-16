# Topic 中心 Good/Bad 示例库 实现计划

> 基于深入代码探索（2026-04-15）
> 规模：约 2000 行新增代码 + schema 迁移

---

## 执行摘要

现有系统是**卡片（Card）中心**：每张卡片代表一个完整的生产事故解决方案，包含"坏例子"和"好例子"。当两个用户对同一问题有不同观点时，需要通过 merge API 来处理冲突。

新提案改为**Topic 中心**：Topic 是问题的分组单位（如"PostgreSQL 连接池耗尽"），每个 Example 是用户上传的实战案例，用户自己决定是 good（推荐）还是 bad（反面教材）。无需 merge，因为相反的观点本身就有价值。

---

## 现有代码布局（核心发现）

### 1. 存储层（`insightsd/store.py`，587 行）

#### InsightStore（扁平模式）
- `__init__(path: Path)` — 单个 `wiki.json` 文件
- `load()` → `list[dict]` — 从 JSON 数组或 `{cards: [...]}` 读取
- `save(cards: list)` — 原子写，先 `.tmp` 后 `rename`
- `add(card: dict)` → `dict` — 追加或覆盖（查 id），返回卡片
- `list_all()` → `list[dict]` — 只返回 id/title/tags/author
- `search(q: str, k: int)` → `list[dict]` — Jaccard 相似度 Bag-of-Words 检索

**当前卡片 schema**（wiki.json 中）：
```python
{
  "id": "alice-pgpool-2026-04-10",
  "title": "PostgreSQL pool exhaustion under burst traffic",
  "author": "alice",
  "tags": ["postgres", "connection-pool", "latency", "prod-incident"],
  "context": "API tier behind PgBouncer, transaction pooling mode",
  "symptom": "p99 latency spikes; ...",
  "root_cause": "Long-lived idle txns ...",
  "fix": "Set idle_in_transaction_session_timeout=30s ...",
  "confidence": 0.82,
  "applies_when": ["postgres>=13", "pgbouncer transaction mode"],
  "do_not_apply_when": ["session pooling mode", "single-tenant DB"]
}
```
**路径**：`/Users/m1/projects/demo_insights_share/insights-share/demo_codes/insightsd/store.py:90-174`

#### TreeInsightStore（树形模式，4 层）
- `__init__(root: Path)` — wiki_tree 根目录
- `load()` → `list[dict]` — 遍历所有 `<type>/<slug>.md`，解析 frontmatter + 分割 sections
- `list_all()` — 返回 id/title/tags/author/wiki_type/status
- `search(q: str, k: int)` — 同样的 Jaccard 检索，支持 status="not_triggered" 过滤
- `add(card, wiki_type="general")` → 写 `<type>/<slug>.md` + 写 `<type>/raw/<id>.jsonl` + 更新 INDEX.md
- `delete(card_id)` → 删除 `.md` + `/raw/<id>.jsonl` + 重建 INDEX
- `edit(card_id, patch)` → 部分更新卡片字段
- `tag(card_id, tags, sticky=True)` → 追加标签，sticky 控制 not_triggered 持久性
- `merge(source_id, target_id)` → 合并 tags/applies_when/do_not_apply_when，删除 source
- `research(query: str)` → 调用 search_agent.py，生成新卡片到 research wiki_type

**路径**：`/Users/m1/projects/demo_insights_share/insights-share/demo_codes/insightsd/store.py:272-587`

### 2. 目录布局（`wiki_tree/`）

```
wiki_tree/
├── wiki_types.json              (types 列表)
├── database/
│   ├── INDEX.md
│   ├── postgres_pool.md         (frontmatter JSON + ## 分割的 markdown)
│   └── raw/
│       └── alice-pgpool-2026-04-10.jsonl   (单行 JSON，card 扁平化备份)
├── infra_cache/
│   ├── INDEX.md
│   ├── redis_lru_session_eviction.md
│   └── raw/
└── infra_queue/
    ├── INDEX.md
    └── raw/
```

**当前 wiki_types.json**：
```json
{
  "types": ["database", "infra_cache", "infra_queue"]
}
```

**INDEX.md 结构**：markdown 表格，列为 name/description/trigger when/docs，用于人工浏览

**Card 在 .md 中的存储**：
```markdown
---
{
  "id": "...",
  "title": "...",
  "author": "...",
  "confidence": 0.82,
  "tags": [...],
  "status": "active",
  "applies_when": [...],
  "do_not_apply_when": [...],
  "raw_log": "./raw/alice-pgpool-2026-04-10.jsonl"
}
---

# Title

> author: alice · confidence: 0.82

## Description
...

## Bad example
...

## Good example
...

## Applies when
...

## Do NOT apply when
...

## Raw log
[./raw/alice-pgpool-2026-04-10.jsonl](./raw/alice-pgpool-2026-04-10.jsonl)
```

**路径**：`/Users/m1/projects/demo_insights_share/insights-share/demo_codes/wiki_tree/`
- wiki_types.json: `/Users/m1/projects/demo_insights_share/insights-share/demo_codes/wiki_tree/wiki_types.json`
- 示例 database/postgres_pool.md: `/Users/m1/projects/demo_insights_share/insights-share/demo_codes/wiki_tree/database/postgres_pool.md`

### 3. HTTP API（`insightsd/server.py`，231 行）

**框架**：`stdlib http.server.BaseHTTPRequestHandler + ThreadingHTTPServer`（无 FastAPI）

**完整端点列表**：

| 方法 | 路径 | 用途 | 树/扁平 | 实现行号 |
|------|------|------|--------|---------|
| GET | `/` | 返回 dashboard.html 页面 | 无 | 61 |
| GET | `/dashboard` | 同上 | 无 | 61 |
| GET | `/healthz` | 健康检查 → `{"ok": true}` | 无 | 74 |
| GET | `/insights` | 列出全部卡片（摘要） | 两者 | 77-78 |
| GET | `/search?q=...&k=...` | 检索 top-k 卡片 | 两者 | 80-88 |
| POST | `/insights` | 新增卡片 | 两者 | 96-110 |
| POST | `/insights/merge` | 合并（source 入 target） | 树 only | 113-126 |
| POST | `/insights/research` | AI 搜索+新卡 | 树 only | 129-144 |
| POST | `/insights/{id}/edit` | 编辑字段 | 树 only | 147-161 |
| POST | `/insights/{id}/tag` | 添加标签 | 树 only | 164-180 |
| DELETE | `/insights/{id}` | 删除卡片 | 树 only | 185-198 |

**关键：** 树模式才支持 CRUD，扁平模式只支持 GET + POST add

**启动命令**：
```bash
python insights_cli.py serve --host 0.0.0.0 --port 7821 --store-mode tree
```

**路径**：`/Users/m1/projects/demo_insights_share/insights-share/demo_codes/insightsd/server.py:1-231`

### 4. 种子数据（Seeds）

**文件**：
- `/Users/m1/projects/demo_insights_share/insights-share/demo_codes/seeds/alice_pgpool.json`
- `/Users/m1/projects/demo_insights_share/insights-share/demo_codes/seeds/alice_celery_retry.json`
- `/Users/m1/projects/demo_insights_share/insights-share/demo_codes/seeds/carol_redis_eviction.json`

**Schema** 同 wiki.json card 格式

### 5. raw_log 现有处理

**当前状态**：
- `raw_log` 字段在 card 中是相对路径字符串，如 `"./raw/alice-pgpool-2026-04-10.jsonl"`
- `/raw/` 目录包含 `.jsonl` 文件（单行 JSON，是整个 card 的备份）
- 路径示例：`/Users/m1/projects/demo_insights_share/insights-share/demo_codes/wiki_tree/database/raw/alice-pgpool-2026-04-10.jsonl`

**内容示例**（单行）：
```json
{"id": "alice-pgpool-2026-04-10", "title": "PostgreSQL pool exhaustion under burst traffic", ...}
```

**export_template.txt** 用于示例，包含 `/export` 命令导出的人类可读文本（但目前代码中未被使用，仅作参考）

**路径**：
- `export_template.txt`: `/Users/m1/projects/demo_insights_share/export_template.txt`
- 示例 raw 文件: `/Users/m1/projects/demo_insights_share/insights-share/demo_codes/wiki_tree/database/raw/alice-pgpool-2026-04-10.jsonl`

### 6. SKILL + Daemon 架构

#### insights-wiki Skill（用户端，静默回灌）
**文件**：`/Users/m1/projects/demo_insights_share/insights-share/demo_codes/.claude/skills/insights-wiki/SKILL.md`

- 自动从 LAN insightsd 拉取卡片，缓存到 `~/.cache/insights-wiki/`
- **触发流程**：
  1. UserPromptSubmit hook → `insights_prefetch.py` → GET `/insights` → persist all cards
  2. Stop hook → `search_agent.py` → 语义搜索 → top hit → persist + 记 manifest

#### insights-wiki-server Skill（管理员端，服务器+面板）
**文件**：`/Users/m1/projects/demo_insights_share/insights-share/demo_codes/.claude/skills/insights-wiki-server/SKILL.md`

- 启动 daemon：`python insights_cli.py serve --host 0.0.0.0 --port 7821 --store-mode tree`
- 打开 dashboard：自动弹出 kanban UI

#### Daemon 缓存机制
- **manifest.json** 位置：`~/.cache/insights-wiki/manifest.json`
- **缓存文件**：`~/.cache/insights-wiki/<card_id>.json`
- manifest 结构：
  ```json
  {
    "last_sync_at": "2026-04-15T13:30:45+0000",
    "cards": ["alice-pgpool-2026-04-10", "carol-redis-eviction-2026-03-27"]
  }
  ```

**路径**：
- SKILL.md: `/Users/m1/projects/demo_insights_share/insights-share/demo_codes/.claude/skills/insights-wiki/SKILL.md`
- 缓存模块: `/Users/m1/projects/demo_insights_share/insights-share/demo_codes/hooks/insights_cache.py` (111 行)
- prefetch: `/Users/m1/projects/demo_insights_share/insights-share/demo_codes/hooks/insights_prefetch.py` (58 行)
- Stop hook: `/Users/m1/projects/demo_insights_share/insights-share/demo_codes/hooks/insights_stop_hook.py` (138 行)

### 7. Search Agent（AI 语义检索）
**文件**：`/Users/m1/projects/demo_insights_share/insights-share/demo_codes/search_agent.py` (169 行)

- 使用 `claude_agent_sdk` (MiniMax)
- 接收 query + wiki_tree 路径
- 返回 JSON：`{"hits": [{"wiki_type": "...", "item": "...", "score": 0.87, "rationale": "..."}]}`
- 通过 sentinel `<<<SEARCH_HITS>>> ... <<<END>>>` 包围 JSON

**关键**：严禁任何 fallback，任何异常直接 raise

**路径**：`/Users/m1/projects/demo_insights_share/insights-share/demo_codes/search_agent.py:1-169`

### 8. 测试覆盖
**文件**：`/Users/m1/projects/demo_insights_share/insights-share/validation/test_examples_demo_scripts.py` (150 行)

- 验证 A/B 实验的 prompt 一致性
- 验证 A/B 导出的卡片引用（alice-pgpool-2026-04-10）
- 验证 common prompt 文件存在且一致

**关键约束**：严禁打断用户、严禁吞异常、强制中文

**路径**：`/Users/m1/projects/demo_insights_share/insights-share/validation/test_examples_demo_scripts.py:1-150`

---

## 新提案的 Schema 变化

### 新增对象：Topic

```python
{
  "id":          "postgres-pool-exhaustion",
  "title":       "PostgreSQL 连接池耗尽",
  "tags":        ["postgres", "connection-pool", "latency"],
  "created_by":  "alice",
  "created_at":  "2026-04-10T08:00:00Z",
  "example_ids": ["alice-pgpool-good-001", "bob-pgpool-bad-001"]
}
```

### 新增对象：Example

```python
{
  "id":                "alice-pgpool-good-001",
  "topic_id":          "postgres-pool-exhaustion",
  "author":            "alice",

  "label":             "good",
  "label_note":        "这个方案在我们的 PgBouncer transaction mode 下彻底解决了连接耗尽",

  "label_override":    null,
  "label_override_by": null,
  "label_override_at": null,

  "summary":           "设置 idle_in_transaction_session_timeout=30s，pool size ×2",

  "raw_log_type":      "export",  # or "jsonl"
  "raw_log":           "<完整文本内容，明文存储>",
  "raw_log_path":      null,      # 如果 raw_log_type="jsonl" 则有值

  "uploaded_at":       "2026-04-10T09:15:00Z"
}
```

### 新增 API 端点

| 方法 | 路径 | 用途 | 
|------|------|------|
| POST | `/topics` | 创建 Topic |
| GET | `/topics?q=...` | 检索 Topic（命中 title/tags） |
| POST | `/topics/{topic_id}/examples` | 上传 Example |
| GET | `/topics/{topic_id}/examples` | 列出该 Topic 下所有 Example |
| GET | `/topics/{topic_id}/examples?label=good` | 只返回 good example |
| GET | `/topics/{topic_id}/examples?label=bad` | 只返回 bad example |
| POST | `/topics/{topic_id}/examples/{example_id}/relabel` | 管理员覆盖 label |
| DELETE | `/topics/{topic_id}/examples/{example_id}` | 删除 Example |
| POST | `/topics/{topic_id}/merge` | 合并两个 Topic（高级） |

---

## 迁移策略

### 阶段 1：保持兼容
- 新建 `TopicStore` 和 `ExampleStore` 类，与现有 InsightStore/TreeInsightStore 并存
- 增加 API 端点（不删除旧的）
- 旧 card 数据迁移脚本：card → Topic（自动生成）+ Example

### 阶段 2：切换
- 更新 SKILL、manifest、搜索逻辑
- 转换 hook 从 card-centric 到 topic-centric

### 阶段 3：清理
- 删除旧 API 端点（如果需要）
- 重构测试

---

## 实现核清单（按优先级）

### P0：Core Schema + Store（1-2 周）
- [ ] `TopicStore` 类（读写 topics）
- [ ] `ExampleStore` 类（CRUD examples）
- [ ] 新 wiki_tree 目录结构：`topics/{topic_id}/examples/{id}.md`
- [ ] 迁移脚本：card → topic+example
- [ ] 单元测试

### P1：HTTP API（1 周）
- [ ] POST /topics 端点
- [ ] POST /topics/{topic_id}/examples 端点（支持 export + jsonl 两种 raw_log 来源）
- [ ] GET /topics?q=... 
- [ ] GET /topics/{topic_id}/examples?label=...
- [ ] POST /topics/{topic_id}/examples/{id}/relabel
- [ ] DELETE /topics/{topic_id}/examples/{id}
- [ ] 集成测试

### P2：搜索与检索（1 周）
- [ ] Topic 级 search_agent（而非 card 级）
- [ ] Example 级精细检索（按 label）
- [ ] 更新 SKILL 的 manifest 和缓存逻辑

### P3：管理功能（5 天）
- [ ] 管理员覆盖 label 端点
- [ ] Topic 合并逻辑
- [ ] Dashboard kanban 适配（可选）

### P4：验证与文档（3 天）
- [ ] 更新 test_examples_demo_scripts.py
- [ ] 写 proposal_conflict_design.md 的实现细节
- [ ] 写迁移指南

---

## 关键技术决策

### raw_log 存储
- **当前**：相对路径 `./raw/<id>.jsonl`，文件系统上只有 JSON object，无完整 export 文本
- **提案**：
  - 来源 1（export）：`raw_log_type: "export"` + `raw_log: "<整段文本>"` → 明文存储在 card dict 中
  - 来源 2（jsonl）：`raw_log_type: "jsonl"` + `raw_log: "<server 读取后存入的内容>"` → 也明文存储
  - 都不走文件系统，而是 dict 字段

**实现影响**：Example card 体积会增大（包含完整原始日志），存储层需要优化写性能（GZip？）

### Topic ID 生成
- 手工创建（用户提供）或自动生成？
  → **决策**：手工 + 规范化（lowercase kebab-case），CLI 验证唯一性

### Label 权限
- 用户自己打，管理员可覆盖 + 记录 override_by 和 override_at
  → **决策**：所有改动都记录审计日志，Example 本身是不可变的，只有 label 可变

### 搜索优先级
- Topic 先（用户检索问题） vs Example 先（用户检索解决方案）
  → **决策**：Topic 级 GET /search，然后按 label 筛选 Example 子集

---

## 风险与缓解

| 风险 | 影响 | 缓解 |
|------|------|------|
| raw_log 明文存储导致体积爆炸 | 卡片从 KiB 增到 MiB | 分页读取 + GZip 压缩 + 可选检索 |
| 迁移脚本丢失 card 字段 | 数据损失 | 保留备份卡片，支持回滚 |
| 搜索性能下降 | 响应时间 >1s | 缓存 Topic 级别的索引 |
| Label 被频繁覆盖 | 审计日志爆炸 | 限制频率 + 归档旧日志 |

---

## 相关文件清单

### 现有核心代码
- `/Users/m1/projects/demo_insights_share/insights-share/demo_codes/insightsd/store.py` — InsightStore / TreeInsightStore
- `/Users/m1/projects/demo_insights_share/insights-share/demo_codes/insightsd/server.py` — HTTP server
- `/Users/m1/projects/demo_insights_share/insights-share/demo_codes/search_agent.py` — AI 搜索
- `/Users/m1/projects/demo_insights_share/insights-share/demo_codes/hooks/insights_cache.py` — 缓存
- `/Users/m1/projects/demo_insights_share/insights-share/demo_codes/hooks/insights_stop_hook.py` — Stop hook
- `/Users/m1/projects/demo_insights_share/insights-share/demo_codes/hooks/insights_prefetch.py` — UserPromptSubmit hook
- `/Users/m1/projects/demo_insights_share/insights-share/demo_codes/insights_cli.py` — CLI 主入口

### SKILL 和配置
- `/Users/m1/projects/demo_insights_share/insights-share/demo_codes/.claude/skills/insights-wiki/SKILL.md`
- `/Users/m1/projects/demo_insights_share/insights-share/demo_codes/.claude/skills/insights-wiki-server/SKILL.md`
- `/Users/m1/projects/demo_insights_share/insights-share/demo_codes/.claude/skills/insights-wiki-server/scripts/start_server.sh`
- `/Users/m1/projects/demo_insights_share/insights-share/demo_codes/.claude/skills/insights-wiki-server/scripts/start_ui.sh`

### 测试与验证
- `/Users/m1/projects/demo_insights_share/insights-share/validation/test_examples_demo_scripts.py`
- `/Users/m1/projects/demo_insights_share/insights-share/validation/test_ab_demo_plan.py`
- `/Users/m1/projects/demo_insights_share/insights-share/demo_codes/hooks/test_insights_cache.py`

### 数据
- `/Users/m1/projects/demo_insights_share/insights-share/demo_codes/wiki_tree/` — 树形数据
- `/Users/m1/projects/demo_insights_share/insights-share/demo_codes/seeds/` — 种子 JSON
- `/Users/m1/projects/demo_insights_share/insights-share/demo_codes/wiki.json` — 扁平数据

### 文档
- `/Users/m1/projects/demo_insights_share/proposal_conflict_design.md` — 本提案文档

---

## 后续步骤

1. **确认 Schema** — 与团队 review `proposal_conflict_design.md` 的 Example 和 Topic 定义
2. **编码 TopicStore** — 先做 read-only，再加 write
3. **编码 API** — POST /topics → 测试
4. **迁移数据** — 现有 card → topic+example
5. **更新 Search Agent** — 适配新 wiki 结构
6. **验证 Skill 集成** — insights-wiki manifest 和 Stop hook 改动
7. **测试 A/B** — 跑现有 test_examples_demo_scripts.py

