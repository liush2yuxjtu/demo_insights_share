#!/usr/bin/env bash
# ================================================================
# run_topic_walkthrough.sh — Topic 工作流线性演示
# ================================================================
set -e
PORT=7821
STORE_DIR=$(pwd)/insights-share/demo_codes/wiki_tree
PYTHON_BIN="${PWD}/insights-share/demo_codes/.venv/bin/python"
LOG_FILE="${PWD}/examples/topic_walkthrough.log"

REPO_ROOT="/Users/m1/projects/demo_insights_share"
cd "${REPO_ROOT}"

log() { printf '[%s] %s\n' "$(date +%H:%M:%S)" "$*" | tee -a "${LOG_FILE}"; }

cleanup() {
  pkill -f "insights_cli.py serve" 2>/dev/null || true
}
trap cleanup EXIT

# 1. 启动 server
log "Step 1: 启动 insightsd (tree mode) port ${PORT}"
cd insights-share/demo_codes
"${PYTHON_BIN}" insights_cli.py serve --host 0.0.0.0 --port $PORT --store ./wiki_tree --store-mode tree &
SERVER_PID=$!
sleep 2

if ! curl -sf http://127.0.0.1:$PORT/insights >/dev/null; then
  log "daemon 健康检查失败"
  exit 1
fi
log "daemon 启动成功"

# 2. Topic + Example 发布
log "Step 2: Topic + Example 发布"
"${PYTHON_BIN}" insights_cli.py topic-create postgres-pool-exhaustion \
    --title "PostgreSQL 连接池耗尽" --tags postgres connection-pool --wiki-type database 2>&1 | tee -a "${LOG_FILE}"
"${PYTHON_BIN}" insights_cli.py publish seeds/alice_pgpool.json 2>&1 | tee -a "${LOG_FILE}"
"${PYTHON_BIN}" insights_cli.py publish seeds/bob_pgpool_bad.json 2>&1 | tee -a "${LOG_FILE}"

# 3. 读端验证
log "Step 3: 读端验证"
log "=== topics ==="
curl -s http://127.0.0.1:$PORT/topics | tee -a "${LOG_FILE}" | python -m json.tool 2>/dev/null || cat
log "=== good examples ==="
curl -s "http://127.0.0.1:$PORT/topics/postgres-pool-exhaustion/examples?label=good" | tee -a "${LOG_FILE}" | python -m json.tool 2>/dev/null || cat
log "=== bad examples ==="
curl -s "http://127.0.0.1:$PORT/topics/postgres-pool-exhaustion/examples?label=bad" | tee -a "${LOG_FILE}" | python -m json.tool 2>/dev/null || cat

# 4. Relabel CLI 流程
log "Step 4: Relabel bob from bad to good"
"${PYTHON_BIN}" insights_cli.py relabel bob-pgpool-bad-2026-04-12 --to good --by admin 2>&1 | tee -a "${LOG_FILE}"
log "=== topic show after relabel ==="
"${PYTHON_BIN}" insights_cli.py topic-show postgres-pool-exhaustion 2>&1 | tee -a "${LOG_FILE}"

# 5. raw_log 完整性
log "Step 5: raw_log 文件验证"
log "=== alice raw_log ==="
cat wiki_tree/database/raw/alice-pgpool-2026-04-10.jsonl 2>/dev/null | head || log "alice raw not found"
log "=== bob raw_log ==="
cat wiki_tree/database/raw/bob-pgpool-bad-2026-04-12.txt 2>/dev/null | head || log "bob raw not found"

# 6. effective_label summary
log "=== effective_label summary ==="
curl -s "http://127.0.0.1:$PORT/topics/postgres-pool-exhaustion/effective_labels" | tee -a "${LOG_FILE}" | python -m json.tool 2>/dev/null || cat

kill $SERVER_PID 2>/dev/null || true
log "[green] topic walkthrough ok"
echo "[green] topic walkthrough ok" >> "${LOG_FILE}"
