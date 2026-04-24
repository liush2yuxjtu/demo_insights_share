---
{
  "id": "m1-kb-aj-005",
  "title": "Actionable Insights",
  "author": "m1",
  "confidence": 0.85,
  "tags": [
    "knowledge-extraction",
    "session-analysis",
    "group_aj"
  ],
  "status": "active",
  "topic_id": "m1-kb-aj",
  "label": "good",
  "label_note": "\n- Use hookify rules with YAML frontmatter in .claude/hookify.*.local.md\n- Stop hook limitation: can only approve/block, cannot modify already-generated output\n- Before running on different GPU (e.g., Tesla T4 vs RTX 3090), run small soak test first\n- Remote notebook is for preview/debug only - real logic must be in reusable Python harness\n- Commits with 'simplify:' prefix should be skipped during automated review\n- When fixing torch.load, always use weights_only=True for security\n- Use double q",
  "applies_when": [],
  "do_not_apply_when": []
}
---

# Actionable Insights

> author: m1 · confidence: 0.85


- Use hookify rules with YAML frontmatter in .claude/hookify.*.local.md
- Stop hook limitation: can only approve/block, cannot modify already-generated output
- Before running on different GPU (e.g., Tesla T4 vs RTX 3090), run small soak test first
- Remote notebook is for preview/debug only - real logic must be in reusable Python harness
- Commits with 'simplify:' prefix should be skipped during automated review
- When fixing torch.load, always use weights_only=True for security
- Use double q
