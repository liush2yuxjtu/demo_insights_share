#!/usr/bin/env bash
# guide_loop.sh — 左 pane 讲解引擎（沙箱感知版）
#
# 用法：
#   bash guide_loop.sh <SANDBOX_DIR> <GUIDE_LOG> <SKILL_NAME> <SANDBOX_HOME>
#
# 职责：
#   1. 按阶段往 GUIDE_LOG 写中文讲解卡片（左 pane 通过 tail -f 看到）
#   2. 监听沙箱 HOME 下的信号文件决定何时推进下一阶段
#   3. 信号缺失时最多等 TIMEOUT，再给出兜底讲解
#
# 重要：所有路径检测都基于 SANDBOX_HOME（沙箱 HOME），
#      不碰用户真实 ~/.claude/，保证沙箱完整性。

set -eu

SANDBOX="${1:?需要 SANDBOX 路径}"
LOG="${2:?需要 guide.log 路径}"
SKILL_NAME="${3:-insights-share}"
SANDBOX_HOME="${4:?需要 SANDBOX_HOME 路径（用于沙箱隔离检测）}"

PLUGIN_CACHE_ROOT="$SANDBOX_HOME/.claude/plugins/cache"
INSTALLED_PLUGINS="$SANDBOX_HOME/.claude/plugins/installed_plugins.json"
CACHE_DIR="$SANDBOX_HOME/.cache/insights-share"

# 每阶段最多等多少秒（避免某个信号永远不来时左边卡死）
STAGE_TIMEOUT=120

# ── 输出工具 ──────────────────────────────────────────
card() {
  local title="$1"; shift
  {
    printf '\n'
    printf '┌─────────────────────────────────────────────────────────────┐\n'
    printf '│ %s\n' "$title"
    printf '├─────────────────────────────────────────────────────────────┤\n'
    for line in "$@"; do
      printf '│ %s\n' "$line"
    done
    printf '└─────────────────────────────────────────────────────────────┘\n'
  } >> "$LOG"
}

ok()   { printf '  ✅ %s\n' "$1" >> "$LOG"; }
wait_msg() { printf '  ⏳ %s\n' "$1" >> "$LOG"; }
warn_msg() { printf '  ⚠️  %s\n' "$1" >> "$LOG"; }

# 等信号文件出现，带 timeout
wait_for_file() {
  local path="$1"
  local timeout="${2:-$STAGE_TIMEOUT}"
  local waited=0
  while [ ! -e "$path" ]; do
    sleep 2
    waited=$((waited + 2))
    if [ "$waited" -ge "$timeout" ]; then
      return 1
    fi
  done
  return 0
}

find_plugin_skill() {
  find "$PLUGIN_CACHE_ROOT" -path "*/skills/$SKILL_NAME/SKILL.md" -print -quit 2>/dev/null || true
}

wait_for_plugin_skill() {
  local timeout="${1:-$STAGE_TIMEOUT}"
  local waited=0
  while [ -z "$(find_plugin_skill)" ]; do
    sleep 2
    waited=$((waited + 2))
    if [ "$waited" -ge "$timeout" ]; then
      return 1
    fi
  done
  return 0
}

# ── Stage 0: 欢迎 ─────────────────────────────────────
sleep 1
card "📖 欢迎进入 insights-share demo（左边讲解 / 右边 Claude）" \
  "这个 demo 会带你亲眼看完一条完整链路：" \
  "  1. 确认 insights-share plugin 已经装好" \
  "  2. 在右边 Claude 会话提一个真实 postgres 超时问题" \
  "  3. 观察 skill 静默触发，拉回 LAN wiki 卡片" \
  "  4. 对比有无 skill 时的答案差异" \
  "  5. 按 F12 整体退出" \
  "" \
  "操作规则：" \
  "  · 读完左边卡片，直接看右边 Claude 输入区" \
  "  · 鼠标点哪个 pane 就进哪个，不用记 tmux 快捷键" \
  "  · 遇到任何问题按 F12 可以一键退出并清理"

sleep 3

# ── Stage 1: 确认 plugin 已装 ─────────────────────────
card "📖 第 1 步：确认 insights-share plugin 已经装好" \
  "plugin 会把 skill、hook、statusline、slash 命令一起装进沙箱。" \
  "我们刚刚已经用 claude plugin install 写入：" \
  "  $INSTALLED_PLUGINS" \
  "并把 plugin 内容缓存到：" \
  "  $PLUGIN_CACHE_ROOT" \
  "" \
  "现在在右边 Claude 会话里输入：" \
  "" \
  "    请列出我本地的 plugin 和 skill" \
  "" \
  "输出里出现 insights-share 就说明装好了。"

if wait_for_plugin_skill 30; then
  plugin_skill="$(find_plugin_skill)"
  ok "检测到 $plugin_skill — plugin 内 skill 已装好"
else
  warn_msg "等了 30 秒还没看到 plugin cache 内的 SKILL.md，可能 plugin install 失败了。但不阻塞，继续往下。"
fi

sleep 3

# ── Stage 2: 发起首次提问 ─────────────────────────────
card "📖 第 2 步：在右边向 Claude 提一个真实 postgres 问题" \
  "请把下面这段复制到右边 Claude 输入框（整段一次性贴进去）：" \
  "" \
  "    我们的 checkout API 正在超时，postgres 在午餐高峰拒绝" \
  "    新连接，应该如何诊断与修复？请给出可执行的 SQL 与代码片段。" \
  "" \
  "如果 skill 生效，Claude 会静默后台调用 insights-share 去查 LAN wiki，" \
  "拉回别人之前遇到同类问题时沉淀下来的卡片。" \
  "整个过程不会弹任何确认窗口。"

wait_msg "正在等待 Claude 触发 skill 并写入本地缓存…"

if wait_for_file "$CACHE_DIR/manifest.json" "$STAGE_TIMEOUT"; then
  ok "检测到 $CACHE_DIR/manifest.json — skill 已触发并写缓存"
else
  warn_msg "${STAGE_TIMEOUT} 秒内没有看到缓存生成，继续讲解但请检查右边 Claude 输出。"
fi

sleep 3

# ── Stage 3: 展示 skill 拉到的卡片 ────────────────────
card_count=0
if [ -d "$CACHE_DIR" ]; then
  card_count="$(find "$CACHE_DIR" -maxdepth 1 -type f 2>/dev/null | wc -l | tr -d ' ')"
fi

card "📖 第 3 步：看看 skill 拉到了什么" \
  "skill 已经把相关卡片写到本地缓存：" \
  "  $CACHE_DIR" \
  "  （共 $card_count 个文件）" \
  "" \
  "这些卡片是团队其他人遇到同类问题时沉淀的。" \
  "Claude 会把卡片内容融合到回答里，你在右边应该能看到：" \
  "  · 具体的 SQL 诊断语句（比如查 pg_stat_activity）" \
  "  · postgres 连接池 / pgbouncer 配置建议" \
  "  · 引用的 LAN 卡片 ID（比如 alice-pgpool-2026-04-10）"

sleep 15

# ── Stage 4: 对比有无 skill 的差异 ─────────────────────
card "📖 第 4 步：对比有无 skill 时的答案差异" \
  "如果你想直观对比：没装 skill 时 Claude 会怎么答？" \
  "仓库里有一份录制好的 A/B 对照文件，可以在右边直接查看：" \
  "" \
  "    !head -80 examples/A_without.human.md   ← 没装 skill" \
  "    !head -80 examples/B_with.human.md      ← 装了 skill" \
  "" \
  "重点看两份回答里：" \
  "  · 是否引用了 alice-pgpool-2026-04-10 这类 LAN 卡片 ID" \
  "  · 给出的 SQL 是否有针对本团队 pgbouncer 配置的调整" \
  "  · 第一次回答时间，有 skill 的版本通常更直接"

sleep 20

# ── Stage 5: 结束 ─────────────────────────────────────
card "🎉 全部步骤完成" \
  "你已经看完一条真实闭环：" \
  "  skill 安装 → 静默触发 → 卡片拉取 → 答案融合 → A/B 对比" \
  "" \
  "接下来：" \
  "  · 想换个问题再玩：在右边继续输入新问题即可" \
  "  · 想看本次完整日志：$SANDBOX/guide.log" \
  "  · 想退出整个 demo：按 F12 一键退出并自动清理沙箱"

# Stage 5 是终态，保持 loop 让 tail -f 不退出
while true; do
  sleep 60
done
