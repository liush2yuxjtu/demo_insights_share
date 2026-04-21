#!/usr/bin/env bash
# 后台启动 insightsd + 自动弹出 dashboard kanban
set -euo pipefail
cd "$(dirname "$0")/../../../.."
[ -d .venv ] && source .venv/bin/activate
python insights_cli.py serve --host 0.0.0.0 --port 7821 --store-mode tree >/tmp/insightsd_ui.log 2>&1 &
PID=$!
for _ in 1 2 3 4 5 6 7 8 9 10; do
  curl -fs http://127.0.0.1:7821/healthz >/dev/null && break
  sleep 0.5
done
LAN_IP=$(python -c "from insightsd.server import _detect_lan_ip; print(_detect_lan_ip())")
echo "[insights-wiki-server] dashboard at http://${LAN_IP}:7821/"
open -a "Google Chrome" "http://${LAN_IP}:7821/" || echo "[warn] Chrome not available, dashboard at http://${LAN_IP}:7821/"
wait $PID
