#!/usr/bin/env bash
# ================================================================
# validate_commands.sh — 两行可复制到 sandbox 的 A/B 验证命令
# 使用：挑下方一行命令，直接粘贴到一个干净的终端（sandbox）执行。
# 执行完你会得到：
#   /tmp/A_without.log  或  /tmp/B_with.log
# 对比这两个 log 就能看到 insights-wiki 是否生效。
# ================================================================

# ----------------------------------------------------------------
# 命令 1 / 2  ·  A / WITHOUT  ·  不装 skill · 看 Claude 的通用答案
# ----------------------------------------------------------------
# 复制下面这一整行到 sandbox 终端：

pkill -f "insights_cli.py serve" 2>/dev/null; rm -rf ~/.claude/skills/insights-wiki ~/.claude/skills/insights-wiki-server && claude -p "我们的 checkout API 正在超时，postgres 在午餐高峰拒绝新连接，应该如何诊断与修复？请给出可执行的 SQL 与代码片段。" 2>&1 | sed -E 's/\x1b\[[0-9;]*[A-Za-z]//g' > /tmp/A_without.log && echo "✅ A/WITHOUT → /tmp/A_without.log ($(wc -c < /tmp/A_without.log) bytes)"

# ----------------------------------------------------------------
# 命令 2 / 2  ·  B / WITH  ·  从 github clone skill + 启 daemon + 问同一个问题
# ----------------------------------------------------------------
# 复制下面这一整行到 sandbox 终端：

rm -rf ~/.claude/skills/insights-wiki ~/.claude/skills/insights-wiki-server /tmp/isw-clone && git clone --depth 1 https://github.com/liush2yuxjtu/demo_insights_share.git /tmp/isw-clone && cp -r /tmp/isw-clone/insights-share/demo_codes/.claude/skills/insights-wiki ~/.claude/skills/ && cp -r /tmp/isw-clone/insights-share/demo_codes/.claude/skills/insights-wiki-server ~/.claude/skills/ && (cd /tmp/isw-clone/insights-share/demo_codes && nohup python3 insights_cli.py serve --host 0.0.0.0 --port 7821 --store ./wiki.json > /tmp/isd.log 2>&1 &) && sleep 3 && curl -sf http://127.0.0.1:7821/insights >/dev/null && echo "daemon up, cards=$(curl -s http://127.0.0.1:7821/insights | python3 -c 'import sys,json;print(len(json.load(sys.stdin).get(\"cards\",[])))')" && claude -p "我们的 checkout API 正在超时，postgres 在午餐高峰拒绝新连接，应该如何诊断与修复？请给出可执行的 SQL 与代码片段；若有 insights-wiki 注入的 LAN 实战卡片请在回答里明确引用。" 2>&1 | sed -E 's/\x1b\[[0-9;]*[A-Za-z]//g' > /tmp/B_with.log && echo "✅ B/WITH → /tmp/B_with.log ($(wc -c < /tmp/B_with.log) bytes)"

# ----------------------------------------------------------------
# 验证 A vs B 差异（可选）：
# ----------------------------------------------------------------
# grep -c "alice-pgpool-2026-04-10" /tmp/A_without.log   # 应 = 0
# grep -c "alice-pgpool-2026-04-10" /tmp/B_with.log     # 应 ≥ 1
