#!/usr/bin/env bash
# ================================================================
# without_reproduce.sh — A/B 对照 · WITHOUT 版（无 insights-wiki skill）
# ----------------------------------------------------------------
# 流程：
#   1. 重置 /tmp/demo_insights_A，并清理 ~/.claude/skills/insights-wiki（若存在则暂存到 .bak）
#   2. tmux new-session 启动纯净 shell
#   3. 通过 tmux send-keys 执行 claude -p
#      prompt 内要求 Claude 先跑 !pwd、列出顶层 filetree，再答技术问题
#   4. 轮询 __DONE__ 标记，最长 120s
#   5. 去 ANSI 落盘成 /tmp/demo_insights_A/A_without.log 和 claude_export_WITHOUT.md
#   6. tmux send "clear" + kill-session 收尾
# 用法：
#   bash insights-share/validation/without_reproduce.sh
# ================================================================
set -u

REPO_ROOT="/Users/m1/projects/demo_insights_share"
DELIV="${REPO_ROOT}/insights-share/validation/reports/deliverables"
SKILL_DST="${HOME}/.claude/skills/insights-wiki"
SKILL_SERVER_DST="${HOME}/.claude/skills/insights-wiki-server"
WORKSPACE_A="/tmp/demo_insights_A"
SESSION="insights_without_repro"
RAW="${WORKSPACE_A}/A_without.raw"
LOG="${WORKSPACE_A}/A_without.log"
PROMPT_FILE="${WORKSPACE_A}/insights_without_prompt.txt"
WRAPPER="${WORKSPACE_A}/insights_without_wrapper.sh"
MD="${DELIV}/claude_export_WITHOUT.md"
WAIT_SEC=150

# 核心 prompt：让 Claude 先自检环境（pwd + filetree）再答技术问题
# 写到文件，由 wrapper cat 读入，避免 tmux send-keys 对中文/换行/引号的截断
PROMPT='请严格按顺序执行三步。第一步：运行 !pwd 打印当前工作目录。第二步：运行 !ls -la ~/.claude/skills/ 展示已安装的 skill 列表（若目录不存在也要显示该事实）。第三步：回答 — 我们的 checkout API 正在超时，postgres 在午餐高峰拒绝新连接，应该如何诊断与修复？请给出可执行的 SQL 与代码片段。'

mkdir -p "${DELIV}"
log() { printf '[%s] %s\n' "$(date +%H:%M:%S)" "$*"; }

# ---------- Step 0: 清理 skill 环境 ----------
log "=== WITHOUT 轮开始 ==="
pkill -f "insights_cli.py serve" 2>/dev/null || true
rm -rf "${WORKSPACE_A}"
mkdir -p "${WORKSPACE_A}"
cd "${WORKSPACE_A}"
log "Step 0: 工作目录已重置 → ${WORKSPACE_A}"
if [ -d "${SKILL_DST}" ]; then
  log "Step 0a: 发现已有 ${SKILL_DST}，移动到 .bak.$$"
  mv "${SKILL_DST}" "${SKILL_DST}.bak.$$"
fi
if [ -d "${SKILL_SERVER_DST}" ]; then
  log "Step 0b: 发现已有 ${SKILL_SERVER_DST}，移动到 .bak.$$"
  mv "${SKILL_SERVER_DST}" "${SKILL_SERVER_DST}.bak.$$"
fi
log "Step 0c: 清理完成，~/.claude/skills/ 中不存在 insights-wiki*"

# ---------- Step 1: 写 prompt 文件 + wrapper 脚本 ----------
log "Step 1a: 写 prompt 文件 ${PROMPT_FILE}"
printf '%s' "${PROMPT}" > "${PROMPT_FILE}"
log "  prompt $(wc -c < "${PROMPT_FILE}" | tr -d ' ') 字节"

log "Step 1b: 写 wrapper 脚本 ${WRAPPER}"
cat > "${WRAPPER}" <<WRAPPER_EOF
#!/usr/bin/env bash
cd "${WORKSPACE_A}"
claude -p "\$(cat ${PROMPT_FILE})" 2>&1 | tee "${RAW}"
echo __DONE__
WRAPPER_EOF
chmod +x "${WRAPPER}"

# ---------- Step 2: tmux 启动并执行 wrapper ----------
tmux kill-session -t "${SESSION}" 2>/dev/null || true
rm -f "${RAW}"
log "Step 2a: tmux new-session -d -s ${SESSION} -x 220 -y 60"
tmux new-session -d -s "${SESSION}" -x 220 -y 60

log "Step 2b: tmux send-keys bash ${WRAPPER}"
tmux send-keys -t "${SESSION}" "bash ${WRAPPER}" Enter

# ---------- Step 3: 轮询等待 ----------
log "Step 3: 轮询等待 __DONE__（最长 ${WAIT_SEC}s）"
elapsed=0
while [ "${elapsed}" -lt "${WAIT_SEC}" ]; do
  sleep 5
  elapsed=$((elapsed + 5))
  if [ -f "${RAW}" ] && grep -q "^__DONE__$" "${RAW}" 2>/dev/null; then
    log "  检测到 __DONE__，提前结束 (elapsed=${elapsed}s)"
    break
  fi
  size=$(stat -f%z "${RAW}" 2>/dev/null || echo 0)
  log "  ...elapsed=${elapsed}s raw_size=${size}"
done

# ---------- Step 4: 去 ANSI 落盘 md ----------
log "Step 4: 清洗 ANSI 写入 ${MD}"
if [ -s "${RAW}" ]; then
  sed -E 's/\x1b\[[0-9;]*[A-Za-z]//g' "${RAW}" | grep -v '^__DONE__$' > "${LOG}"
else
  printf '[会话超时] claude -p 在 %d 秒内未输出任何内容\n' "${WAIT_SEC}" > "${LOG}"
fi
{
  printf '# Claude Export — WITHOUT 版（无 insights-wiki skill）\n\n'
  printf '## 元信息\n\n'
  printf -- '- 时间：%s\n' "$(date '+%Y-%m-%d %H:%M:%S')"
  printf -- '- 模式：A/B 对照 · WITHOUT 轮\n'
  printf -- '- tmux 会话：%s\n' "${SESSION}"
  printf -- '- 工作目录：%s\n' "${WORKSPACE_A}"
  printf -- '- 日志：%s\n' "${LOG}"
  printf -- '- skill 状态：~/.claude/skills/ 下无 insights-wiki* 目录\n'
  printf -- '- prompt：\n\n'
  printf '```\n%s\n```\n\n' "${PROMPT}"
  printf '## Claude 原始输出\n\n'
  printf '```\n'
  cat "${LOG}"
  printf '```\n'
} > "${MD}"
log "  已写入 ${MD}（$(wc -c < "${MD}" | tr -d ' ') 字节）"
log "  A 日志保存在 ${LOG}（$(wc -c < "${LOG}" | tr -d ' ') 字节）"

# ---------- Step 5: tmux 清屏并关闭 ----------
log "Step 5: tmux send clear + kill-session"
tmux send-keys -t "${SESSION}" "clear" Enter 2>/dev/null || true
sleep 1
tmux kill-session -t "${SESSION}" 2>/dev/null || true

# ---------- Step 6: 恢复可能被暂存的 skill ----------
if [ -d "${SKILL_DST}.bak.$$" ]; then
  log "Step 6a: 恢复 ${SKILL_DST} from .bak.$$"
  mv "${SKILL_DST}.bak.$$" "${SKILL_DST}"
fi
if [ -d "${SKILL_SERVER_DST}.bak.$$" ]; then
  log "Step 6b: 恢复 ${SKILL_SERVER_DST} from .bak.$$"
  mv "${SKILL_SERVER_DST}.bak.$$" "${SKILL_SERVER_DST}"
fi

log "=== WITHOUT 轮结束 ==="
ls -la "${MD}" "${LOG}"
