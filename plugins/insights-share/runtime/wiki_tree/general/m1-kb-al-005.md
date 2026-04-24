---
{
  "id": "m1-kb-al-005",
  "title": "可执行洞察",
  "author": "m1",
  "confidence": 0.85,
  "tags": [
    "knowledge-extraction",
    "session-analysis",
    "group_al"
  ],
  "status": "active",
  "topic_id": "m1-kb-al",
  "label": "good",
  "label_note": "\n1. **caveman mode** 适合简单快速任务，节省 ~75% token，但安全/不可逆操作必须退出\n2. **agent-judge 双探针** 是 self-verify 的核心，比硬编码关键词更鲁棒\n3. **语言裁判** 强制 chinese-only，发现任何外语碎片都是 FAIL\n4. **hook 降级**: OpenIslandHooks bridge 不可用时继续执行，不阻塞\n5. **skill-creator**: 创建 skill 要保持 concise，context window 是公共资源",
  "applies_when": [],
  "do_not_apply_when": []
}
---

# 可执行洞察

> author: m1 · confidence: 0.85


1. **caveman mode** 适合简单快速任务，节省 ~75% token，但安全/不可逆操作必须退出
2. **agent-judge 双探针** 是 self-verify 的核心，比硬编码关键词更鲁棒
3. **语言裁判** 强制 chinese-only，发现任何外语碎片都是 FAIL
4. **hook 降级**: OpenIslandHooks bridge 不可用时继续执行，不阻塞
5. **skill-creator**: 创建 skill 要保持 concise，context window 是公共资源
