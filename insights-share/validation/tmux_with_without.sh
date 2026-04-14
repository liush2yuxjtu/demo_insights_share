#!/usr/bin/env bash
# WITH/WITHOUT tmux 对照实验
# - WITHOUT 轮：纯净 claude 会话（无 insights-wiki skill）
# - WITH 轮：先把 insights-wiki skill 拷到 ~/.claude/skills/，再启会话
# 两轮都通过 tmux send-keys 发起 claude -p，60 秒后用 sed 去 ANSI 落盘
set -u

REPO_ROOT="/Users/m1/projects/demo_insights_share"
DELIV="${REPO_ROOT}/insights-share/validation/reports/deliverables"
SKILL_SRC="${REPO_ROOT}/insights-share/demo_codes/.claude/skills/insights-wiki"
SKILL_DST="${HOME}/.claude/skills/insights-wiki"
PROMPT='Our checkout API is timing out, postgres is rejecting new connections during the lunch spike'
WAIT_SEC=60

mkdir -p "${DELIV}"

log() { printf '[%s] %s\n' "$(date +%H:%M:%S)" "$*"; }

run_round() {
  local round="$1"   # without / with
  local round_upper
  round_upper=$(echo "${round}" | tr '[:lower:]' '[:upper:]')
  local session="insights_${round}"
  local raw="/tmp/insights_${round}.out"
  local out="${DELIV}/claude_export_${round_upper}.txt"

  log "=== ${round_upper} 轮开始 ==="
  tmux kill-session -t "${session}" 2>/dev/null || true
  rm -f "${raw}"

  log "tmux 启动 session=${session}"
  tmux new-session -d -s "${session}" -x 200 -y 50
  # send-keys: 用 tee 保存原始输出，2>&1 合流
  tmux send-keys -t "${session}" "claude -p \"${PROMPT}\" 2>&1 | tee ${raw}; echo __DONE__" Enter

  log "等待 ${WAIT_SEC} 秒让 claude -p 出结果"
  local elapsed=0
  while [ "${elapsed}" -lt "${WAIT_SEC}" ]; do
    sleep 5
    elapsed=$((elapsed + 5))
    if [ -f "${raw}" ] && grep -q "__DONE__" "${raw}" 2>/dev/null; then
      log "检测到 __DONE__，提前结束等待 (elapsed=${elapsed}s)"
      break
    fi
    log "  ...elapsed=${elapsed}s, raw_size=$(stat -f%z ${raw} 2>/dev/null || echo 0)"
  done

  if [ ! -s "${raw}" ]; then
    log "[warn] ${raw} 为空，会话可能超时"
    printf '[会话超时] claude -p 在 %d 秒内未输出任何内容\n' "${WAIT_SEC}" > "${out}"
  else
    # 去 ANSI、去 __DONE__ 行
    sed -E 's/\x1b\[[0-9;]*[A-Za-z]//g' "${raw}" | grep -v '^__DONE__$' > "${out}"
    log "已写入 ${out} ($(wc -c < ${out}) 字节)"
  fi

  log "tmux kill-session ${session}"
  tmux kill-session -t "${session}" 2>/dev/null || true
  log "=== ${round_upper} 轮结束 ==="
  echo
}

# ---------- WITHOUT 轮 ----------
# 确保 skill 不在 ~/.claude/skills/ 下
if [ -d "${SKILL_DST}" ]; then
  log "WITHOUT 轮前临时移除 ${SKILL_DST}"
  mv "${SKILL_DST}" "${SKILL_DST}.bak.$$"
fi
run_round "without"

# ---------- WITH 轮 ----------
if [ ! -f "${SKILL_SRC}/SKILL.md" ]; then
  log "[warn] ${SKILL_SRC}/SKILL.md 不存在，Team A 尚未完成 skill 化"
  log "[warn] 跳过 WITH 轮，写占位文件"
  cat > "${DELIV}/claude_export_WITH.txt" <<'EOF'
[等待 Team A] insights-share/demo_codes/.claude/skills/insights-wiki/SKILL.md 不存在
[等待 Team A] WITH 轮被跳过，待 skill 就绪后由 Team C 补跑
EOF
else
  log "拷贝 skill 到 ${SKILL_DST}"
  mkdir -p "${SKILL_DST}"
  cp -r "${SKILL_SRC}/." "${SKILL_DST}/"
  run_round "with"
fi

log "全部完成。产物："
ls -la "${DELIV}/claude_export_"*.txt
