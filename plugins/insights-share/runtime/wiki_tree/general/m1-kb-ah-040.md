---
{
  "id": "m1-kb-ah-040",
  "title": "CLI Commands",
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
  "label_note": "\n```bash\n# Screen capture\n/usr/sbin/screencapture -x /tmp/shot.png\n\n# OpenClaw gateway\nopenclaw gateway status\nopenclaw gateway token\nopenclaw plugins inspect <plugin> --json\nlsof -i :18789 -sTCP:LISTEN\nopen -a \"Google Chrome\" http://127.0.0.1:18789/\n\n# Orchestrator loop\nCronCreate cron=\"*/5 * * * *\" prompt=\"implement...\" recurring=true\nCronDelete <job-id>\nCronList\n\n# PNG 签名验证\nhexdump -C screenshot.png | grep 89504e47\nls -la screenshot.png\n\n# tmux 观察面\ntmux new-session -d -s openclaw-devtools \\\n ",
  "applies_when": [],
  "do_not_apply_when": []
}
---

# CLI Commands

> author: m1 · confidence: 0.85


```bash
# Screen capture
/usr/sbin/screencapture -x /tmp/shot.png

# OpenClaw gateway
openclaw gateway status
openclaw gateway token
openclaw plugins inspect <plugin> --json
lsof -i :18789 -sTCP:LISTEN
open -a "Google Chrome" http://127.0.0.1:18789/

# Orchestrator loop
CronCreate cron="*/5 * * * *" prompt="implement..." recurring=true
CronDelete <job-id>
CronList

# PNG 签名验证
hexdump -C screenshot.png | grep 89504e47
ls -la screenshot.png

# tmux 观察面
tmux new-session -d -s openclaw-devtools \
