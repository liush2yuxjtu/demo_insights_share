---
{
  "id": "m1-kb-ak-005",
  "title": "可操作洞察",
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
  "label_note": "\n1. **OpenIslandHooks 不可用时** → hook 链无法触发，但 session 本身可正常运行\n2. **TODO.md 重复条目** → 需要去重机制，相同语义不重复追加\n3. **screenshots 编号归零 bug** → 需在 `start.claude.sh` 中修复计数器持久化\n4. **caveman plugin 安装** → 可通过 marketplace 一键完成，无需手动 clone\n5. **session 短（<7 条）则 continuous-learning 跳过** → 短任务不适合 learn skill\n\n---\n\n*来源：243 个 jsonl 文件（group_ak），涵盖 simple-screen-monitor、skill-recorder、insights-share 多版本、slack-remote 等项目，2026-04-17 至 2026-04-22 时段。*",
  "applies_when": [],
  "do_not_apply_when": []
}
---

# 可操作洞察

> author: m1 · confidence: 0.85


1. **OpenIslandHooks 不可用时** → hook 链无法触发，但 session 本身可正常运行
2. **TODO.md 重复条目** → 需要去重机制，相同语义不重复追加
3. **screenshots 编号归零 bug** → 需在 `start.claude.sh` 中修复计数器持久化
4. **caveman plugin 安装** → 可通过 marketplace 一键完成，无需手动 clone
5. **session 短（<7 条）则 continuous-learning 跳过** → 短任务不适合 learn skill

---

*来源：243 个 jsonl 文件（group_ak），涵盖 simple-screen-monitor、skill-recorder、insights-share 多版本、slack-remote 等项目，2026-04-17 至 2026-04-22 时段。*
