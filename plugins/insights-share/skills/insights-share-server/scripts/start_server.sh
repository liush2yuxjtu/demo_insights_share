#!/usr/bin/env bash
# 启动 insightsd 前台守护进程（tree 模式 + 0.0.0.0:7821）
# 注意：必须 cd 到 insights-share/demo_codes/，那里才有 insights_cli.py + wiki_tree/
set -euo pipefail
cd "$(dirname "$0")/../../../../../insights-share/demo_codes"
PY="${INSIGHTS_PYTHON:-$(pwd)/.venv/bin/python}"
[ -x "$PY" ] || PY="python"
exec "$PY" insights_cli.py serve \
  --host 0.0.0.0 --port 7821 \
  --store-mode tree --store ./wiki_tree
