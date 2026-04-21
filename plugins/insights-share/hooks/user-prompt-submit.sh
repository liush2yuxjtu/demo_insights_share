#!/usr/bin/env bash
# insights-share plugin :: UserPromptSubmit hook
#
# 迁移自 insights-share/demo_codes/hooks/insights_prefetch.py。
# 保留 today_count 口径：一次 UserPromptSubmit → 触发一次 prefetch。
# 设计依据：proposal/proposal_plugin_design.md §"Plugin 槽位映射"
# 和 §"风险与约束" 第 1 行（迁移前后 today_count 口径不变）。
#
# 定位策略：
#   1. 优先用 plugin 内置 bootstrap 路径（未来 M2+ 会自带 venv）
#   2. M1 阶段 fallback 到仓库既有 demo_codes venv + 既有 prefetch 脚本
#      原因：避免 M1 同时动代码 + 搬运路径，只做"包装"不做"重写"
#
# 失败策略：静默退出 0（不阻塞主对话）。对齐 skill SKILL.md 中 SILENT 约定。

set -u

# 允许 plugin install 时注入绝对仓库根；fallback 用 hook 脚本自身相对路径
REPO_ROOT="${INSIGHTS_SHARE_REPO_ROOT:-}"
if [ -z "$REPO_ROOT" ]; then
  HOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  # hooks/user-prompt-submit.sh → plugins/insights-share/ → plugins/ → repo root
  REPO_ROOT="$(cd "$HOOK_DIR/../../.." && pwd)"
fi

DEMO_CODES="$REPO_ROOT/insights-share/demo_codes"
VENV_PY="$DEMO_CODES/.venv/bin/python"
PREFETCH="$DEMO_CODES/hooks/insights_prefetch.py"

# 缺任一组件则静默退出：M1 迁移阶段兼容只装 plugin 不装 venv 的场景
[ -x "$VENV_PY" ] || exit 0
[ -f "$PREFETCH" ] || exit 0

# 透传 stdin（Claude Code 把 prompt 作为 JSON 喂给 hook）
exec "$VENV_PY" "$PREFETCH" 2>/dev/null
