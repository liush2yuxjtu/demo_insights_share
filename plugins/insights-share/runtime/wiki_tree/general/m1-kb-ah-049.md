---
{
  "id": "m1-kb-ah-049",
  "title": "4. Project-Specific Knowledge",
  "author": "m1",
  "confidence": 0.85,
  "tags": [
    "knowledge-extraction",
    "session-analysis",
    "group_ah"
  ],
  "status": "active",
  "topic_id": "m1-kb-ah",
  "label": "good",
  "label_note": "\n### screen-monitor-openclaw\n- **核心需求**: 15s 截图 + 意图理解 + TODO 记录 + 后台执行 + 隐藏需求 surprise\n- **证据目录结构**:\n  ```\n  evidence/v{N}/screenshots/   # PNG 截图\n  evidence/v{N}/actions/       # action_*.md 文件\n  evidence/v{N}/TODO.md        # 意图清单\n  evidence/v{N}/executions.jsonl  # 执行日志\n  evidence/v{N}/surprise.html  # 隐藏需求报告\n  evidence/v{N}/index.html     # 三列表验收报告\n  ```\n- **WORKDONE 协议**: spec 中 `WORKDONE: pending`，全部 sensor 通过后改为 `WORKDONE: true`\n\n### OpenClaw Gateway Config 冲突\n- **问题**: CLI 和 service 使用不",
  "applies_when": [],
  "do_not_apply_when": []
}
---

# 4. Project-Specific Knowledge

> author: m1 · confidence: 0.85


### screen-monitor-openclaw
- **核心需求**: 15s 截图 + 意图理解 + TODO 记录 + 后台执行 + 隐藏需求 surprise
- **证据目录结构**:
  ```
  evidence/v{N}/screenshots/   # PNG 截图
  evidence/v{N}/actions/       # action_*.md 文件
  evidence/v{N}/TODO.md        # 意图清单
  evidence/v{N}/executions.jsonl  # 执行日志
  evidence/v{N}/surprise.html  # 隐藏需求报告
  evidence/v{N}/index.html     # 三列表验收报告
  ```
- **WORKDONE 协议**: spec 中 `WORKDONE: pending`，全部 sensor 通过后改为 `WORKDONE: true`

### OpenClaw Gateway Config 冲突
- **问题**: CLI 和 service 使用不
