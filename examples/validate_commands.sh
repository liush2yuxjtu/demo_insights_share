#!/usr/bin/env bash
# ================================================================
# validate_commands.sh — 三步可复制到 sandbox 的 A/B 验证命令
# 使用：按顺序复制命令 1、2a、2b，最后用命令 3 检查 A/B 差异。
# 执行完你会得到：
#   /tmp/demo_insights_A/A_without.log
#   /tmp/demo_insights_B/B_with.log
# ================================================================

# ----------------------------------------------------------------
# 命令 1 · A / WITHOUT · 不装 skill · 看 Claude 的通用答案
# ----------------------------------------------------------------
pkill -f "insights_cli.py serve" 2>/dev/null; \
rm -rf ~/.claude/skills/insights-wiki ~/.claude/skills/insights-wiki-server && \
mkdir -p /tmp/demo_insights_A && cd /tmp/demo_insights_A && \
claude -p "我们的 checkout API 正在超时，postgres 在午餐高峰拒绝新连接，应该如何诊断与修复？请给出可执行的 SQL 与代码片段。" 2>&1 | sed -E 's/\x1b\[[0-9;]*[A-Za-z]//g' > /tmp/demo_insights_A/A_without.log && \
echo "✅ A/WITHOUT → /tmp/demo_insights_A/A_without.log ($(wc -c < /tmp/demo_insights_A/A_without.log) bytes)"

# ----------------------------------------------------------------
# 命令 2a · B / WITH · clone 一个干净的工作区
# ----------------------------------------------------------------
mkdir -p /tmp/demo_insights_B && cd /tmp/demo_insights_B && \
rm -rf isw-clone && \
git clone --depth 1 https://github.com/liush2yuxjtu/demo_insights_share.git isw-clone \
  || { echo "❌ git clone 失败，请检查 github 配置（ssh key / https token）后重试"; exit 1; } && \
echo "✅ Step 2a: clone 完成 → /tmp/demo_insights_B/isw-clone"

# ----------------------------------------------------------------
# 命令 2b · B / WITH · 安装 skill + 启 daemon + 问同一个问题
# ----------------------------------------------------------------
cd /tmp/demo_insights_B && \
rm -rf ~/.claude/skills.disabled/insights-wiki.active ~/.claude/skills.disabled/insights-wiki-server.active 2>/dev/null; \
cp -r isw-clone/insights-share/demo_codes/.claude/skills/insights-wiki ~/.claude/skills/ && \
cp -r isw-clone/insights-share/demo_codes/.claude/skills/insights-wiki-server ~/.claude/skills/ && \
(cd isw-clone/insights-share/demo_codes && nohup python3 insights_cli.py serve --host 0.0.0.0 --port 7821 --store ./wiki.json > /tmp/demo_insights_B/isd.log 2>&1 &) && \
sleep 3 && curl -sf http://127.0.0.1:7821/insights >/dev/null && \
claude -p "我们的 checkout API 正在超时，postgres 在午餐高峰拒绝新连接，应该如何诊断与修复？若 insights-wiki 注入了 LAN 实战卡片请在回答里明确引用。" 2>&1 | sed -E 's/\x1b\[[0-9;]*[A-Za-z]//g' > /tmp/demo_insights_B/B_with.log && \
echo "✅ Step 2b: B_with.log $(wc -c < /tmp/demo_insights_B/B_with.log) bytes"

# ----------------------------------------------------------------
# 命令 3 · 验证 A vs B 差异（A 应 = 0，B 应 ≥ 1）
# ----------------------------------------------------------------
grep -c alice-pgpool-2026-04-10 /tmp/demo_insights_A/A_without.log /tmp/demo_insights_B/B_with.log
