#!/usr/bin/env bash
# insights-share plugin :: SessionStart hook (O6 + user-unaware full download)
#
# M7_LATENCY_DEEP 优化项 O6：会话启动时预拉 topics.json 到 warm cache，
# 让首轮 /insights 查询省掉 ~300ms 的冷启动开销。
#
# 扩展 user-unaware download：
# - 原来：topics.json metadata warm（轻量）
# - 新增：session_start_full_fetch.py 拉完整 cards + delta sync（ETag）
#   → 用户打开 Claude Code 时卡片已在本地缓存，后续 UserPromptSubmit
#     prefetch 几乎零延迟
#
# 两阶段均 soft-skip：失败只打 stderr，exit 0，不阻塞会话。
#
# 设计依据：proposal/proposal_generation_latency.md §O6
# 与 proposal.md user-unaware download 契约。

set -euo pipefail

DAEMON_URL="${INSIGHTS_SHARE_URL:-${INSIGHTS_DAEMON_URL:-http://192.168.22.42:7821}}"
WARM_DIR_DEFAULT="$HOME/.cache/insights-share/warm"
WARM_DIR="${INSIGHTS_WARM_DIR:-$WARM_DIR_DEFAULT}"

HOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(cd "$HOOK_DIR/.." && pwd)"
PYTHON_BIN="$(command -v python3 || true)"

mkdir -p "$WARM_DIR"

TOPICS_PATH="$WARM_DIR/topics.json"
META_PATH="$WARM_DIR/warm.meta.json"
TMP_PATH="$WARM_DIR/.topics.json.tmp"

SOURCE=""
FAIL_REASON=""

# 拉 URL 到 TMP_PATH；成功 return 0，失败 return 非 0（5xx/超时/connect refused 均算失败）
try_url() {
  local url="$1"
  if curl --fail --max-time 2 -sS -o "$TMP_PATH" "$url" 2>/dev/null; then
    return 0
  fi
  return 1
}

# 1) /topics
if try_url "$DAEMON_URL/topics"; then
  SOURCE="$DAEMON_URL/topics"
# 2) /wiki/topics.json
elif try_url "$DAEMON_URL/wiki/topics.json"; then
  SOURCE="$DAEMON_URL/wiki/topics.json"
else
  FAIL_REASON="daemon topics endpoints unreachable"
fi

if [ -z "$SOURCE" ]; then
  rm -f "$TMP_PATH" 2>/dev/null || true
  echo "[session-start] topics warm skipped: ${FAIL_REASON:-all sources failed}" >&2
else
  # 原子替换
  mv -f "$TMP_PATH" "$TOPICS_PATH"

  BYTES=$(wc -c < "$TOPICS_PATH" | tr -d ' ')
  WARMED_AT=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

  # topics_count 仅在 jq 可用时填入，否则 null
  if command -v jq >/dev/null 2>&1; then
    TOPICS_COUNT=$(jq 'if type=="array" then length elif .topics? then (.topics|length) else (keys|length) end' "$TOPICS_PATH" 2>/dev/null || echo "null")
    [ -z "$TOPICS_COUNT" ] && TOPICS_COUNT="null"
  else
    TOPICS_COUNT="null"
  fi

  # 写 meta（source 字段如果是 URL 加引号；local 同样字符串；BYTES/TOPICS_COUNT 是数字或 null）
  cat > "$META_PATH" <<EOF
{"warmed_at":"$WARMED_AT","source":"$SOURCE","bytes":$BYTES,"topics_count":$TOPICS_COUNT}
EOF
fi

# ---- Phase 2: Full card fetch with delta sync (user-unaware download) ----
# 调用 bundle-local session_start_full_fetch.py 拉完整卡片到 ~/.cache/insights-share/
FULL_FETCH_SCRIPT="$PLUGIN_ROOT/scripts/session_start_full_fetch.py"
if [ -f "$FULL_FETCH_SCRIPT" ]; then
  if [ -n "$PYTHON_BIN" ]; then
    "$PYTHON_BIN" "$FULL_FETCH_SCRIPT" >&2
  else
    echo "[session-start] python3 not found, skipping full card fetch" >&2
  fi
else
  echo "[session-start] session_start_full_fetch.py not found at $FULL_FETCH_SCRIPT" >&2
fi

exit 0
