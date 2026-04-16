#!/usr/bin/env bash
# ================================================================
# run_human_AB.sh — 用 tmux + 交互式 claude + /export 生成 A/B human logs
# ----------------------------------------------------------------
# 目标：
#   1. A/WITHOUT 必须跑在 /tmp/demo_insights_A，且不能加载 insights-wiki
#   2. B/WITH 必须跑在 /tmp/demo_insights_B，显式安装 skill + 启 daemon
#   3. /export 产物先写到 /tmp/{workspace}/，再回写 examples/*.human.md
# ================================================================
set -u

REPO_ROOT="/Users/m1/projects/demo_insights_share"
EXAMPLES_DIR="${REPO_ROOT}/examples"
DEMO_ENV_SRC="${REPO_ROOT}/insights-share/demo_codes/.env"

WORKSPACE_A="/tmp/demo_insights_A"
WORKSPACE_B="/tmp/demo_insights_B"
CLONE_DIR="${WORKSPACE_B}/isw-clone"
DAEMON_LOG="${WORKSPACE_B}/isd.log"
PYTHON_BIN="${REPO_ROOT}/insights-share/demo_codes/.venv/bin/python"
A_SETTINGS="${WORKSPACE_A}/.claude/settings.json"
B_SETTINGS="${WORKSPACE_B}/.claude/settings.json"
ACTIVE_SETTINGS_DST="${HOME}/.claude/settings.json"
ACTIVE_SETTINGS_BAK="${HOME}/.claude/settings.json.human-bak.$$"

A_EXPORT="${WORKSPACE_A}/A_without.human.md"
B_EXPORT="${WORKSPACE_B}/B_with.human.md"
A_SNAPSHOT="${WORKSPACE_A}/A_without.human.tmux-snapshot.txt"
B_SNAPSHOT="${WORKSPACE_B}/B_with.human.tmux-snapshot.txt"

SKILL_DST="${HOME}/.claude/skills/insights-wiki"
SKILL_SERVER_DST="${HOME}/.claude/skills/insights-wiki-server"
SKILL_BAK="${HOME}/.claude/skills/insights-wiki.human-bak.$$"
SKILL_SERVER_BAK="${HOME}/.claude/skills/insights-wiki-server.human-bak.$$"
CACHE_DIR="${HOME}/.cache/insights-wiki"
CACHE_BAK="${HOME}/.cache/insights-wiki.human-bak.$$"
COMMON_PROMPT_FILE="${EXAMPLES_DIR}/COMMON_PROMPT.txt"

COMMON_PROMPT=""

WAIT_CLAUDE_READY=10
WAIT_TRUST_CONFIRM=4
WAIT_ANSWER=240
WAIT_EXPORT=5
PANE_STABLE_MIN_ELAPSED=120
PANE_STABLE_REQUIRED=2

log() { printf '[%s] %s\n' "$(date +%H:%M:%S)" "$*"; }

require_file() {
  local path="$1"
  local label="$2"
  if [ ! -f "${path}" ]; then
    log "✗ 缺少 ${label}: ${path}"
    exit 12
  fi
}

count_matches() {
  local needle="$1"
  local file="$2"
  local count=""
  count="$(grep -F -c -- "${needle}" "${file}" 2>/dev/null || true)"
  printf '%s' "${count:-0}"
}

load_common_prompt() {
  require_file "${COMMON_PROMPT_FILE}" "A/B COMMON_PROMPT"
  COMMON_PROMPT="$(cat "${COMMON_PROMPT_FILE}")"
}

normalize_prompt_text() {
  printf '%s\n' "$1" \
    | tr '\n' ' ' \
    | sed -E 's/[[:space:]]+/ /g; s/^[[:space:]]+//; s/[[:space:]]+$//'
}

extract_export_prompt() {
  local file="$1"
  awk '
    /^❯ / { capture = 1 }
    capture {
      if ($0 ~ /^⏺ /) exit
      print
    }
  ' "${file}" \
    | sed -E '1s/^❯[[:space:]]*//; s/^[[:space:]]{2,}//' \
    | tr '\n' ' ' \
    | sed -E 's/[[:space:]]+/ /g; s/^[[:space:]]+//; s/[[:space:]]+$//'
}

assert_export_prompt_matches_common() {
  local round="$1"
  local file="$2"
  local expected_prompt=""
  local actual_prompt=""

  expected_prompt="$(normalize_prompt_text "${COMMON_PROMPT}")"
  actual_prompt="$(extract_export_prompt "${file}")"

  if [ -z "${actual_prompt}" ]; then
    log "✗ ${round} human 导出缺少可抽取 prompt"
    exit 13
  fi

  if [ "${actual_prompt}" != "${expected_prompt}" ]; then
    log "✗ ${round} human 导出 prompt 与 COMMON_PROMPT 不一致"
    log "  expected: ${expected_prompt}"
    log "  actual:   ${actual_prompt}"
    exit 14
  fi
}

assert_ab_prompts_identical() {
  local prompt_a=""
  local prompt_b=""

  prompt_a="$(extract_export_prompt "${A_EXPORT}")"
  prompt_b="$(extract_export_prompt "${B_EXPORT}")"

  if [ -z "${prompt_a}" ] || [ -z "${prompt_b}" ]; then
    log "✗ A/B 导出缺少 prompt，无法执行 strict A/B gate"
    exit 15
  fi

  if [ "${prompt_a}" != "${prompt_b}" ]; then
    log "✗ A/B 导出 prompt 不一致，strict A/B 失效"
    log "  A: ${prompt_a}"
    log "  B: ${prompt_b}"
    exit 16
  fi
}

backup_active_skills() {
  mkdir -p "${HOME}/.claude/skills"
  if [ -d "${SKILL_DST}" ]; then
    mv "${SKILL_DST}" "${SKILL_BAK}"
  fi
  if [ -d "${SKILL_SERVER_DST}" ]; then
    mv "${SKILL_SERVER_DST}" "${SKILL_SERVER_BAK}"
  fi
}

backup_active_cache() {
  mkdir -p "${HOME}/.cache"
  if [ -d "${CACHE_DIR}" ]; then
    mv "${CACHE_DIR}" "${CACHE_BAK}"
  fi
}

backup_active_settings() {
  mkdir -p "${HOME}/.claude"
  if [ -f "${ACTIVE_SETTINGS_DST}" ]; then
    cp "${ACTIVE_SETTINGS_DST}" "${ACTIVE_SETTINGS_BAK}"
  fi
}

restore_active_skills() {
  rm -rf "${SKILL_DST}" "${SKILL_SERVER_DST}"
  if [ -d "${SKILL_BAK}" ]; then
    mv "${SKILL_BAK}" "${SKILL_DST}"
  fi
  if [ -d "${SKILL_SERVER_BAK}" ]; then
    mv "${SKILL_SERVER_BAK}" "${SKILL_SERVER_DST}"
  fi
}

restore_active_cache() {
  rm -rf "${CACHE_DIR}"
  if [ -d "${CACHE_BAK}" ]; then
    mv "${CACHE_BAK}" "${CACHE_DIR}"
  fi
}

restore_active_settings() {
  if [ -f "${ACTIVE_SETTINGS_BAK}" ]; then
    mv "${ACTIVE_SETTINGS_BAK}" "${ACTIVE_SETTINGS_DST}"
  else
    rm -f "${ACTIVE_SETTINGS_DST}"
  fi
}

activate_settings() {
  local src="$1"
  mkdir -p "${HOME}/.claude"
  cp "${src}" "${ACTIVE_SETTINGS_DST}"
}

cleanup() {
  tmux kill-session -t "human_without" 2>/dev/null || true
  tmux kill-session -t "human_with" 2>/dev/null || true
  pkill -f "insights_cli.py serve" 2>/dev/null || true
  restore_active_settings
  restore_active_skills
  restore_active_cache
}

trap cleanup EXIT

prepare_workspace_a() {
  log "A 轮前置：重置 ${WORKSPACE_A}"
  pkill -f "insights_cli.py serve" 2>/dev/null || true
  rm -rf "${WORKSPACE_A}"
  mkdir -p "${WORKSPACE_A}"
  require_file "${DEMO_ENV_SRC}" "A/B 录制 .env"

  log "A 轮前置：强化净室隔离 — 显式删除 skill 目录"
  rm -rf "${SKILL_DST}" "${SKILL_SERVER_DST}"
  rm -rf "${CACHE_DIR}"

  if ls ~/.claude/skills/insights-wiki* 2>/dev/null | grep -q .; then
    log "✗ A 轮净室隔离失败：~/.claude/skills/insights-wiki* 仍有残留"
    ls -la ~/.claude/skills/ 2>&1 | sed 's/^/    /'
    exit 7
  fi
  if [ -e "${CACHE_DIR}" ]; then
    log "✗ A 轮净室隔离失败：${CACHE_DIR} 仍有残留"
    find "${CACHE_DIR}" -maxdepth 2 -type f 2>&1 | sed 's/^/    /'
    exit 17
  fi
  log "A 轮前置：✓ 净室隔离验证通过"

  log "A 轮前置：写入最小 Claude 配置 → ${A_SETTINGS}"
  write_a_workspace_settings
  activate_settings "${A_SETTINGS}"
}

sync_local_repo_snapshot() {
  log "B 轮前置：同步当前工作树 → ${CLONE_DIR}"
  rsync -a --delete \
    --exclude '.git' \
    --exclude '.venv' \
    --exclude '.pytest_cache' \
    --exclude '__pycache__' \
    --exclude '.DS_Store' \
    "${REPO_ROOT}/" "${CLONE_DIR}/"
}

write_a_workspace_settings() {
  mkdir -p "${WORKSPACE_A}/.claude"
  cat > "${A_SETTINGS}" <<EOF
{
  "env": {
    "CLAUDE_CODE_ENABLE_AWAY_SUMMARY": "0"
  },
  "permissions": {
    "defaultMode": "bypassPermissions"
  },
  "language": "Chinese",
  "skipDangerousModePermissionPrompt": true,
  "hooks": {}
}
EOF
}

write_b_workspace_settings() {
  mkdir -p "${WORKSPACE_B}/.claude"
  cat > "${B_SETTINGS}" <<EOF
{
  "env": {
    "CLAUDE_CODE_ENABLE_AWAY_SUMMARY": "0"
  },
  "permissions": {
    "defaultMode": "bypassPermissions"
  },
  "language": "Chinese",
  "skipDangerousModePermissionPrompt": true,
  "hooks": {
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "${PYTHON_BIN} ${CLONE_DIR}/insights-share/demo_codes/hooks/insights_stop_hook.py"
          }
        ]
      }
    ],
    "UserPromptSubmit": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "${PYTHON_BIN} ${CLONE_DIR}/insights-share/demo_codes/hooks/insights_prefetch.py >/dev/null 2>&1 &"
          }
        ]
      }
    ]
  }
}
EOF
}

prepare_workspace_b() {
  log "B 轮前置：重置 ${WORKSPACE_B}"
  pkill -f "insights_cli.py serve" 2>/dev/null || true
  rm -rf "${WORKSPACE_B}"
  mkdir -p "${WORKSPACE_B}" "${HOME}/.claude/skills"
  rm -rf "${CACHE_DIR}"

  if [ ! -x "${PYTHON_BIN}" ]; then
    log "✗ 缺少 hook/runtime Python：${PYTHON_BIN}"
    exit 8
  fi

  sync_local_repo_snapshot
  require_file "${CLONE_DIR}/insights-share/demo_codes/.env" "B 轮 clone .env"

  log "B 轮前置：安装 insights-wiki skill 到 ~/.claude/skills/"
  cp -r "${CLONE_DIR}/insights-share/demo_codes/.claude/skills/insights-wiki" "${HOME}/.claude/skills/"
  cp -r "${CLONE_DIR}/insights-share/demo_codes/.claude/skills/insights-wiki-server" "${HOME}/.claude/skills/"

  log "B 轮前置：写入 workspace hooks → ${B_SETTINGS}"
  write_b_workspace_settings
  activate_settings "${B_SETTINGS}"

  log "B 轮前置：启动 daemon → ${DAEMON_LOG}"
  (cd "${CLONE_DIR}/insights-share/demo_codes" && nohup "${PYTHON_BIN}" insights_cli.py serve --host 0.0.0.0 --port 7821 --store ./wiki.json > "${DAEMON_LOG}" 2>&1 &)
  sleep 3
  if ! curl -sf http://127.0.0.1:7821/insights >/dev/null; then
    log "✗ daemon 健康检查失败"
    exit 3
  fi
  log "B 轮前置：注入 Topic + Seeds（alice good + bob bad）"
  (cd "${CLONE_DIR}/insights-share/demo_codes" && "${PYTHON_BIN}" insights_cli.py topic-create postgres-pool-exhaustion \
    --title "PostgreSQL 连接池耗尽" --tags postgres connection-pool 2>/dev/null || true)
  (cd "${CLONE_DIR}/insights-share/demo_codes" && "${PYTHON_BIN}" insights_cli.py publish seeds/alice_pgpool.json)
  (cd "${CLONE_DIR}/insights-share/demo_codes" && "${PYTHON_BIN}" insights_cli.py publish seeds/bob_pgpool_bad.json)

  log "B 轮前置：同步预热缓存（消除 UserPromptSubmit & 竞态）"
  "${PYTHON_BIN}" "${CLONE_DIR}/insights-share/demo_codes/hooks/insights_prefetch.py"
  if [ ! -f "${CACHE_DIR}/manifest.json" ]; then
    log "✗ B 轮缓存预热失败：${CACHE_DIR}/manifest.json 未生成"
    exit 18
  fi
  log "B 轮前置：✓ 缓存预热完成：$(cat "${CACHE_DIR}/manifest.json")"
}

run_tmux_human() {
  local round="$1"
  local prompt="$2"
  local out="$3"
  local snapshot="$4"
  local session="human_${round}"
  local start_cmd=""
  local env_src=""

  case "${round}" in
    without)
      env_src="${DEMO_ENV_SRC}"
      start_cmd="cd \"${WORKSPACE_A}\" && bash -lc 'set -a; source \"${env_src}\"; set +a; exec claude'"
      ;;
    with)
      env_src="${CLONE_DIR}/insights-share/demo_codes/.env"
      start_cmd="cd \"${WORKSPACE_B}\" && bash -lc 'set -a; source \"${env_src}\"; set +a; exec claude'"
      ;;
    *) log "未知 round: ${round}"; exit 4 ;;
  esac

  log "=== ${round} human 轮开始 → ${out} ==="

  tmux kill-session -t "${session}" 2>/dev/null || true
  rm -f "${out}" "${snapshot}"

  log "Step 1: tmux new-session -d -s ${session} -x 220 -y 60"
  tmux new-session -d -s "${session}" -x 220 -y 60
  tmux send-keys -t "${session}" "${start_cmd}" Enter

  log "Step 2: 等待 ${WAIT_CLAUDE_READY}s 让 claude UI 就绪"
  sleep "${WAIT_CLAUDE_READY}"

  log "Step 3: 先按 Enter 接受 trust prompt"
  tmux send-keys -t "${session}" Enter
  sleep "${WAIT_TRUST_CONFIRM}"

  log "Step 4: 发送 prompt（${#prompt} 字符）"
  tmux send-keys -t "${session}" -l "${prompt}"
  tmux send-keys -t "${session}" Enter

  log "Step 5: 等待 ${WAIT_ANSWER}s 让 Claude 回答完成"
  local elapsed=0
  local prev_pane=""
  local stable_hits=0
  while [ "${elapsed}" -lt "${WAIT_ANSWER}" ]; do
    sleep 10
    elapsed=$((elapsed + 10))
    local pane=""
    pane="$(tmux capture-pane -t "${session}" -p 2>/dev/null || true)"
    if [ "${elapsed}" -ge "${PANE_STABLE_MIN_ELAPSED}" ] && [ -n "${pane}" ]; then
      if [ "${pane}" = "${prev_pane}" ]; then
        stable_hits=$((stable_hits + 1))
      else
        stable_hits=0
      fi
      log "  ...elapsed=${elapsed}s/${WAIT_ANSWER}s stable=${stable_hits}/${PANE_STABLE_REQUIRED}"
      if [ "${stable_hits}" -ge "${PANE_STABLE_REQUIRED}" ]; then
        log "  ...pane 连续稳定，提前结束等待"
        break
      fi
    else
      log "  ...elapsed=${elapsed}s/${WAIT_ANSWER}s"
    fi
    prev_pane="${pane}"
  done

  log "Step 6: 发送 /export ${out}"
  tmux send-keys -t "${session}" -l "/export ${out}"
  tmux send-keys -t "${session}" Enter
  sleep "${WAIT_EXPORT}"

  log "Step 7: capture-pane → ${snapshot}"
  tmux capture-pane -t "${session}" -p > "${snapshot}" 2>/dev/null || true

  log "Step 8: 发送 /exit"
  tmux send-keys -t "${session}" -l "/exit"
  tmux send-keys -t "${session}" Enter
  sleep 2
  tmux kill-session -t "${session}" 2>/dev/null || true

  if [ ! -s "${out}" ]; then
    if [ -s "${snapshot}" ] && rg -q "You've hit your limit|resets" "${snapshot}"; then
      log "✗ ${round} human 导出失败：Claude 当前会话额度已用尽，请额度恢复后重跑"
      exit 6
    fi
    log "✗ ${out} 为空或不存在"
    exit 5
  fi

  local alice_count
  local bob_count
  local skill_count
  local stop_error_count
  local interrupted_count
  alice_count="$(count_matches "alice-pgpool-2026-04-10" "${out}")"
  bob_count="$(count_matches "bob-pgpool-bad-2026-04-12" "${out}")"
  skill_count="$(count_matches "Skill(insights-wiki)" "${out}")"
  stop_error_count="$(count_matches "Stop hook error" "${out}")"
  interrupted_count="$(count_matches "Interrupted" "${out}")"

  log "Step 9: 校验导出 prompt 与 COMMON_PROMPT"
  assert_export_prompt_matches_common "${round}" "${out}"

  log "Step 10: 校验导出内容 alice=${alice_count} bob=${bob_count} skill=${skill_count} stop_error=${stop_error_count} interrupted=${interrupted_count}"
  if [ "${stop_error_count}" -ne 0 ] || [ "${interrupted_count}" -ne 0 ]; then
    log "✗ ${round} human 导出包含 Stop hook 错误或中断痕迹"
    exit 9
  fi
  if [ "${round}" = "without" ]; then
    if [ "${alice_count}" -ne 0 ] || [ "${skill_count}" -ne 0 ]; then
      log "✗ A 轮导出被污染：期望 alice=0 且 Skill(insights-wiki)=0"
      exit 10
    fi
  else
    if [ "${alice_count}" -lt 1 ]; then
      log "✗ B 轮导出未引用 alice-pgpool-2026-04-10"
      exit 11
    fi
    if [ "${bob_count}" -lt 1 ]; then
      log "✗ B 轮导出未引用 bob-pgpool-bad-2026-04-12"
      exit 19
    fi
  fi

  log "✓ ${out} 落盘成功 ($(wc -c < "${out}" | tr -d ' ') 字节)"
  log "=== ${round} human 轮结束 ==="
  echo
}

backup_active_settings
backup_active_skills
backup_active_cache
load_common_prompt
prepare_workspace_a
run_tmux_human without "${COMMON_PROMPT}" "${A_EXPORT}" "${A_SNAPSHOT}"

prepare_workspace_b
run_tmux_human with "${COMMON_PROMPT}" "${B_EXPORT}" "${B_SNAPSHOT}"

log "Step 11: 执行 strict A/B prompt equality gate"
assert_ab_prompts_identical

log "Step 12: prompt gate 通过，回写 examples/ human 资产"
cp "${A_EXPORT}" "${EXAMPLES_DIR}/A_without.human.md"
cp "${B_EXPORT}" "${EXAMPLES_DIR}/B_with.human.md"

log "全部完成："
ls -la "${A_EXPORT}" "${B_EXPORT}" "${EXAMPLES_DIR}/A_without.human.md" "${EXAMPLES_DIR}/B_with.human.md" 2>&1
