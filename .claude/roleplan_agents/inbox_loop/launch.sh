#!/usr/bin/env bash
# launch.sh — kick off the inner-loop subagent in the background.
#
# The subagent writes only to inbox_dir; it does NOT call AskUserQuestion.
# The main session polls inbox_dir via main_drain.py.
#
# usage:
#   ./launch.sh <task-file> <artifact-file> [inbox-dir] [iters]
#
# defaults:
#   inbox-dir = $PWD/docs/user_complaints_inbox
#   iters     = 5
#
# artifacts:
#   $inbox_dir/run.pid          # subagent pid
#   $inbox_dir/subagent.log     # stdout + stderr
#   $inbox_dir/summary.json     # normal-exit sentinel (absent => crash)

set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$HERE/../../.." && pwd)"

TASK_FILE="${1:-}"
ARTIFACT_FILE="${2:-}"
INBOX_DIR="${3:-$REPO_ROOT/docs/user_complaints_inbox}"
ITERS="${4:-5}"

if [ -z "$TASK_FILE" ] || [ -z "$ARTIFACT_FILE" ]; then
  cat >&2 <<USAGE
[launch] missing args
usage: $0 <task-file> <artifact-file> [inbox-dir] [iters]
USAGE
  exit 1
fi

[ -f "$TASK_FILE" ] || { echo "[launch] task-file not found: $TASK_FILE" >&2; exit 1; }
[ -f "$ARTIFACT_FILE" ] || { echo "[launch] artifact-file not found: $ARTIFACT_FILE" >&2; exit 1; }

ROLES_DIR="$(cd "$HERE/.." && pwd)"
JUDGE="$HERE/judge.sh"
[ -x "$JUDGE" ] || { echo "[launch] judge not executable: $JUDGE" >&2; exit 1; }

VENV_PY="$REPO_ROOT/insights-share/demo_codes/.venv/bin/python"
if [ -x "$VENV_PY" ]; then
  PY="$VENV_PY"
else
  PY="$(command -v python3 || command -v python)"
fi
[ -x "$PY" ] || { echo "[launch] no python interpreter found" >&2; exit 1; }

mkdir -p "$INBOX_DIR"
PID_FILE="$INBOX_DIR/run.pid"
LOG_FILE="$INBOX_DIR/subagent.log"

if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
  echo "[launch] subagent already running pid=$(cat "$PID_FILE")" >&2
  exit 1
fi

echo "[launch] starting subagent" >&2
echo "[launch]   task-file     : $TASK_FILE" >&2
echo "[launch]   artifact-file : $ARTIFACT_FILE" >&2
echo "[launch]   inbox-dir     : $INBOX_DIR" >&2
echo "[launch]   iters         : $ITERS" >&2

nohup "$PY" "$HERE/subagent.py" \
  --task-file "$TASK_FILE" \
  --artifact-file "$ARTIFACT_FILE" \
  --inbox-dir "$INBOX_DIR" \
  --roles-dir "$ROLES_DIR" \
  --judge "$JUDGE" \
  --iters "$ITERS" \
  --resume \
  > "$LOG_FILE" 2>&1 &

echo $! > "$PID_FILE"
echo "[launch] pid=$(cat "$PID_FILE") log=$LOG_FILE" >&2
