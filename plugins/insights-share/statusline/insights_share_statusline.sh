#!/usr/bin/env bash
# insights-share statusline badge 渲染器
#
# 契约（proposal/proposal_statusline.md）：
#   - 输出单行 badge：[share ✓ N/today] / [share … N/today] / [share ✗ N/today] / [share ⚠ stale] / [share 🔒 sig-fail]
#   - 渲染耗时 < 100 ms
#   - daemon 探活短超时 300 ms + 本地 60 s TTL 缓存
#   - skill 装配性：ls ~/.claude/skills/insights-share/SKILL.md
#   - 计数：~/.cache/insights-share/today_count.json
#   - stale 判定：~/.cache/insights-share/manifest.json 超过 TTL 未同步
#   - A/B 开关：SHARE_STATUSLINE=off 时输出空串（保持 A 侧零特征）
#   - badge 本体 ≤ 20 字符（不含 ANSI 色）
#
# 环境变量：
#   INSIGHTS_SHARE_URL     daemon base url，默认 http://127.0.0.1:7821
#   SHARE_STATUSLINE       "off" 时整条链路禁用（用于 A 侧录制）
#   SHARE_STATUSLINE_NO_COLOR  非空时禁用 ANSI 色（兼容纯日志场景）
#   SHARE_STATUSLINE_STALE_TTL_SECONDS  本地缓存 stale TTL，默认 86400

set -u
umask 077

if [[ "${SHARE_STATUSLINE:-}" == "off" ]]; then
  exit 0
fi

WIKI_URL="${INSIGHTS_SHARE_URL:-http://127.0.0.1:7821}"
CACHE_DIR="${HOME}/.cache/insights-share"
TODAY_JSON="${CACHE_DIR}/today_count.json"
MANIFEST_JSON="${CACHE_DIR}/manifest.json"
HEALTH_CACHE="${CACHE_DIR}/.health_cache"
IN_FLIGHT_FLAG="${CACHE_DIR}/.in_flight"
SKILL_MARK="${HOME}/.claude/skills/insights-share/SKILL.md"
STALE_TTL_SECONDS="${SHARE_STATUSLINE_STALE_TTL_SECONDS:-86400}"

mkdir -p "${CACHE_DIR}" 2>/dev/null || true

# ---- 色彩 ----
if [[ -t 1 && -z "${SHARE_STATUSLINE_NO_COLOR:-}" ]]; then
  C_OK=$'\033[32m'
  C_WAIT=$'\033[33m'
  C_FAIL=$'\033[31m'
  C_WARN=$'\033[33m'
  C_LOCK=$'\033[31m'
  C_RESET=$'\033[0m'
else
  C_OK=""
  C_WAIT=""
  C_FAIL=""
  C_WARN=""
  C_LOCK=""
  C_RESET=""
fi

# ---- 计数读取 ----
count=0
if [[ -r "${TODAY_JSON}" ]]; then
  today=$(date +%F)
  stored_date=$(sed -n 's/.*"date"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' "${TODAY_JSON}" | head -n1)
  stored_count=$(sed -n 's/.*"count"[[:space:]]*:[[:space:]]*\([0-9]*\).*/\1/p' "${TODAY_JSON}" | head -n1)
  if [[ "${stored_date}" == "${today}" && -n "${stored_count}" ]]; then
    count="${stored_count}"
  fi
fi

# ---- in-flight 检测（flag 文件 mtime < 3s 视为 …）----
in_flight=0
if [[ -f "${IN_FLIGHT_FLAG}" ]]; then
  now_epoch=$(date +%s)
  flag_epoch=$(stat -f '%m' "${IN_FLIGHT_FLAG}" 2>/dev/null || stat -c '%Y' "${IN_FLIGHT_FLAG}" 2>/dev/null || echo 0)
  if (( now_epoch - flag_epoch < 3 )); then
    in_flight=1
  fi
fi

# ---- skill 装配性 ----
skill_ok=0
[[ -r "${SKILL_MARK}" ]] && skill_ok=1

# ---- daemon 探活（60s TTL 缓存）----
daemon_ok=0
cache_valid=0
if [[ -r "${HEALTH_CACHE}" ]]; then
  cache_epoch=$(stat -f '%m' "${HEALTH_CACHE}" 2>/dev/null || stat -c '%Y' "${HEALTH_CACHE}" 2>/dev/null || echo 0)
  now_epoch=$(date +%s)
  if (( now_epoch - cache_epoch < 60 )); then
    cache_valid=1
    cached=$(cat "${HEALTH_CACHE}" 2>/dev/null)
    [[ "${cached}" == "ok" ]] && daemon_ok=1
  fi
fi

if (( cache_valid == 0 )); then
  probe_status=$(curl -s --max-time 0.3 -o /dev/null -w '%{http_code}' \
    "${WIKI_URL}/healthz" 2>/dev/null || echo "000")
  # 兼容旧端点 /health（proposal 两种写法）
  if [[ "${probe_status}" != "200" ]]; then
    probe_status=$(curl -s --max-time 0.3 -o /dev/null -w '%{http_code}' \
      "${WIKI_URL}/health" 2>/dev/null || echo "000")
  fi
  if [[ "${probe_status}" == "200" ]]; then
    daemon_ok=1
    printf 'ok' > "${HEALTH_CACHE}" 2>/dev/null || true
  else
    printf 'fail' > "${HEALTH_CACHE}" 2>/dev/null || true
  fi
fi

# ---- stale 判定（manifest.last_sync_at 超过 TTL）----
stale=0
sig_fail=0
if [[ -r "${MANIFEST_JSON}" ]]; then
  sig_fail="$(
    python3 - "${MANIFEST_JSON}" <<'PY' 2>/dev/null || echo 0
import json
import sys
from pathlib import Path

try:
    payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
except Exception:
    print(0)
    raise SystemExit(0)

failures = ((payload.get("signature") or {}).get("failures") or [])
print(1 if isinstance(failures, list) and len(failures) > 0 else 0)
PY
  )"
  stale="$(
    python3 - "${MANIFEST_JSON}" "${STALE_TTL_SECONDS}" <<'PY' 2>/dev/null || echo 0
import datetime as dt
import json
import sys
from pathlib import Path

manifest = Path(sys.argv[1])
ttl_seconds = int(sys.argv[2])
try:
    data = json.loads(manifest.read_text(encoding="utf-8"))
except Exception:
    print(0)
    raise SystemExit(0)

last_sync_at = data.get("last_sync_at")
if not isinstance(last_sync_at, str) or not last_sync_at.strip():
    print(0)
    raise SystemExit(0)

normalized = last_sync_at.strip()
if normalized.endswith("Z"):
    normalized = normalized[:-1] + "+00:00"
try:
    last_sync = dt.datetime.fromisoformat(normalized)
except ValueError:
    try:
        last_sync = dt.datetime.strptime(normalized, "%Y-%m-%dT%H:%M:%S%z")
    except ValueError:
        print(0)
        raise SystemExit(0)

if last_sync.tzinfo is None:
    last_sync = last_sync.replace(tzinfo=dt.datetime.now().astimezone().tzinfo)

age = (dt.datetime.now().astimezone() - last_sync.astimezone()).total_seconds()
print(1 if age >= ttl_seconds else 0)
PY
  )"
fi

# ---- 状态决策 ----
if (( skill_ok == 0 || daemon_ok == 0 )); then
  symbol="✗"
  color="${C_FAIL}"
elif (( in_flight == 1 )); then
  symbol="…"
  color="${C_WAIT}"
elif (( sig_fail == 1 )); then
  symbol="🔒"
  color="${C_LOCK}"
elif (( stale == 1 )); then
  symbol="⚠"
  color="${C_WARN}"
else
  symbol="✓"
  color="${C_OK}"
fi

if [[ "${symbol}" == "⚠" ]]; then
  printf '%s[share ⚠ stale]%s\n' "${color}" "${C_RESET}"
elif [[ "${symbol}" == "🔒" ]]; then
  printf '%s[share 🔒 sig-fail]%s\n' "${color}" "${C_RESET}"
else
  printf '%s[share %s %s/today]%s\n' "${color}" "${symbol}" "${count}" "${C_RESET}"
fi
