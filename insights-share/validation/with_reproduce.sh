#!/usr/bin/env bash
# ================================================================
# with_reproduce.sh — A/B 对照 · WITH 版（安装 insights-wiki skill）
# ----------------------------------------------------------------
# 本脚本必须"从零开始"：
#   1. 重置 /tmp/demo_insights_B，并清空 ~/.claude/skills/insights-wiki*（确保干净环境）
#   2. git clone --depth 1 从 github 拉取 demo_insights_share 仓库
#      （关键：不从本地 filetree 复制，保证真实 setup 流程）
#   3. 从 cloned 目录把 insights-wiki / insights-wiki-server skill
#      复制到 ~/.claude/skills/
#   4. 打印 first-setup-guide，并在隔离目录里启动 daemon
#   5. tmux new-session 启动纯净 shell
#   6. 通过 tmux send-keys 执行 claude -p
#      prompt 内要求 Claude 先跑 !pwd、列出 filetree + skill 列表，再答技术问题
#   7. 轮询 __DONE__ 标记，最长 180s（skill 加载 + hook 预热需要时间）
#   8. 去 ANSI 落盘成 /tmp/demo_insights_B/B_with.log 和 claude_export_WITH.md
#   9. tmux send "clear" + kill-session 收尾
# 用法：
#   bash insights-share/validation/with_reproduce.sh
# ================================================================
set -u

REPO_ROOT="/Users/m1/projects/demo_insights_share"
DELIV="${REPO_ROOT}/insights-share/validation/reports/deliverables"
GITHUB_URL="https://github.com/liush2yuxjtu/demo_insights_share.git"
WORKSPACE_B="/tmp/demo_insights_B"
CLONE_DIR="${WORKSPACE_B}/isw-clone"
SKILL_DST="${HOME}/.claude/skills/insights-wiki"
SKILL_SERVER_DST="${HOME}/.claude/skills/insights-wiki-server"
SESSION="insights_with_repro"
RAW="${WORKSPACE_B}/B_with.raw"
LOG="${WORKSPACE_B}/B_with.log"
DAEMON_LOG="${WORKSPACE_B}/isd.log"
PROMPT_FILE="${WORKSPACE_B}/insights_with_prompt.txt"
WRAPPER="${WORKSPACE_B}/insights_with_wrapper.sh"
MD="${DELIV}/claude_export_WITH.md"
WAIT_SEC=240

# 核心 prompt：要求 Claude 先自检环境（pwd + skill 列表 + filetree）再答技术问题
# 单行化，避免 tmux send-keys 截断
PROMPT='请严格按顺序执行三步。第一步：运行 !pwd 打印当前工作目录。第二步：运行 !ls -la ~/.claude/skills/ 展示已安装的 skill 列表，并用 !head -40 ~/.claude/skills/insights-wiki/SKILL.md 读取 insights-wiki 的 SKILL.md 前 40 行。第三步：回答 — 我们的 checkout API 正在超时，postgres 在午餐高峰拒绝新连接，应该如何诊断与修复？请给出可执行的 SQL 与代码片段；如果你有 insights-wiki 注入的 LAN 实战卡片，请在回答里明确引用。'

mkdir -p "${DELIV}"
log() { printf '[%s] %s\n' "$(date +%H:%M:%S)" "$*"; }

log "=== WITH 轮开始（从零 setup）==="
pkill -f "insights_cli.py serve" 2>/dev/null || true
rm -rf "${WORKSPACE_B}"
mkdir -p "${WORKSPACE_B}" "${HOME}/.claude/skills"
cd "${WORKSPACE_B}"
log "Step 0: 工作目录已重置 → ${WORKSPACE_B}"

# ---------- Step 0: 清理 skill 环境 ----------
log "Step 0a: 清理 ~/.claude/skills/insights-wiki*（若存在）"
if [ -d "${SKILL_DST}" ]; then
  mv "${SKILL_DST}" "${SKILL_DST}.bak.$$"
  log "  已暂存 ${SKILL_DST} → .bak.$$"
fi
if [ -d "${SKILL_SERVER_DST}" ]; then
  mv "${SKILL_SERVER_DST}" "${SKILL_SERVER_DST}.bak.$$"
  log "  已暂存 ${SKILL_SERVER_DST} → .bak.$$"
fi

# ---------- Step 1: git clone from github ----------
log "Step 1: git clone --depth 1 ${GITHUB_URL} → ${CLONE_DIR}"
rm -rf "${CLONE_DIR}"
if ! git clone --depth 1 "${GITHUB_URL}" "${CLONE_DIR}" 2>&1 | tail -5; then
  log "[fatal] git clone 失败，退出"
  exit 2
fi
log "  clone 完成，HEAD=$(cd ${CLONE_DIR} && git rev-parse --short HEAD)"

# 断言 skill 在 cloned 目录里存在
CLONED_SKILL="${CLONE_DIR}/insights-share/demo_codes/.claude/skills/insights-wiki"
CLONED_SKILL_SERVER="${CLONE_DIR}/insights-share/demo_codes/.claude/skills/insights-wiki-server"
if [ ! -f "${CLONED_SKILL}/SKILL.md" ]; then
  log "[fatal] cloned 目录内缺失 insights-wiki/SKILL.md，github 仓库未推送 skill？"
  exit 3
fi
log "  cloned skill SKILL.md 存在 → $(wc -c < "${CLONED_SKILL}/SKILL.md" | tr -d ' ') 字节"

# ---------- Step 2: 安装 skill 到 ~/.claude/skills/ ----------
log "Step 2a: 安装 insights-wiki skill → ${SKILL_DST}"
mkdir -p "${SKILL_DST}"
cp -r "${CLONED_SKILL}/." "${SKILL_DST}/"
log "  拷贝完成 → $(ls -1 "${SKILL_DST}" | wc -l | tr -d ' ') 个文件"

if [ -f "${CLONED_SKILL_SERVER}/SKILL.md" ]; then
  log "Step 2b: 安装 insights-wiki-server skill → ${SKILL_SERVER_DST}"
  mkdir -p "${SKILL_SERVER_DST}"
  cp -r "${CLONED_SKILL_SERVER}/." "${SKILL_SERVER_DST}/"
fi

# ---------- Step 3: first-setup-guide ----------
log "Step 3: 打印 first-setup-guide"
cat <<EOF

============================================================
  insights-wiki First-Setup Guide
============================================================
  1. skill 已安装：
     - ${SKILL_DST}
     - ${SKILL_SERVER_DST} (管理员可选)
  2. 启动 LAN daemon（管理员一次性）：
     python ${CLONE_DIR}/insights-share/demo_codes/insights_cli.py serve \\
         --host 0.0.0.0 --port 7821 --store-mode tree
  3. 发布卡片（管理员）：
     curl -X POST http://<LAN_IP>:7821/insights \\
         -H 'Content-Type: application/json' -d @card.json
  4. 触发静默回灌（普通用户）：
     直接用 claude -p 提问或在 Claude Code 里写代码，
     Stop hook 会自动把 top hit 以 additionalContext 注入下一轮
  5. 查看命中缓存：
     ls ~/.cache/insights-wiki/
============================================================
EOF

# ---------- Step 4: 启动 daemon ----------
log "Step 4a: 在 ${CLONE_DIR}/insights-share/demo_codes 启动 insightsd"
(cd "${CLONE_DIR}/insights-share/demo_codes" && nohup python3 insights_cli.py serve --host 0.0.0.0 --port 7821 --store ./wiki.json > "${DAEMON_LOG}" 2>&1 &)
sleep 3
if ! curl -sf http://127.0.0.1:7821/insights >/dev/null; then
  log "[fatal] insightsd 健康检查失败，请查看 ${DAEMON_LOG}"
  exit 4
fi
log "  daemon 已启动 → ${DAEMON_LOG}"

# ---------- Step 5: 写 prompt 文件 + wrapper 脚本 ----------
log "Step 5a: 写 prompt 文件 ${PROMPT_FILE}"
printf '%s' "${PROMPT}" > "${PROMPT_FILE}"
log "  prompt $(wc -c < "${PROMPT_FILE}" | tr -d ' ') 字节"

log "Step 5b: 写 wrapper 脚本 ${WRAPPER}"
cat > "${WRAPPER}" <<WRAPPER_EOF
#!/usr/bin/env bash
cd "${WORKSPACE_B}"
claude -p "\$(cat ${PROMPT_FILE})" 2>&1 | tee "${RAW}"
echo __DONE__
WRAPPER_EOF
chmod +x "${WRAPPER}"

# ---------- Step 6: tmux 启动并执行 wrapper ----------
tmux kill-session -t "${SESSION}" 2>/dev/null || true
rm -f "${RAW}"
log "Step 6a: tmux new-session -d -s ${SESSION} -x 220 -y 60"
tmux new-session -d -s "${SESSION}" -x 220 -y 60

log "Step 6b: tmux send-keys bash ${WRAPPER}"
tmux send-keys -t "${SESSION}" "bash ${WRAPPER}" Enter

# ---------- Step 7: 轮询等待 ----------
log "Step 7: 轮询等待 __DONE__（最长 ${WAIT_SEC}s，含 hook 预热）"
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

# ---------- Step 8: 去 ANSI 落盘 md ----------
log "Step 8: 清洗 ANSI 写入 ${MD}"
if [ -s "${RAW}" ]; then
  sed -E 's/\x1b\[[0-9;]*[A-Za-z]//g' "${RAW}" | grep -v '^__DONE__$' > "${LOG}"
else
  printf '[会话超时] claude -p 在 %d 秒内未输出任何内容\n' "${WAIT_SEC}" > "${LOG}"
fi
{
  printf '# Claude Export — WITH 版（安装 insights-wiki skill）\n\n'
  printf '## 元信息\n\n'
  printf -- '- 时间：%s\n' "$(date '+%Y-%m-%d %H:%M:%S')"
  printf -- '- 模式：A/B 对照 · WITH 轮（从零 setup）\n'
  printf -- '- tmux 会话：%s\n' "${SESSION}"
  printf -- '- 工作目录：%s\n' "${WORKSPACE_B}"
  printf -- '- 日志：%s\n' "${LOG}"
  printf -- '- daemon 日志：%s\n' "${DAEMON_LOG}"
  printf -- '- skill 来源：git clone %s (HEAD=%s)\n' "${GITHUB_URL}" "$(cd ${CLONE_DIR} 2>/dev/null && git rev-parse --short HEAD || echo unknown)"
  printf -- '- skill 安装路径：%s\n' "${SKILL_DST}"
  printf -- '- prompt：\n\n'
  printf '```\n%s\n```\n\n' "${PROMPT}"
  printf '## Claude 原始输出\n\n'
  printf '```\n'
  cat "${LOG}"
  printf '```\n'
} > "${MD}"
log "  已写入 ${MD}（$(wc -c < "${MD}" | tr -d ' ') 字节）"
log "  B 日志保存在 ${LOG}（$(wc -c < "${LOG}" | tr -d ' ') 字节）"

# ---------- Step 9: tmux 清屏并关闭 ----------
log "Step 9: tmux send clear + kill-session"
tmux send-keys -t "${SESSION}" "clear" Enter 2>/dev/null || true
sleep 1
tmux kill-session -t "${SESSION}" 2>/dev/null || true

log "=== WITH 轮结束 ==="
ls -la "${MD}" "${LOG}" "${CLONE_DIR}"
