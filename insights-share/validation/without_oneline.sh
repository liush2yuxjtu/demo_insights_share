#!/usr/bin/env bash
# ================================================================
# without_oneline.sh — WITHOUT 版 一行复制粘贴命令
# ----------------------------------------------------------------
# 用途：快速验证 "无 skill" 环境下 claude -p 的回答
# 设计：所有命令用 && 串成一条可直接复制到终端的命令
# ================================================================
#
# === 一行可复制命令（WITHOUT）===
# 下方是单行命令，直接复制中间这一整行到终端即可运行：
#
# ----------------------------------------------------------------
# pkill -f "insights_cli.py serve" 2>/dev/null; rm -rf ~/.claude/skills/insights-wiki ~/.claude/skills/insights-wiki-server 2>/dev/null; rm -rf /tmp/demo_insights_A && mkdir -p /tmp/demo_insights_A && cd /tmp/demo_insights_A && claude -p "我们的 checkout API 正在超时，postgres 在午餐高峰拒绝新连接，应该如何诊断与修复？请给出可执行的 SQL 与代码片段。" 2>&1 | sed -E 's/\x1b\[[0-9;]*[A-Za-z]//g' | tee /tmp/demo_insights_A/A_without.log
# ----------------------------------------------------------------
#
# 说明：
#   1. 先停 daemon，再删 ~/.claude/skills/insights-wiki* 保证环境干净
#   2. 创建 /tmp/demo_insights_A 并切进去，避免污染当前 cwd
#   3. 用 sed 去 ANSI 转义 → tee 落盘到 /tmp/demo_insights_A/A_without.log
#
# 如果你直接执行本脚本，它会帮你跑上面那一行：
set -u
WORKSPACE_A="/tmp/demo_insights_A"
OUT_FILE="${WORKSPACE_A}/A_without.log"

pkill -f "insights_cli.py serve" 2>/dev/null || true
rm -rf "${HOME}/.claude/skills/insights-wiki" "${HOME}/.claude/skills/insights-wiki-server" 2>/dev/null || true
rm -rf "${WORKSPACE_A}"
mkdir -p "${WORKSPACE_A}"
cd "${WORKSPACE_A}"

printf '[%s] WITHOUT one-line 开始\n' "$(date +%H:%M:%S)"
claude -p "我们的 checkout API 正在超时，postgres 在午餐高峰拒绝新连接，应该如何诊断与修复？请给出可执行的 SQL 与代码片段。" 2>&1 \
  | sed -E 's/\x1b\[[0-9;]*[A-Za-z]//g' \
  | tee "${OUT_FILE}"
printf '[%s] WITHOUT one-line 结束 → %s\n' "$(date +%H:%M:%S)" "${OUT_FILE}"
