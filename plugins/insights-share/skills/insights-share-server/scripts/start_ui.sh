#!/usr/bin/env bash
# 后台启动 bundle-local insightsd + 自动弹出 dashboard kanban
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
RUNTIME_DIR="${INSIGHTS_SHARE_RUNTIME_DIR:-$PLUGIN_ROOT/runtime}"
STORE_DIR="${INSIGHTS_SHARE_STORE:-$RUNTIME_DIR/wiki_tree}"
HOST="${INSIGHTS_SHARE_HOST:-0.0.0.0}"
PORT="${INSIGHTS_SHARE_PORT:-7821}"
PY="${INSIGHTS_PYTHON:-}"

if [ -z "$PY" ]; then
  if command -v python3 >/dev/null 2>&1; then
    PY="$(command -v python3)"
  else
    PY="$(command -v python || true)"
  fi
fi

[ -n "$PY" ] || { echo "[insights-share-server] python not found" >&2; exit 127; }
[ -f "$RUNTIME_DIR/insights_cli.py" ] || {
  echo "[insights-share-server] runtime missing: $RUNTIME_DIR/insights_cli.py" >&2
  exit 2
}
[ -d "$STORE_DIR" ] || {
  echo "[insights-share-server] store missing: $STORE_DIR" >&2
  exit 2
}

export PYTHONPATH="$RUNTIME_DIR${PYTHONPATH:+:$PYTHONPATH}"
"$PY" "$RUNTIME_DIR/insights_cli.py" serve \
  --host "$HOST" --port "$PORT" \
  --store-mode tree --store "$STORE_DIR" \
  >/tmp/insightsd_ui.log 2>&1 &
PID=$!
for _ in 1 2 3 4 5 6 7 8 9 10; do
  curl -fs "http://127.0.0.1:${PORT}/healthz" >/dev/null && break
  sleep 0.5
done
LAN_IP=$(PYTHONPATH="$RUNTIME_DIR${PYTHONPATH:+:$PYTHONPATH}" "$PY" -c "from insightsd.server import _detect_lan_ip; print(_detect_lan_ip())")
echo "[insights-share-server] dashboard at http://${LAN_IP}:${PORT}/"
open -a "Google Chrome" "http://${LAN_IP}:${PORT}/" || echo "[warn] Chrome not available, dashboard at http://${LAN_IP}:${PORT}/"
wait $PID
