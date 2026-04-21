# 设计提案：Topic 中心的 Good/Bad 示例 Wiki

> 作者：用户设计
> 日期：2026-04-15
> 状态：草稿

---

## 核心思路

Wiki 不以"冲突检测"为出发点，而是以 **Topic（话题）** 为组织单位。

同一 Topic 下，任意用户上传自己的实战决策。每条决策都是「**某人在某场景下的选择**」，包含两种方向：

- **good**：在此场景下**选了**这个方案（采纳）
- **bad**：在此场景下**拒绝了**这个方案（避免）

两者都是有价值的决策数据。标注权在上传者，管理员可后置覆盖。

两个用户对同一 Topic 持不同策略 **不是冲突**——Alice 在场景 α 选了 X（good），Bob 在场景 β 拒绝了 X（bad），Carol 在场景 γ 选了 Y（good），这三条**全部并列存在**，不合并、不删除、不选最优。

消费侧根据自己当前场景与 `applies_when` / `do_not_apply_when` 匹配，自行挑选可参考的决策。系统**不代替用户做选择**。

---

## 数据结构

### Topic（话题）

```json
{
  "id":          "postgres-pool-exhaustion",
  "title":       "PostgreSQL 连接池耗尽",
  "tags":        ["postgres", "connection-pool", "latency"],
  "created_by":  "alice",
  "created_at":  "2026-04-10T08:00:00Z",
  "example_ids": ["alice-pgpool-good-001", "bob-pgpool-bad-001"]
}
```

### Example（实例）

```json
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

  "applies_when":      ["postgres>=13", "pgbouncer transaction mode"],
  "do_not_apply_when": ["session pooling mode", "单租户 DB"],

  "raw_log_type":      "export",
  "raw_log":           "<完整 /export 导出内容，明文存储>",
  "raw_log_path":      null,

  "uploaded_at":       "2026-04-10T09:15:00Z"
}
```

`applies_when` / `do_not_apply_when` 是场景刻画的核心字段，消费侧用它们做匹配。拒绝类 Example（label=bad）也必须填写，表达"在这种场景下我选择不走这条路"。

---

## label 语义

| label | 含义 | 谁来决定 |
|-------|------|---------|
| `good` | 上传者在此场景下**选了**这个方案（采纳决策） | 上传者（后可被管理员覆盖） |
| `bad`  | 上传者在此场景下**拒绝了**这个方案（避免决策） | 上传者（后可被管理员覆盖） |

核心原则：

1. **并列共存**：同一 Topic 下可同时存在多个 good 和多个 bad，不互相排斥，不合并，不删除。
2. **场景先行**：每条 Example 必须写清 `applies_when`（什么情况下我做了这个决策）。
3. **拒绝也是数据**：Bob 拒绝某方案 ≠ 该方案是"错"，只代表在 Bob 的场景下不合适。这条拒绝记录对场景类似的下一个人有直接价值。
4. **不评最优**：系统不声明"这个 Topic 下哪个是最佳方案"。Alice good + Bob bad + Carol good（不同方案）三条全显示，消费者自行匹配场景。

### Example：同一 Topic 下的多视角

```
Topic: postgres-pool-exhaustion

├── alice-pgpool-good-001
│     label: good · applies_when: [pgbouncer transaction mode]
│     summary: "idle_in_transaction_session_timeout=30s + pool×2"
│
├── bob-pgpool-bad-001
│     label: bad · applies_when: [32 核 + IO 密集]
│     summary: "盲目把 pool_size 从 10 改到 50 反而拖垮 IO"
│
├── carol-pgpool-good-002
│     label: good · applies_when: [单租户 + 可接受 session pooling]
│     summary: "切到 session pooling，放弃 transaction mode"
│
└── dave-pgpool-bad-002
      label: bad · applies_when: [高并发短连接]
      summary: "切 session pooling 在高并发场景反而不如 transaction mode"
```

四条全部 `status=active`，前端并列渲染，后端不做冲突标记。

---

## raw_log 来源

Example 必须携带完整原始日志，支持两种来源：

### 来源一：`/export` 导出

用户在 Claude Code 会话结束时运行 `/export`，得到人类可读的纯文本聊天记录。
上传时将整段文本写入 `raw_log` 字段（明文）。

```
raw_log_type: "export"
raw_log:      "<整段 export 文本>"
raw_log_path: null
```

### 来源二：本地 `.jsonl` 文件路径

用户上传自己机器上的 Claude Code 项目会话文件：
`~/.claude/projects/**/*.jsonl`

上传时填写文件路径，server 负责在上传时读取并存储内容。

```
raw_log_type: "jsonl"
raw_log:      "<server 读取后存入的内容>"
raw_log_path: "/Users/alice/.claude/projects/my-project/abc123.jsonl"
```

---

## API 设计

### 创建 Topic

```
POST /topics
Body: { "id": "...", "title": "...", "tags": [...] }
```

### 上传 Example

```
POST /topics/{topic_id}/examples
Body: {
  "author":       "alice",
  "label":        "good",
  "label_note":   "...",
  "summary":      "...",
  "raw_log_type": "export" | "jsonl",
  "raw_log":      "...",
  "raw_log_path": null
}
```

### 管理员覆盖 label

```
POST /topics/{topic_id}/examples/{example_id}/relabel
Body: {
  "label":    "bad",
  "override_by": "admin"
}
```

### 检索

```
GET /topics?q=postgres+pool        → 返回命中 topic 列表
GET /topics/{topic_id}/examples    → 返回该 topic 下所有 example（并列，不排序挑最优）
GET /topics/{topic_id}/examples?label=good   → 只返回「被采纳」的决策
GET /topics/{topic_id}/examples?label=bad    → 只返回「被拒绝」的决策
```

检索响应**不带**冲突警告、不带合并建议、不带"推荐方案"。每条 Example 自带 `applies_when` / `do_not_apply_when`，由消费方（人或 Agent）自行匹配场景。

---

## 与现有 card 体系的关系

| 维度 | 现有 card | 本提案 Example |
|------|----------|--------------|
| 组织单位 | 卡片（单条 insight） | Topic 下的 Example |
| 冲突处理 | **废弃**（原 merge / conflicting / deprecate 全部移除） | 无冲突概念，多决策并列共存 |
| 策略分歧 | 两卡同时出现可能混淆 | Alice good（采纳） + Bob bad（拒绝） + Carol good（另一方案）= 决策图谱 |
| 原始日志 | raw_log 字段（路径引用） | raw_log 全文存储 + 来源类型 |
| 检索粒度 | 卡片级 | Topic 级（再按 label 筛选） |
| 消费模型 | AI 替用户挑最优 | 展示全部决策 + 各自场景，用户/Agent 自行匹配 |

---

## 管理员权限范围

| 操作 | 说明 |
|------|------|
| 覆盖 label | `good` ↔ `bad` 互转，记录 override_by 和 override_at |
| 删除 Example | 明显错误或违规内容 |
| 合并 Topic | 两个高度重合的 Topic 可合并（Example 归属迁移） |
| 编辑 summary | 修正摘要措辞，不得修改 raw_log |

管理员**不得修改** raw_log 内容，保证原始证据完整性。

---

## 不在本提案范围内

| 排除项 | 原因 |
|--------|------|
| AI 自动打 label | label 是主观判断，必须由人决定 |
| AI 挑最优决策 | 本设计明确不做——展示全部并列决策即止 |
| 冲突检测 / 自动合并 | 本设计明确废弃——多决策并列共存即是答案 |
| raw_log 字段级脱敏 | 需要独立 PII 扫描流水线 |
| 实时通知 | 需要 WebSocket，当前 server 是纯 HTTP |
| label 版本历史 | MVP 阶段只保留最新一次 override |
