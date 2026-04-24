---
{
  "id": "m1-kb-ad-004",
  "title": "任务执行模式 / Task Execution Patterns",
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
  "label_note": "\n### 状态流转\n```\ncompleted: 726 次\nblocked: 594 次\n```\n\n### 常见任务类型\n1. **skills 列表查询** - 列出可用 skill 名称与用途说明\n2. **事实校正** - 用 Bash 获取真实数据，纠正 md 文件中的错误描述\n3. **只更新 memory** - 严格限制在 state/memory/*.md 中操作\n\n### 固定派发语义\n```\ncancel previous loop and run this : /loop 10m {task}\n```\n每次新任务到达时先取消之前的循环，再启动新的 10 分钟循环。",
  "applies_when": [],
  "do_not_apply_when": []
}
---

# 任务执行模式 / Task Execution Patterns

> author: m1 · confidence: 0.85


### 状态流转
```
completed: 726 次
blocked: 594 次
```

### 常见任务类型
1. **skills 列表查询** - 列出可用 skill 名称与用途说明
2. **事实校正** - 用 Bash 获取真实数据，纠正 md 文件中的错误描述
3. **只更新 memory** - 严格限制在 state/memory/*.md 中操作

### 固定派发语义
```
cancel previous loop and run this : /loop 10m {task}
```
每次新任务到达时先取消之前的循环，再启动新的 10 分钟循环。
