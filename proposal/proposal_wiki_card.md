# Wiki 卡片 Schema 与存储速查

> 状态：现状文档（Living doc）
> 日期：2026-04-18（对齐"并列共存"设计后重写）
> 作用：说明仓库当前 `wiki_tree/` 存储结构与卡片字段；正式数据模型请看 [proposal_conflict_design.md](proposal_conflict_design.md)

---

## 1. 正式设计的唯一来源

**本文件不再定义 Topic / Example 的业务语义**。

业务模型请看 [proposal_conflict_design.md](proposal_conflict_design.md)。关键点：

- 组织单位是 **Topic**，每 Topic 下挂多条 **Example**
- 每条 Example = 一个人在一个场景下的决策
- `label=good` = 在此场景下**选了**此方案
- `label=bad`  = 在此场景下**拒绝了**此方案
- 所有 Example **并列共存**，不合并、不排序挑最优、不做冲突检测
- 消费方自行根据 `applies_when` / `do_not_apply_when` 匹配场景

本文件仅描述上述模型落到磁盘上的具体形态，方便开发者对代码。

---

## 2. 卡片 Schema（磁盘形态）

`wiki_tree/{wiki_type}/{slug}.md` 的文件头用 `---` 包裹一段 JSON，随后是 markdown 正文：

```json
{
  "id":               "alice-pgpool-2026-04-10",   // {author}-{slug}-{date}，全局唯一
  "title":            "PostgreSQL pool exhaustion under burst traffic",
  "author":           "alice",
  "tags":             ["postgres", "connection-pool", "latency"],
  "status":           "active",                     // 单状态：active（可选 pending 做审批）
  "applies_when":     ["postgres>=13", "pgbouncer transaction mode"],
  "do_not_apply_when":["session pooling mode"],
  "raw_log":          "./raw/alice-pgpool-2026-04-10.jsonl",
  "topic_id":         "postgres-pool-exhaustion",
  "label":            "good",                       // good = 采纳 / bad = 拒绝
  "label_note":       "在 PgBouncer transaction mode 下彻底解决",
  "label_override":   null,                         // 管理员可覆盖为 good/bad
  "label_override_by":null,
  "label_override_at":null,
  "raw_log_type":     "jsonl"                       // jsonl | export
}
```

随后的 markdown 正文：

```markdown
# {title}

> author: {author} · label: **{label}**

## Description
{场景 / 上下文 / 环境}

## Bad example
{若 label=good：被避免的现象 / 若 label=bad：本次被拒绝的方案}

## Good example
{若 label=good：被采纳的方案 / 若 label=bad：本次最终选择了什么}

## Applies when
- {条件}

## Do NOT apply when
- {条件}

## Raw log
[./raw/{id}.{ext}](./raw/{id}.{ext})
```

---

## 3. 存储模式

| 模式 | 类 | 文件结构 | 操作 |
|------|----|---------|------|
| flat | `InsightStore` | 单个 `wiki.json` 数组 | add（upsert by id）、list、search |
| tree | `TreeInsightStore` | `wiki_tree/{type}/{slug}.md` + `./raw/{id}.*` + `INDEX.md` | add、edit、delete、tag、relabel、research |

tree 模式是当前默认落地形态。

---

## 4. 目录布局

```
wiki_tree/
├── wiki_types.json          # 注册合法 wiki_type 列表
├── topics.json              # 注册 Topic（title/tags/wiki_type/created_by/created_at）
└── {wiki_type}/             # database / general / infra_cache / infra_queue / ...
    ├── INDEX.md             # 本类索引表：\| name \| description \| trigger when \| docs \|
    ├── {slug}.md            # 卡片主体（见第 2 节）
    └── raw/
        └── {id}.{jsonl|txt} # 原始 Claude Code 会话日志
```

新增卡时需同步：

1. 如是新 wiki_type → 追加到 `wiki_types.json`
2. 如是新 topic → 追加到 `topics.json`
3. 追加一行到对应 `{wiki_type}/INDEX.md`
4. 写 `{slug}.md` 主体
5. 写 `raw/{id}.*` 原始日志

---

## 5. label override 流程

1. 上传者写入 `label=good|bad` + `label_note`
2. 管理员发现 label 不恰当 → POST relabel：
   - 写 `label_override = "good" | "bad"`
   - 写 `label_override_by = "admin"`
   - 写 `label_override_at = ISO8601`
3. 原 `label` 字段**保持不变**，保留上传者主观判断作为历史
4. 检索与消费侧读取时，优先取 `label_override`（若非 null），否则取 `label`

---

## 6. 已废弃的字段与能力

以下为历史设计遗留，当前实现已不再使用，也不会写入新卡：

| 已废弃 | 替代 |
|--------|------|
| `confidence` 字段（0.0–1.0） | 删除——评分是主观判断，不作为 wiki 字段；语义交给 label + applies_when |
| `status = pending / conflicting / deprecated` | 统一为 `active`（可选 `pending` 做入库审批） |
| `conflict_with` / `conflict_reason` | 删除——多决策并列，不标冲突 |
| `supersedes` / `superseded_by` | 删除——不做合并、不做废弃 |
| `POST /insights/merge` 端点 | 保留代码但不再是主线路径；新设计不鼓励合并 |
| 自动冲突检测（applies_when Jaccard + fix 相似度） | 删除——不需要 |

此段保留目的仅为方便清理历史代码，新功能不要再引入上述概念。

---

## 7. 参考样例

- **good 卡**：`wiki_tree/database/postgres_pool.md`（alice，jsonl raw）
- **bad 卡 + admin override**：`wiki_tree/general/bob_pgpool_bad_2026_04_12.md`（bob，export txt raw，admin 覆盖 bad→good）
- **queue 类**：`wiki_tree/infra_queue/celery_retry_storm.md`
- **cache 类**：`wiki_tree/infra_cache/redis_lru_session_eviction.md`
