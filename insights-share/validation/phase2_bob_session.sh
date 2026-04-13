#!/usr/bin/env bash
# Phase 2 演示脚本：模拟 Bob 在 claude code 里只是"打字思考"，没有主动求助。
# 退出后 .claude/settings.json 注册的 Stop hook 自动拉起 insights_stop_hook.py，
# 静默搜 wiki，把命中的 insight 写入 /tmp/insights_review.md。
#
# 严禁 fallback：search_agent 必须真实调用 MiniMax；任何异常都是 phase fail。

set -e
DEMO_CODES="/Users/m1/projects/demo_insights_share/insights-share/demo_codes"
cd "$DEMO_CODES"

export INSIGHTS_TRIGGER_MODE="${INSIGHTS_TRIGGER_MODE:-SILENT_AND_JUST_RUN}"
# 走本地 daemon，避免 socks5 代理
export NO_PROXY="127.0.0.1,localhost,${NO_PROXY:-}"

echo "[bob_session] mode=$INSIGHTS_TRIGGER_MODE"
echo "[bob_session] cwd=$DEMO_CODES"
echo "[bob_session] starting claude (one-shot, no proactive help request)"

# Bob 的"输入"：他不是在求助，只是把脑子里的事情打出来。
PROMPT="I'm debugging PostgreSQL connection timeouts on checkout API during the lunch spike. Postgres is rejecting new connections. Just thinking out loud, no fix needed from you."

# claude -p 是一次性 print 模式：处理完 prompt 即退出，触发 Stop hook。
# --permission-mode=dontAsk 避免 Bob 看到任何确认提示，符合 SILENT 语义。
claude -p "$PROMPT" --permission-mode=dontAsk 2>&1 || true

echo
echo "[bob_session] claude exited; reading /tmp/insights_review.md tail"
if [[ -f /tmp/insights_review.md ]]; then
    tail -30 /tmp/insights_review.md
else
    echo "[bob_session] WARN /tmp/insights_review.md missing; hook may not have fired"
fi
echo "[bob_session] grep markers"
grep -E '\[SILENT_AND_JUST_RUN\]|postgres_pool' /tmp/insights_review.md || echo "[bob_session] WARN no markers"
echo "[bob_session] done"
