# 设计提案：Topic 中心的 Good/Bad 示例 Wiki

> 作者：用户设计
> 日期：2026-04-15
> 状态：草稿

---

## 核心思路

Wiki 不以"冲突检测"为出发点，而是以 **Topic（话题）** 为组织单位。
同一 Topic 下，任意用户可上传自己的实战案例，并自行标注为 **good**（建议做）或 **bad**（建议避免）。
标注权在上传者，管理员可后置覆盖。两个用户对同一场景持不同策略，不是"冲突"，而是两条并存的经验——各自有各自的 label。

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

  "raw_log_type":      "export",
  "raw_log":           "<完整 /export 导出内容，明文存储>",
  "raw_log_path":      null,

  "uploaded_at":       "2026-04-10T09:15:00Z"
}
```

---

## label 语义

| label | 含义 | 谁来决定 |
|-------|------|---------|
| `good` | 上传者认为"应该这样做" | 上传者（后可被管理员覆盖） |
| `bad`  | 上传者认为"应该避免" | 上传者（后可被管理员覆盖） |

同一 Topic 下可同时存在多个 good 和多个 bad，不互相排斥。
Alice 上传 good、Bob 上传 bad，两条并存，都对消费者有价值。

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
GET /topics/{topic_id}/examples    → 返回该 topic 下所有 example（含 label）
GET /topics/{topic_id}/examples?label=good   → 只返回 good
GET /topics/{topic_id}/examples?label=bad    → 只返回 bad
```

---

## 与现有 card 体系的关系

| 维度 | 现有 card | 本提案 Example |
|------|----------|--------------|
| 组织单位 | 卡片（单条 insight） | Topic 下的 Example |
| 冲突处理 | 并存 / 管理员 merge | 无需 merge，label 决定语义 |
| 策略分歧 | 两卡同时出现可能混淆 | Alice good + Bob bad = 两种经验都有价值 |
| 原始日志 | raw_log 字段（路径引用） | raw_log 全文存储 + 来源类型 |
| 检索粒度 | 卡片级 | Topic 级（再按 label 筛选） |

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
| raw_log 字段级脱敏 | 需要独立 PII 扫描流水线 |
| 实时通知 | 需要 WebSocket，当前 server 是纯 HTTP |
| label 版本历史 | MVP 阶段只保留最新一次 override |
