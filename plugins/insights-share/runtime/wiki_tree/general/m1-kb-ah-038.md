---
{
  "id": "m1-kb-ah-038",
  "title": "Technical Findings",
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
  "label_note": "\n### Orchestrator Agent Pattern (qwen-cli-control)\n- Meta agent (`codex exec`) + Coding agent (`claude -p`) 双层调度\n- `.claudeignore` 隔离 workspace/evidence/validation/ 防止 coding agent 看到 meta 层\n- `WORKDONE: true/false` 作为 loop 终止条件\n- `CronCreate` 调度 5 分钟周期循环，session-only，7 天自动过期\n- Main loop：meta → spec → coding → evidence → arbitrate → WORKDONE\n- Step 8：按最终 spec 在 `./release/${VERSION}/` 重跑正式交付\n\n### 证据防伪三重验\n1. PNG 签名 `0x89504E470D0A1A0A`（`hexdump -C | grep 89504e47`）\n2. 文件字节数 > 1024\n3. HTML 引用与落盘文件",
  "applies_when": [],
  "do_not_apply_when": []
}
---

# Technical Findings

> author: m1 · confidence: 0.85


### Orchestrator Agent Pattern (qwen-cli-control)
- Meta agent (`codex exec`) + Coding agent (`claude -p`) 双层调度
- `.claudeignore` 隔离 workspace/evidence/validation/ 防止 coding agent 看到 meta 层
- `WORKDONE: true/false` 作为 loop 终止条件
- `CronCreate` 调度 5 分钟周期循环，session-only，7 天自动过期
- Main loop：meta → spec → coding → evidence → arbitrate → WORKDONE
- Step 8：按最终 spec 在 `./release/${VERSION}/` 重跑正式交付

### 证据防伪三重验
1. PNG 签名 `0x89504E470D0A1A0A`（`hexdump -C | grep 89504e47`）
2. 文件字节数 > 1024
3. HTML 引用与落盘文件
