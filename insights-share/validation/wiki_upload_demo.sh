#!/usr/bin/env bash
# wiki_upload_demo.sh — 演示普通开发用 insights-wiki skill 上传一条 insight 卡
# 单轮 tmux + claude -p，200s 轮询 __DONE__，去 ANSI 落盘
# 注：claude -p 启动时 prefetch hook 会跑 ~110s，所以 WAIT_SEC 必须 ≥180
set -u

REPO_ROOT="/Users/m1/projects/demo_insights_share"
DELIV="${REPO_ROOT}/insights-share/validation/reports/deliverables"
SKILL_SRC="${REPO_ROOT}/insights-share/demo_codes/.claude/skills/insights-wiki"
SKILL_DST="${HOME}/.claude/skills/insights-wiki"
PROMPT='帮我把这条 postgres pgbouncer 连接池耗尽的 insight 上传到 LAN wiki'
WAIT_SEC=200

mkdir -p "${DELIV}"
log() { printf '[%s] %s\n' "$(date +%H:%M:%S)" "$*"; }

# 预置：把 insights-wiki skill 拷到 ~/.claude/skills/
if [ ! -f "${SKILL_SRC}/SKILL.md" ]; then
  log "[fatal] ${SKILL_SRC}/SKILL.md 不存在，Track C-1 未完成"
  exit 2
fi
log "拷贝 skill 到 ${SKILL_DST}"
mkdir -p "${SKILL_DST}"
cp -r "${SKILL_SRC}/." "${SKILL_DST}/"

session="insights_wiki_upload"
raw="/tmp/insights_wiki_upload.out"
out="${DELIV}/wiki_upload.txt"

log "=== wiki_upload 演示开始 ==="
tmux kill-session -t "${session}" 2>/dev/null || true
rm -f "${raw}"

log "tmux 启动 session=${session}"
tmux new-session -d -s "${session}" -x 200 -y 50
tmux send-keys -t "${session}" "claude -p \"${PROMPT}\" 2>&1 | tee ${raw}; echo __DONE__" Enter

log "等待 ${WAIT_SEC} 秒让 claude -p 出结果"
elapsed=0
while [ "${elapsed}" -lt "${WAIT_SEC}" ]; do
  sleep 5
  elapsed=$((elapsed + 5))
  if [ -f "${raw}" ] && grep -q "__DONE__" "${raw}" 2>/dev/null; then
    log "检测到 __DONE__，提前结束 (elapsed=${elapsed}s)"
    break
  fi
  log "  ...elapsed=${elapsed}s, raw_size=$(stat -f%z ${raw} 2>/dev/null || echo 0)"
done

if [ ! -s "${raw}" ]; then
  log "[warn] ${raw} 为空，写占位"
  printf '[会话超时] claude -p 在 %d 秒内未输出任何内容\n' "${WAIT_SEC}" > "${out}"
else
  sed -E 's/\x1b\[[0-9;]*[A-Za-z]//g' "${raw}" | grep -v '^__DONE__$' > "${out}"
  log "已写入 ${out} ($(wc -c < ${out}) 字节)"
fi

log "tmux kill-session ${session}"
tmux kill-session -t "${session}" 2>/dev/null || true
log "=== wiki_upload 演示结束 ==="
ls -la "${out}"
