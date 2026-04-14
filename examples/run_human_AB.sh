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
GITHUB_URL="https://github.com/liush2yuxjtu/demo_insights_share.git"

WORKSPACE_A="/tmp/demo_insights_A"
WORKSPACE_B="/tmp/demo_insights_B"
CLONE_DIR="${WORKSPACE_B}/isw-clone"
DAEMON_LOG="${WORKSPACE_B}/isd.log"

A_EXPORT="${WORKSPACE_A}/A_without.human.md"
B_EXPORT="${WORKSPACE_B}/B_with.human.md"
A_SNAPSHOT="${WORKSPACE_A}/A_without.human.tmux-snapshot.txt"
B_SNAPSHOT="${WORKSPACE_B}/B_with.human.tmux-snapshot.txt"

SKILL_DST="${HOME}/.claude/skills/insights-wiki"
SKILL_SERVER_DST="${HOME}/.claude/skills/insights-wiki-server"
SKILL_BAK="${HOME}/.claude/skills/insights-wiki.human-bak.$$"
SKILL_SERVER_BAK="${HOME}/.claude/skills/insights-wiki-server.human-bak.$$"

PROMPT_WITHOUT='请严格按顺序执行三步。第一步：运行 !pwd 打印当前工作目录。第二步：运行 !ls -la ~/.claude/skills/ 展示已安装的 skill 列表（若目录不存在也要显示该事实）。第三步：回答 — 我们的 checkout API 正在超时，postgres 在午餐高峰拒绝新连接，应该如何诊断与修复？请给出可执行的 SQL 与代码片段。若意外出现 LAN 卡片 alice-pgpool-2026-04-10，请明确说明这是污染。'
PROMPT_WITH='请严格按顺序执行三步。第一步：运行 !pwd 打印当前工作目录。第二步：运行 !ls -la ~/.claude/skills/ 展示已安装的 skill 列表。第三步：回答 — 我们的 checkout API 正在超时，postgres 在午餐高峰拒绝新连接，应该如何诊断与修复？请给出可执行的 SQL 与代码片段；若 insights-wiki 注入了 LAN 实战卡片请明确引用 alice-pgpool-2026-04-10。'

WAIT_CLAUDE_READY=10
WAIT_ANSWER=150
WAIT_EXPORT=5

log() { printf '[%s] %s\n' "$(date +%H:%M:%S)" "$*"; }

backup_active_skills() {
  mkdir -p "${HOME}/.claude/skills"
  if [ -d "${SKILL_DST}" ]; then
    mv "${SKILL_DST}" "${SKILL_BAK}"
  fi
  if [ -d "${SKILL_SERVER_DST}" ]; then
    mv "${SKILL_SERVER_DST}" "${SKILL_SERVER_BAK}"
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

cleanup() {
  tmux kill-session -t "human_without" 2>/dev/null || true
  tmux kill-session -t "human_with" 2>/dev/null || true
  pkill -f "insights_cli.py serve" 2>/dev/null || true
  restore_active_skills
}

trap cleanup EXIT

prepare_workspace_a() {
  log "A 轮前置：重置 ${WORKSPACE_A}"
  pkill -f "insights_cli.py serve" 2>/dev/null || true
  rm -rf "${WORKSPACE_A}"
  mkdir -p "${WORKSPACE_A}"
}

prepare_workspace_b() {
  log "B 轮前置：重置 ${WORKSPACE_B}"
  pkill -f "insights_cli.py serve" 2>/dev/null || true
  rm -rf "${WORKSPACE_B}"
  mkdir -p "${WORKSPACE_B}" "${HOME}/.claude/skills"

  log "B 轮前置：clone github 仓库 → ${CLONE_DIR}"
  git clone --depth 1 "${GITHUB_URL}" "${CLONE_DIR}" 2>&1 | tail -5

  log "B 轮前置：安装 insights-wiki skill 到 ~/.claude/skills/"
  cp -r "${CLONE_DIR}/insights-share/demo_codes/.claude/skills/insights-wiki" "${HOME}/.claude/skills/"
  cp -r "${CLONE_DIR}/insights-share/demo_codes/.claude/skills/insights-wiki-server" "${HOME}/.claude/skills/"

  log "B 轮前置：启动 daemon → ${DAEMON_LOG}"
  (cd "${CLONE_DIR}/insights-share/demo_codes" && nohup python3 insights_cli.py serve --host 0.0.0.0 --port 7821 --store ./wiki.json > "${DAEMON_LOG}" 2>&1 &)
  sleep 3
  if ! curl -sf http://127.0.0.1:7821/insights >/dev/null; then
    log "✗ daemon 健康检查失败"
    exit 3
  fi
}

run_tmux_human() {
  local round="$1"
  local prompt="$2"
  local out="$3"
  local snapshot="$4"
  local session="human_${round}"
  local start_cmd=""

  case "${round}" in
    without) start_cmd="cd \"${WORKSPACE_A}\" && claude" ;;
    with)    start_cmd="cd \"${WORKSPACE_B}\" && claude" ;;
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

  log "Step 3: 发送 prompt（${#prompt} 字符）"
  tmux send-keys -t "${session}" -l "${prompt}"
  tmux send-keys -t "${session}" Enter

  log "Step 4: 等待 ${WAIT_ANSWER}s 让 Claude 回答完成"
  local elapsed=0
  while [ "${elapsed}" -lt "${WAIT_ANSWER}" ]; do
    sleep 10
    elapsed=$((elapsed + 10))
    log "  ...elapsed=${elapsed}s/${WAIT_ANSWER}s"
  done

  log "Step 5: 发送 /export ${out}"
  tmux send-keys -t "${session}" -l "/export ${out}"
  tmux send-keys -t "${session}" Enter
  sleep "${WAIT_EXPORT}"

  log "Step 6: capture-pane → ${snapshot}"
  tmux capture-pane -t "${session}" -p > "${snapshot}" 2>/dev/null || true

  log "Step 7: 发送 /exit"
  tmux send-keys -t "${session}" -l "/exit"
  tmux send-keys -t "${session}" Enter
  sleep 2
  tmux kill-session -t "${session}" 2>/dev/null || true

  if [ ! -s "${out}" ]; then
    log "✗ ${out} 为空或不存在"
    exit 5
  fi

  if [ "${round}" = "without" ]; then
    cp "${A_EXPORT}" "${EXAMPLES_DIR}/A_without.human.md"
  else
    cp "${B_EXPORT}" "${EXAMPLES_DIR}/B_with.human.md"
  fi

  log "✓ ${out} 落盘成功 ($(wc -c < "${out}" | tr -d ' ') 字节)"
  log "=== ${round} human 轮结束 ==="
  echo
}

backup_active_skills
prepare_workspace_a
run_tmux_human without "${PROMPT_WITHOUT}" "${A_EXPORT}" "${A_SNAPSHOT}"

prepare_workspace_b
run_tmux_human with "${PROMPT_WITH}" "${B_EXPORT}" "${B_SNAPSHOT}"

log "全部完成："
ls -la "${A_EXPORT}" "${B_EXPORT}" "${EXAMPLES_DIR}/A_without.human.md" "${EXAMPLES_DIR}/B_with.human.md" 2>&1
