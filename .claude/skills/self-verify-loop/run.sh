#!/usr/bin/env bash
# self-verify-loop run.sh — stub 首版
#
# 完整实现见 SKILL.md 伪码 + docs/rules/self-verify-loop.md
# 首版：参数解析 + 日志路径准备 + 占位 stub，返回 exit 2 提示 "not implemented"。
# 下个 PR 逐步落地 tier_meta / tier_demo。

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
LOG_DIR="$PROJECT_ROOT/insights-share/validation/reports"
LOG="$LOG_DIR/self_verify_loop.log"

mkdir -p "$LOG_DIR"

MAX_FAST="${MAX_FAST:-5}"
TIMEOUT_SEC="${TIMEOUT_SEC:-300}"
POLL_SEC="${POLL_SEC:-2}"
AUTO_PATCH=""
FAST_ONLY=""
NO_AUTO_REGISTER=""
OVERRIDE_REASON=""
SCOPE="auto"

while [[ $# -gt 0 ]]; do
  case "$1" in
    claude-md|feature|all|auto) SCOPE="$1"; shift ;;
    --max-fast) MAX_FAST="$2"; shift 2 ;;
    --timeout-sec) TIMEOUT_SEC="$2"; shift 2 ;;
    --fast-only) FAST_ONLY=1; shift ;;
    --auto-patch) AUTO_PATCH=1; shift ;;
    --no-auto-register) NO_AUTO_REGISTER=1; shift ;;
    --override) OVERRIDE_REASON="$2"; shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done

iso_now() { date -Iseconds; }

log_line() {
  printf '[%s] %s\n' "$(iso_now)" "$*" >>"$LOG"
}

if [[ -n "$OVERRIDE_REASON" ]]; then
  log_line "[override] [reason=$OVERRIDE_REASON]"
  log_line "--- OVERALL --- [OVERRIDE] [$(iso_now)]"
  echo "override: $OVERRIDE_REASON" >&2
  exit 3
fi

log_line "[stub] [scope=$SCOPE] [max_fast=$MAX_FAST] [timeout=$TIMEOUT_SEC] [auto_patch=${AUTO_PATCH:-0}]"
log_line "--- OVERALL --- [NOT_IMPLEMENTED] [$(iso_now)]"

cat >&2 <<EOF
self-verify-loop run.sh is a stub in this PR.
Scope=$SCOPE
Full for-loop implementation pending (see SKILL.md + docs/rules/self-verify-loop.md).
Exit 2 = environment/not-implemented per spec.
EOF

exit 2
