---
{
  "id": "m1-kb-ao-001",
  "title": "1. Web Search 工作模式",
  "author": "m1",
  "confidence": 0.85,
  "tags": [
    "knowledge-extraction",
    "session-analysis",
    "group_ao"
  ],
  "status": "active",
  "topic_id": "m1-kb-ao",
  "label": "good",
  "label_note": "\n### 模式描述\nAgent 被指示使用 WebSearch 进行多角度研究任务，通常以 team-lead 任务分配形式出现。\n\n### 典型指令模板\n```\nYou are a data collection agent. Search for discussions about [topic].\nUse WebSearch with queries like:\n- \"keyword1\" \"keyword2\"\n- site:example.com \"query\"\nFocus on:\n1. [Aspect 1]\n2. [Aspect 2]\n3. [Aspect 3]\nFor relevant content, use WebFetch to get full text.\n```\n\n### 常见研究主题\n- AI 研究批评与伦理问题（vibe coding 学术讨论）\n- 可复现性与验证\n- Hacker News 讨论\n- 图表创建方法论\n- 学术诚信问题\n\n### 关键发现\n- 研究 agent 完成后需要编译成综合报告\n- 使用 WebFetch 获取完整内容而非仅依赖搜索摘要",
  "applies_when": [],
  "do_not_apply_when": []
}
---

# 1. Web Search 工作模式

> author: m1 · confidence: 0.85


### 模式描述
Agent 被指示使用 WebSearch 进行多角度研究任务，通常以 team-lead 任务分配形式出现。

### 典型指令模板
```
You are a data collection agent. Search for discussions about [topic].
Use WebSearch with queries like:
- "keyword1" "keyword2"
- site:example.com "query"
Focus on:
1. [Aspect 1]
2. [Aspect 2]
3. [Aspect 3]
For relevant content, use WebFetch to get full text.
```

### 常见研究主题
- AI 研究批评与伦理问题（vibe coding 学术讨论）
- 可复现性与验证
- Hacker News 讨论
- 图表创建方法论
- 学术诚信问题

### 关键发现
- 研究 agent 完成后需要编译成综合报告
- 使用 WebFetch 获取完整内容而非仅依赖搜索摘要
