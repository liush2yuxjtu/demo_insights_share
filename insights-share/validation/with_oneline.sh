#!/usr/bin/env bash
# ================================================================
# with_oneline.sh — WITH 版 一行复制粘贴命令
# ----------------------------------------------------------------
# 用途：快速验证 "装了 insights-wiki skill" 环境下 claude -p 的回答
# 特点：skill 从 github 远程 clone 获取，不从本地 filetree 复制
# ================================================================
#
# === 一行可复制命令（WITH）===
# 下方是单行命令，直接复制中间这一整行到终端即可运行：
#
# ----------------------------------------------------------------
# rm -rf ~/.claude/skills/insights-wiki ~/.claude/skills/insights-wiki-server 2>/dev/null; pkill -f "insights_cli.py serve" 2>/dev/null; rm -rf /tmp/demo_insights_B && mkdir -p /tmp/demo_insights_B && cd /tmp/demo_insights_B && git clone --depth 1 https://github.com/liush2yuxjtu/demo_insights_share.git isw-clone && cp -r /tmp/demo_insights_B/isw-clone/insights-share/demo_codes/.claude/skills/insights-wiki ~/.claude/skills/ && cp -r /tmp/demo_insights_B/isw-clone/insights-share/demo_codes/.claude/skills/insights-wiki-server ~/.claude/skills/ && (cd /tmp/demo_insights_B/isw-clone/insights-share/demo_codes && nohup python3 insights_cli.py serve --host 0.0.0.0 --port 7821 --store ./wiki.json > /tmp/demo_insights_B/isd.log 2>&1 &) && sleep 3 && curl -sf http://127.0.0.1:7821/insights >/dev/null && claude -p "我们的 checkout API 正在超时，postgres 在午餐高峰拒绝新连接，应该如何诊断与修复？请给出可执行的 SQL 与代码片段；若有 insights-wiki 注入的 LAN 实战卡片请在回答里明确引用。" 2>&1 | sed -E 's/\x1b\[[0-9;]*[A-Za-z]//g' | tee /tmp/demo_insights_B/B_with.log
# ----------------------------------------------------------------
#
# 说明：
#   1. 删除旧 skill、停掉旧 daemon，并创建 /tmp/demo_insights_B 隔离工作区
#   2. git clone --depth 1 从 github 拉取仓库到 /tmp/demo_insights_B/isw-clone
#   3. 把 insights-wiki 和 insights-wiki-server 两个 skill 拷到 ~/.claude/skills/
#   4. 后台启动 daemon，日志写到 /tmp/demo_insights_B/isd.log
#   5. 运行 claude -p 发问（skill 环境 + hook 自动注入 LAN 实战卡片）
#   6. 去 ANSI → tee 落盘到 /tmp/demo_insights_B/B_with.log
#
# 如果你直接执行本脚本，它会帮你跑上面那一行：
set -u
WORKSPACE_B="/tmp/demo_insights_B"
OUT_FILE="${WORKSPACE_B}/B_with.log"
CLONE="${WORKSPACE_B}/isw-clone"
DAEMON_LOG="${WORKSPACE_B}/isd.log"
GITHUB_URL="https://github.com/liush2yuxjtu/demo_insights_share.git"

rm -rf "${HOME}/.claude/skills/insights-wiki" "${HOME}/.claude/skills/insights-wiki-server" 2>/dev/null || true
pkill -f "insights_cli.py serve" 2>/dev/null || true
rm -rf "${WORKSPACE_B}"
mkdir -p "${WORKSPACE_B}" "${HOME}/.claude/skills"
cd "${WORKSPACE_B}"

printf '[%s] WITH one-line 开始：git clone %s\n' "$(date +%H:%M:%S)" "${GITHUB_URL}"
git clone --depth 1 "${GITHUB_URL}" "${CLONE}" 2>&1 | tail -3

cp -r "${CLONE}/insights-share/demo_codes/.claude/skills/insights-wiki" "${HOME}/.claude/skills/"
cp -r "${CLONE}/insights-share/demo_codes/.claude/skills/insights-wiki-server" "${HOME}/.claude/skills/"
printf '[%s] skill 已从 github clone 并安装到 ~/.claude/skills/\n' "$(date +%H:%M:%S)"

(cd "${CLONE}/insights-share/demo_codes" && nohup python3 insights_cli.py serve --host 0.0.0.0 --port 7821 --store ./wiki.json > "${DAEMON_LOG}" 2>&1 &)
sleep 3
curl -sf http://127.0.0.1:7821/insights >/dev/null
printf '[%s] daemon 已启动 → %s\n' "$(date +%H:%M:%S)" "${DAEMON_LOG}"

claude -p "我们的 checkout API 正在超时，postgres 在午餐高峰拒绝新连接，应该如何诊断与修复？请给出可执行的 SQL 与代码片段；若有 insights-wiki 注入的 LAN 实战卡片请在回答里明确引用。" 2>&1 \
  | sed -E 's/\x1b\[[0-9;]*[A-Za-z]//g' \
  | tee "${OUT_FILE}"

printf '[%s] WITH one-line 结束 → %s\n' "$(date +%H:%M:%S)" "${OUT_FILE}"
