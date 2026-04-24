---
{
  "id": "m1-kb-ag-004",
  "title": "Error Patterns",
  "author": "m1",
  "confidence": 0.85,
  "tags": [
    "knowledge-extraction",
    "session-analysis",
    "group_ag"
  ],
  "status": "active",
  "topic_id": "m1-kb-ag",
  "label": "good",
  "label_note": "\n- {\"verdict\":\"FAIL\",\"reason\":\"响应仅复述 start bootstrap 规则条款（描述性），未体现实际执行痕迹：无四文件读取、无 proposal 扫描、无闭环执行、无 PASS/FAIL 收尾。CLAUDE.md 要求实际执行 bootstrap 并输出证据，不是解释规则本身。\",\"suggested_patch\":\"\"}\n- **关键发现 — 我之前全错了**  start.demo.sh 第 90-96 行直说：  ``` # 不 symlink 用户全局 settings.json —— 全局里注册的是 continuous-learning 等 # 其他用户 hook，在沙箱 HOME 下 claude 解析路径时找不到脚本，会报 # 　Stop hook error: evaluate-session.sh: \n- 代码符合 plan spec。我注意到 `_http_get` 在 server 不可达时可能抛 ConnectionRefusedError（OSError 子类），不一定是 URLError。先清理端口并启动 server。",
  "applies_when": [],
  "do_not_apply_when": []
}
---

# Error Patterns

> author: m1 · confidence: 0.85


- {"verdict":"FAIL","reason":"响应仅复述 start bootstrap 规则条款（描述性），未体现实际执行痕迹：无四文件读取、无 proposal 扫描、无闭环执行、无 PASS/FAIL 收尾。CLAUDE.md 要求实际执行 bootstrap 并输出证据，不是解释规则本身。","suggested_patch":""}
- **关键发现 — 我之前全错了**  start.demo.sh 第 90-96 行直说：  ``` # 不 symlink 用户全局 settings.json —— 全局里注册的是 continuous-learning 等 # 其他用户 hook，在沙箱 HOME 下 claude 解析路径时找不到脚本，会报 # 　Stop hook error: evaluate-session.sh:
- 代码符合 plan spec。我注意到 `_http_get` 在 server 不可达时可能抛 ConnectionRefusedError（OSError 子类），不一定是 URLError。先清理端口并启动 server。
