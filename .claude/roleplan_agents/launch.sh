#!/usr/bin/env bash
# launch.sh — summon a roleplay agent via claudefast -p
#
# usage:
#   ./launch.sh <role> "<question>"
#   ./launch.sh list
#
# prereq:
#   - claudefast alias 已在 shell 中 (zsh function)
#   - insights-share plugin 已装 (可选; 未装时 agent 会降级)
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
ROLE="${1:-}"

case "$ROLE" in
  ""|-h|--help|help)
    echo "usage: $0 <role> <question>"
    echo "       $0 list"
    exit 0
    ;;
  list)
    echo "available roles:"
    for f in "$HERE"/prompt_*.md; do
      base="$(basename "$f" .md)"
      role="${base#prompt_}"
      desc="$(awk -F': ' '/^audience:/ {print $2; exit}' "$f")"
      printf "  %-12s %s\n" "$role" "${desc:-n/a}"
    done
    exit 0
    ;;
esac

shift || true
QUESTION="${*:-}"
PROMPT_FILE="$HERE/prompt_${ROLE}.md"

if [ ! -f "$PROMPT_FILE" ]; then
  echo "[err] role not found: $PROMPT_FILE" >&2
  echo "run: $0 list" >&2
  exit 1
fi

if [ -z "$QUESTION" ]; then
  echo "[err] question empty" >&2
  echo "usage: $0 $ROLE '<question>'" >&2
  exit 1
fi

if ! command -v claudefast >/dev/null 2>&1 && ! typeset -f claudefast >/dev/null 2>&1; then
  echo "[warn] claudefast 未在当前 shell, 尝试 zsh -ic 加载" >&2
fi

PAYLOAD="$(
  cat "$PROMPT_FILE"
  printf '\n\n---\n\n## User question\n\n%s\n' "$QUESTION"
)"

# 通过 zsh -ic 保证 claudefast function 可用
exec zsh -ic "claudefast -p \"\$(cat)\"" <<< "$PAYLOAD"
