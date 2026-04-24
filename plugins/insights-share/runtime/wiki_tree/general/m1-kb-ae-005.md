---
{
  "id": "m1-kb-ae-005",
  "title": "Actionable Insights",
  "author": "m1",
  "confidence": 0.85,
  "tags": [
    "knowledge-extraction",
    "session-analysis",
    "group_ae"
  ],
  "status": "active",
  "topic_id": "m1-kb-ae",
  "label": "good",
  "label_note": "\n1. **Offline wiki search agent**：预加载 topic index hint 可快速定位 wiki_type，避免全量 glob\n2. **工具降级**：sdk-py 入口缺少 Glob 时用 `Bash ls` 替代\n3. **Background loop 任务**：通过 status.md 时间戳追加实现幂等确认，避免重复执行\n4. **Hook 降级**：OpenIslandHooks bridge 不可用不影响核心，agent 应能容错继续\n5. **Session slug**：word pair 模式比 UUID 更可读，适合人类追踪\n6. **Self-verify loop**：文件名编码了 project/branch/agent/timestamp/phase/iter/result 七元组信息\n\n---\n\n*提取自 243 个 jsonl 文件，去重合并。*",
  "applies_when": [],
  "do_not_apply_when": []
}
---

# Actionable Insights

> author: m1 · confidence: 0.85


1. **Offline wiki search agent**：预加载 topic index hint 可快速定位 wiki_type，避免全量 glob
2. **工具降级**：sdk-py 入口缺少 Glob 时用 `Bash ls` 替代
3. **Background loop 任务**：通过 status.md 时间戳追加实现幂等确认，避免重复执行
4. **Hook 降级**：OpenIslandHooks bridge 不可用不影响核心，agent 应能容错继续
5. **Session slug**：word pair 模式比 UUID 更可读，适合人类追踪
6. **Self-verify loop**：文件名编码了 project/branch/agent/timestamp/phase/iter/result 七元组信息

---

*提取自 243 个 jsonl 文件，去重合并。*
