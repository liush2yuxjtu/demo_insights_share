---
{
  "id": "m1-kb-ah-050",
  "title": "5. Actionable Insights",
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
  "label_note": "\n### 开发规范\n1. **绝对路径优先**: 涉及文件路径时优先使用绝对路径，避免 cwd 问题\n2. **unittest 替代 pytest**: macOS 环境有 PEP 668 限制，直接用 `unittest`\n3. **Python 路径指定**: 始终用 `/opt/homebrew/bin/python3` 避免 pyenv 干扰\n\n### OpenClaw Plugin 开发流程\n1. 创建 `openclaw.plugin.json` 清单\n2. 实现 `index.ts` 入口，调用 `definePluginEntry`\n3. 用 `registerService` 实现后台循环\n4. 用 `NDJSON bridge` 连接 Python 运行时\n5. 注册 `registerTool` / `registerHook` / `registerContextEngine`\n\n### Sensor Ladder 实现\n- 每个版本增加 5 条新 sensor\n- sensor 命令用 `$PY` 变量引用绝对路径 Python\n- 测试脚本输出 `TOTA",
  "applies_when": [],
  "do_not_apply_when": []
}
---

# 5. Actionable Insights

> author: m1 · confidence: 0.85


### 开发规范
1. **绝对路径优先**: 涉及文件路径时优先使用绝对路径，避免 cwd 问题
2. **unittest 替代 pytest**: macOS 环境有 PEP 668 限制，直接用 `unittest`
3. **Python 路径指定**: 始终用 `/opt/homebrew/bin/python3` 避免 pyenv 干扰

### OpenClaw Plugin 开发流程
1. 创建 `openclaw.plugin.json` 清单
2. 实现 `index.ts` 入口，调用 `definePluginEntry`
3. 用 `registerService` 实现后台循环
4. 用 `NDJSON bridge` 连接 Python 运行时
5. 注册 `registerTool` / `registerHook` / `registerContextEngine`

### Sensor Ladder 实现
- 每个版本增加 5 条新 sensor
- sensor 命令用 `$PY` 变量引用绝对路径 Python
- 测试脚本输出 `TOTA
