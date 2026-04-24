---
{
  "id": "m1-kb-ad-005",
  "title": "技术发现 / Technical Findings",
  "author": "m1",
  "confidence": 0.85,
  "tags": [
    "knowledge-extraction",
    "session-analysis",
    "group_ad"
  ],
  "status": "active",
  "topic_id": "m1-kb-ad",
  "label": "good",
  "label_note": "\n### 文件路径处理\n- 所有路径使用绝对路径\n- sessionId 即为文件名 (UUID 格式)\n- JSONL 每行一个 operation (queue-operation)\n\n### 操作类型\n- `type: \"queue-operation\"` - 队列操作\n- `operation: \"enqueue\"` - 入队操作\n- `timestamp` - ISO 8601 格式时间戳\n\n### 项目约束\n1. 用 Bash 获取当前时间，不要猜测\n2. 用 `wc -l` 获取脚本真实行数\n3. 纠正与当前项目不一致的描述\n4. 用中文简洁回复",
  "applies_when": [],
  "do_not_apply_when": []
}
---

# 技术发现 / Technical Findings

> author: m1 · confidence: 0.85


### 文件路径处理
- 所有路径使用绝对路径
- sessionId 即为文件名 (UUID 格式)
- JSONL 每行一个 operation (queue-operation)

### 操作类型
- `type: "queue-operation"` - 队列操作
- `operation: "enqueue"` - 入队操作
- `timestamp` - ISO 8601 格式时间戳

### 项目约束
1. 用 Bash 获取当前时间，不要猜测
2. 用 `wc -l` 获取脚本真实行数
3. 纠正与当前项目不一致的描述
4. 用中文简洁回复
