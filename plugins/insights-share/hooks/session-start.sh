#!/usr/bin/env bash
# insights-share plugin :: SessionStart hook (O6)
#
# M7_LATENCY_DEEP 优化项 O6：会话启动时预拉 topics.json 到 warm cache，
# 让首轮 /insights 查询省掉 ~300ms 的冷启动开销。
#
# 设计依据：proposal/proposal_generation_latency.md §优化方案 O6
# 与 §风险与约束（允许在此处唯一 soft-skip，因为 SessionStart 失败不能阻塞会话）。
#
# 拉取源链（依次尝试）：
#   1. $INSIGHTS_DAEMON_URL/topics
#   2. $INSIGHTS_DAEMON_URL/wiki/topics.json
#   3. 本地 fallback：<repo_root>/insights-share/demo_codes/wiki_tree/topics.json
#      （仅允许最后一层 local fallback；前两步 5xx 直接视为失败）
#
# 超时：curl --max-time 2 -sS --fail，无重试。Hook 自身最多延迟会话 ~2s。
# 成功：写 topics.json + warm.meta.json
# 失败：stderr 打一行 `[session-start] warm skipped: <reason>` 并 exit 0

set -euo pipefail

DAEMON_URL="${INSIGHTS_DAEMON_URL:-http://127.0.0.1:7821}"
WARM_DIR_DEFAULT="$HOME/.cache/insights-share/warm"
WARM_DIR="${INSIGHTS_WARM_DIR:-$WARM_DIR_DEFAULT}"

# plugin_root 定位：hook 文件所在 plugins/insights-share/hooks/*.sh
HOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(cd "$HOOK_DIR/.." && pwd)"
# plugin_root/.. = plugins/，再上一层到 repo root，再进 insights-share/demo_codes/wiki_tree/topics.json
LOCAL_TOPICS="$PLUGIN_ROOT/../../insights-share/demo_codes/wiki_tree/topics.json"

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
# 3) 本地 fallback：仅最后一层允许
elif [ -f "$LOCAL_TOPICS" ]; then
  if cp "$LOCAL_TOPICS" "$TMP_PATH" 2>/dev/null; then
    SOURCE="local:$LOCAL_TOPICS"
  else
    FAIL_REASON="local copy failed"
  fi
else
  FAIL_REASON="daemon unreachable and local topics.json missing"
fi

if [ -z "$SOURCE" ]; then
  rm -f "$TMP_PATH" 2>/dev/null || true
  echo "[session-start] warm skipped: ${FAIL_REASON:-all sources failed}" >&2
  exit 0
fi

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

exit 0
