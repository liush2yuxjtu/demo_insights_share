---
{
  "id": "m1-kb-ak-002",
  "title": "技术发现与模式",
  "author": "m1",
  "confidence": 0.85,
  "tags": [
    "knowledge-extraction",
    "session-analysis",
    "group_ak"
  ],
  "status": "active",
  "topic_id": "m1-kb-ak",
  "label": "good",
  "label_note": "\n### 1. 周期性截图分析循环（simple-screen-monitor）\n\n**核心链路：**\n```\nscreenshot → analysis-*.md → background-log.md → TODO.md\n```\n\n**观察到的循环节奏：**\n- 约每 2 分钟一轮截图\n- 每轮生成：`screenshots/screenshot-TIMESTAMP-0001.png` + `logs/analysis-TIMESTAMP.md` + background-log 行 + TODO 候选\n- 文件名中 `-0001` 后缀每轮重置（已知 bug）\n\n**background-log.md 格式：**\n```\n- YYYY-MM-DD HH:MM:SS | script=start.claude.sh | input=<path> | report=<path> | todo=<path>\n```\n\n### 2. CLAUDE.md 规则：只改 TODO 和 logs\n\n`simple-screen-monitor` 项目规则明确：\n- 只允许修改 `TODO.md`",
  "applies_when": [],
  "do_not_apply_when": []
}
---

# 技术发现与模式

> author: m1 · confidence: 0.85


### 1. 周期性截图分析循环（simple-screen-monitor）

**核心链路：**
```
screenshot → analysis-*.md → background-log.md → TODO.md
```

**观察到的循环节奏：**
- 约每 2 分钟一轮截图
- 每轮生成：`screenshots/screenshot-TIMESTAMP-0001.png` + `logs/analysis-TIMESTAMP.md` + background-log 行 + TODO 候选
- 文件名中 `-0001` 后缀每轮重置（已知 bug）

**background-log.md 格式：**
```
- YYYY-MM-DD HH:MM:SS | script=start.claude.sh | input=<path> | report=<path> | todo=<path>
```

### 2. CLAUDE.md 规则：只改 TODO 和 logs

`simple-screen-monitor` 项目规则明确：
- 只允许修改 `TODO.md`
