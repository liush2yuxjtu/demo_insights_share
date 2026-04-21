#!/usr/bin/env bash
# judge helper: fallback claudefast -p -> claude -p --model haiku -> claude -p
# stdin = prompt; stdout = verdict
set -uo pipefail
PROMPT="$(cat)"
[ -z "$PROMPT" ] && { echo "[judge] empty prompt" >&2; exit 2; }

try_layer() {
  local label="$1"; shift
  local out
  out="$(printf '%s' "$PROMPT" | "$@" 2>/dev/null)"
  local rc=$?
  if [ $rc -eq 0 ] && [ -n "$out" ]; then
    printf '%s' "$out"
    return 0
  fi
  echo "[judge] $label failed rc=$rc" >&2
  return 1
}

try_layer "claudefast" /Users/m1/.local/bin/claudefast -p && exit 0
try_layer "claude-haiku" claude -p --model haiku && exit 0
try_layer "claude-full" claude -p && exit 0
echo "[judge] ALL LAYERS FAILED" >&2
exit 3
