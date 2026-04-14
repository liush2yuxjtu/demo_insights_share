#!/usr/bin/env bash
# ================================================================
# run_human_AB.sh — 用 tmux + 交互式 claude + /export 生成 A/B human logs
# ----------------------------------------------------------------
# 与 agent 版（claude -p --output-format json）的区别：
#   agent = 非交互，JSON 结构输出，给程序解析
#   human = 交互式会话，用 /export slash command 导出，给人看
# ================================================================
set -u

REPO_ROOT="/Users/m1/projects/demo_insights_share"
DEMO_CWD="${REPO_ROOT}/insights-share/demo_codes"
OUT_DIR="/tmp/ab_clean"
PROMPT='我们的 checkout API 正在超时，postgres 在午餐高峰拒绝新连接，应该如何诊断与修复？请给出可执行的 SQL 与代码片段。若有 insights-wiki 注入的 LAN 实战卡片请明确引用。'
WAIT_CLAUDE_READY=10   # 启动 claude 交互 UI 就绪
WAIT_ANSWER=150        # 等待 Claude 回答完成
WAIT_EXPORT=5          # /export 写盘

mkdir -p "${OUT_DIR}"
log() { printf '[%s] %s\n' "$(date +%H:%M:%S)" "$*"; }

run_tmux_human() {
  local round="$1"         # without / with
  local session="human_${round}"
  local out="${OUT_DIR}/$(echo "${round}" | awk '{print toupper(substr($0,1,1))tolower(substr($0,2))}' | sed 's/Without/A_without/;s/With/B_with/').human.md"
  case "${round}" in
    without) out="${OUT_DIR}/A_without.human.md" ;;
    with)    out="${OUT_DIR}/B_with.human.md" ;;
  esac

  log "=== ${round} human 轮开始 → ${out} ==="

  # 清理可能残留的 tmux session 和旧导出
  tmux kill-session -t "${session}" 2>/dev/null || true
  rm -f "${out}"

  # Step 1: 启动 tmux + 交互式 claude
  log "Step 1: tmux new-session -d -s ${session} -x 220 -y 60"
  tmux new-session -d -s "${session}" -x 220 -y 60
  tmux send-keys -t "${session}" "cd ${DEMO_CWD} && claude" Enter

  log "Step 2: 等待 ${WAIT_CLAUDE_READY}s 让 claude UI 就绪"
  sleep "${WAIT_CLAUDE_READY}"

  # Step 3: 发送 prompt
  log "Step 3: tmux send-keys 发送 prompt（${#PROMPT} 字符）"
  # 用 -l (literal) 避免元字符被解析，然后单独发 Enter
  tmux send-keys -t "${session}" -l "${PROMPT}"
  tmux send-keys -t "${session}" Enter

  # Step 4: 等待 Claude 回答
  log "Step 4: 等待 ${WAIT_ANSWER}s 让 Claude 回答完成"
  local elapsed=0
  while [ "${elapsed}" -lt "${WAIT_ANSWER}" ]; do
    sleep 10
    elapsed=$((elapsed + 10))
    log "  ...elapsed=${elapsed}s/${WAIT_ANSWER}s"
  done

  # Step 5: 发送 /export <path>
  log "Step 5: 发送 /export ${out}"
  tmux send-keys -t "${session}" -l "/export ${out}"
  tmux send-keys -t "${session}" Enter
  sleep "${WAIT_EXPORT}"

  # Step 6: 退出
  log "Step 6: 发送 /exit"
  tmux send-keys -t "${session}" -l "/exit"
  tmux send-keys -t "${session}" Enter
  sleep 2

  # 落盘前抓一个全屏快照做证据
  tmux capture-pane -t "${session}" -p > "${out%.md}.tmux-snapshot.txt" 2>/dev/null || true

  tmux kill-session -t "${session}" 2>/dev/null || true

  if [ -s "${out}" ]; then
    log "  ✓ ${out} 落盘成功 ($(wc -c < "${out}") 字节)"
  else
    log "  ✗ ${out} 为空或不存在"
  fi
  log "=== ${round} human 轮结束 ==="
  echo
}

# ---------- 主流程 ----------

# A 轮：先把 skills 移走
log "A 轮前置：移走 insights-wiki skill"
if [ -d "${HOME}/.claude/skills/insights-wiki" ]; then
  mv "${HOME}/.claude/skills/insights-wiki" "${HOME}/.claude/skills/insights-wiki.human-bak.$$"
fi
if [ -d "${HOME}/.claude/skills/insights-wiki-server" ]; then
  mv "${HOME}/.claude/skills/insights-wiki-server" "${HOME}/.claude/skills/insights-wiki-server.human-bak.$$"
fi
run_tmux_human without

# B 轮：恢复 skills + 确认 daemon
log "B 轮前置：恢复 insights-wiki skill"
if [ -d "${HOME}/.claude/skills/insights-wiki.human-bak.$$" ]; then
  mv "${HOME}/.claude/skills/insights-wiki.human-bak.$$" "${HOME}/.claude/skills/insights-wiki"
fi
if [ -d "${HOME}/.claude/skills/insights-wiki-server.human-bak.$$" ]; then
  mv "${HOME}/.claude/skills/insights-wiki-server.human-bak.$$" "${HOME}/.claude/skills/insights-wiki-server"
fi
if ! curl -sf -m 2 http://127.0.0.1:7821/insights >/dev/null; then
  log "B 轮前置：daemon 未运行，启动之"
  (cd "${DEMO_CWD}" && nohup python3 insights_cli.py serve --host 0.0.0.0 --port 7821 --store ./wiki.json > /tmp/isd.log 2>&1 &)
  sleep 3
fi
run_tmux_human with

log "全部完成："
ls -la "${OUT_DIR}/A_without.human.md" "${OUT_DIR}/B_with.human.md" 2>&1
