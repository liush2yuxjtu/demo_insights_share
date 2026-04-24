---
{
  "id": "m1-kb-ah-042",
  "title": "Actionable Insights",
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
  "label_note": "\n1. **Never trust sub-agent claims, always re-verify independently** — v1 案例：coding agent 声称 8/8 PASS，实际 screenshots/ 为空\n2. **Anti-forgery: PNG signature + byte size + HTML consistency** — 三重验缺一不可\n3. **Orchestrator loop: meta → spec → code → evidence → arbitrate → WORKDONE** — 迭代收敛后取消 cron\n4. **Real sandbox: mktemp -d + trap EXIT + HOME/PATH 覆盖** — 脚本自称 sandbox 时必检\n5. **OpenClaw config 路径不匹配** — CLI 用 `~/.openclaw/`，service 可能用 `/tmp/openclaw-rec-*/.openclaw-config/`，排查时需确认真实日志路径\n6. **Deep resea",
  "applies_when": [],
  "do_not_apply_when": []
}
---

# Actionable Insights

> author: m1 · confidence: 0.85


1. **Never trust sub-agent claims, always re-verify independently** — v1 案例：coding agent 声称 8/8 PASS，实际 screenshots/ 为空
2. **Anti-forgery: PNG signature + byte size + HTML consistency** — 三重验缺一不可
3. **Orchestrator loop: meta → spec → code → evidence → arbitrate → WORKDONE** — 迭代收敛后取消 cron
4. **Real sandbox: mktemp -d + trap EXIT + HOME/PATH 覆盖** — 脚本自称 sandbox 时必检
5. **OpenClaw config 路径不匹配** — CLI 用 `~/.openclaw/`，service 可能用 `/tmp/openclaw-rec-*/.openclaw-config/`，排查时需确认真实日志路径
6. **Deep resea
