# Proposal：Wiki 卡片冲突与合并机制

> 状态：草稿（Draft）
> 日期：2026-04-15
> 来源：由 Claude 阅读 insightsd/store.py、server.py、seeds/*.json 后提取
> 背景：demo 当前 merge 逻辑已有雏形，本文梳理现状并提出完整冲突设计

---

## 1. 现有卡片实现速查

### 1.1 卡片 Schema（来自 seeds/*.json + store.py）

```json
{
  "id":               "alice-pgpool-2026-04-10",   // 全局唯一键，{author}-{slug}-{date}
  "title":            "PostgreSQL pool exhaustion under burst traffic",
  "author":           "alice",
  "tags":             ["postgres", "connection-pool", "latency"],
  "context":          "...",                        // 背景环境
  "symptom":          "...",                        // 症状（Bad example）
  "root_cause":       "...",                        // 根因
  "fix":              "...",                        // 修复方案（Good example）
  "confidence":       0.82,                         // 0.0–1.0
  "applies_when":     ["postgres>=13", "pgbouncer transaction mode"],
  "do_not_apply_when":["session pooling mode"],
  "status":           "active" | "not_triggered",   // not_triggered = 被管理员标记为不触发
  "sticky_not_triggered": false,
  "wiki_type":        "database" | "infra_queue" | "infra_cache" | "general" | "research",
  "raw_log":          "./raw/{id}.jsonl"
}
```

### 1.2 两种存储模式

| 模式 | 类 | 文件结构 | 支持操作 |
|------|----|---------|---------|
| flat | `InsightStore` | 单个 `wiki.json` 数组 | add（upsert by id）、list、search |
| tree | `TreeInsightStore` | `wiki_tree/{type}/{slug}.md` | add、edit、delete、tag、merge、research |

### 1.3 现有 merge 实现（`store.py:501–550`）

```
POST /insights/merge
Body: { "source_id": "...", "target_id": "..." }
```

**合并规则（当前）：**

| 字段类型 | 处理方式 |
|---------|---------|
| `context / root_cause / symptom / fix` | target 优先；source 不重复内容追加到末尾 |
| `tags` | 去重合并，target 在前 |
| `applies_when / do_not_apply_when` | 去重合并，target 在前 |
| `status=not_triggered` | 任一方有则结果继承 |
| 其余字段（id, title, author, confidence…）| target 原样保留 |

合并后 source 卡片被**物理删除**。

**当前限制：**
- tree 模式专属，flat 模式返回 400
- 无自动冲突检测，完全依赖管理员手动调用
- 无版本历史，merge 不可回滚
- 无"待审批"状态，新卡 POST 后即可被检索

---

## 2. 冲突场景分析

### 场景：同一问题，两人策略不同

```
问题：checkout API 超时，postgres 高峰期拒绝新连接

User A（alice）strategy alpha：
  fix: "Set idle_in_transaction_session_timeout=30s，pool size ×2"
  confidence: 0.82
  applies_when: [pgbouncer transaction mode]

User B（bob）strategy beta：
  fix: "切换到 session pooling，彻底废弃 PgBouncer"
  confidence: 0.75
  applies_when: [session pooling acceptable, single-tenant DB]
```

两张卡 **id 不同**（`alice-pgpool-*` vs `bob-pgpool-*`），POST 后在 wiki 中**并存**。

### 三种冲突类型

| 类型 | 描述 | 当前处理 |
|------|------|---------|
| **策略互斥** | A 说"开 transaction mode"，B 说"关掉 transaction mode" | 并存，无标记 |
| **建议矛盾** | A 说 pool ×2，B 说 pool ×0.5 | 并存，无标记 |
| **作用域重叠** | applies_when 高度重合但 fix 不同 | 并存，搜索都返回，消费者困惑 |

### 当前消费路径的兜底

`adapter.py` 在消费时对**单张**卡做 adopt/adapt/reject。但若搜索返回 alice 和 bob 两张互斥卡，adapter 只处理 top-1，用户看不到冲突存在。

---

## 3. 冲突处理设计提案

### 3.1 设计原则

1. **不阻断发布**：任何人都能 POST 新卡，不因潜在冲突阻塞工作流
2. **显式标记优于静默并存**：冲突要可见，不能让消费者自己撞上
3. **管理员决策，不自动合并内容**：AI 可辅助，但最终 merge/reject 由人决定
4. **消费侧感知**：搜索结果要告知用户"存在冲突卡片"

### 3.2 卡片状态机扩展

```
           POST /insights
                │
                ▼
           ┌─────────┐
           │ pending │  ← 新增：默认进入待审批队列
           └────┬────┘
                │ admin approve
                ▼
           ┌─────────┐
           │  active │  ← 现有：可被检索和消费
           └────┬────┘
                │ conflict detected / admin flag
                ▼
        ┌───────────────┐
        │  conflicting  │  ← 新增：标记为冲突，搜索时附带警告
        └───────┬───────┘
                │ admin merge / deprecate
                ▼
      ┌──────────────────┐      ┌──────────────────┐
      │ merged (deleted) │  或  │   deprecated     │  ← 输家软删除
      └──────────────────┘      └──────────────────┘
```

新增字段：

```json
{
  "status": "pending | active | conflicting | deprecated",
  "conflict_with": ["bob-pgpool-2026-04-15"],
  "conflict_reason": "fix 方向相反：transaction mode vs session mode",
  "supersedes": [],
  "superseded_by": null
}
```

### 3.3 冲突检测策略（POST 时触发）

**Step 1：applies_when 重叠检测**

新卡 POST 后，server 对比所有 active 卡的 `applies_when`：
- Jaccard(新卡 applies_when tokens, 已有卡 applies_when tokens) > 阈值（建议 0.5）
- 且 `wiki_type` 相同
→ 候选冲突对，进入 Step 2

**Step 2：fix 方向相似度**

用已有的 bag-of-words 对 `fix` 字段做相似度：
- 相似度 **低**（< 0.3）→ fix 方向可能相反 → 标记 `conflicting`
- 相似度 **高**（> 0.7）→ 大概率是重复卡 → 建议 merge

**Step 3：管理员通知**

冲突检测结果写入 `conflict_with`，dashboard 展示冲突队列，由管理员决定：
- **Merge**：调用现有 `POST /insights/merge`（target 策略赢）
- **Deprecate**：调用 `POST /insights/{id}/deprecate`，软删除输家
- **Both active**：两张都保留，但搜索结果附带冲突警告

### 3.4 搜索结果变化

当前：返回纯卡片数组。

提案后：

```json
{
  "hits": [
    {
      "id": "alice-pgpool-2026-04-10",
      "score": 0.45,
      "conflict_flag": true,
      "conflict_with": ["bob-pgpool-2026-04-15"],
      "conflict_reason": "fix 方向相反"
    },
    {
      "id": "bob-pgpool-2026-04-15",
      "score": 0.38,
      "conflict_flag": true,
      "conflict_with": ["alice-pgpool-2026-04-10"],
      "conflict_reason": "fix 方向相反"
    }
  ],
  "conflict_warning": "检索到 2 张互斥卡片，建议管理员处理后再参考"
}
```

`adapter.py` 消费时：若 top-1 卡带有 `conflict_flag`，在 adapted_insight 末尾追加警告：
```
⚠ 注意：本卡与 bob-pgpool-2026-04-15 存在策略冲突，请结合实际环境判断。
```

### 3.5 Merge 策略选择（管理员决策时）

| 场景 | 建议操作 | 结果 |
|------|---------|------|
| 策略互斥，环境不同 | **Both active** + 完善各自 applies_when | 分场景各自命中 |
| 策略互斥，环境重叠 | **Merge**：target = 更高 confidence 的卡 | 输家 deprecated |
| 策略冗余（大同小异） | **Merge**：target = 更完整的卡 | 输家 deprecated |
| 一方明确错误 | **Deprecate** 输家 | 不保留错误策略 |

---

## 4. 不在本提案范围内

| 排除项 | 原因 |
|--------|------|
| 向量语义冲突检测 | 需要 embedding 基础设施，超出 demo 范围 |
| 自动 AI 合并内容 | 风险高，策略判断必须由人负责 |
| 实时推送冲突通知 | 需要 WebSocket，当前 server 是纯 HTTP |
| 版本历史回滚 | 需要 SQLite/Postgres，当前是文件存储 |

---

## 5. 实施优先级

| 优先级 | 项目 | 依赖 |
|--------|------|------|
| P0 | `status` 字段扩展（pending / conflicting / deprecated） | 无 |
| P0 | `conflict_with` 字段 + POST 时重叠检测 | P0 status |
| P1 | 搜索结果附带 `conflict_warning` | P0 |
| P1 | `adapter.py` 消费侧冲突警告 | P0 |
| P2 | dashboard UI 冲突队列展示 | P1 |
| P2 | `POST /insights/{id}/deprecate` 端点 | P0 |
