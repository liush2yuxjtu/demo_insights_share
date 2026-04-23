#!/usr/bin/env bash
# insights-share plugin :: UserPromptSubmit hook
#
# 迁移自 insights-share/demo_codes/hooks/insights_prefetch.py。
# 保留 today_count 口径：一次 UserPromptSubmit → 触发一次 prefetch。
# 设计依据：proposal/proposal_plugin_design.md §"Plugin 槽位映射"
# 和 §"风险与约束" 第 1 行（迁移前后 today_count 口径不变）。
#
# 失败策略：静默退出 0（不阻塞主对话）。对齐 skill SKILL.md 中 SILENT 约定。

set -u

HOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(cd "$HOOK_DIR/.." && pwd)"
PREFETCH="$PLUGIN_ROOT/scripts/insights_prefetch.py"
PYTHON_BIN="$(command -v python3 || true)"

[ -n "$PYTHON_BIN" ] || exit 0
[ -f "$PREFETCH" ] || exit 0

# 透传 stdin（Claude Code 把 prompt 作为 JSON 喂给 hook）
exec "$PYTHON_BIN" "$PREFETCH" 2>/dev/null
