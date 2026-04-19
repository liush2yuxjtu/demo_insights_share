#!/usr/bin/env bash
# start.demo.sh — tmux noob 友好的 insights-share demo 入口（真沙箱版）
#
# 沙箱设计（绝不污染真实 ~/.claude/）：
#   /tmp/demo-sandbox-<ts>.XXXX/
#     home/
#       .claude/
#         skills/insights-wiki/        ← cp 进来（完全独立副本）
#         .credentials.json → symlink 到真实 auth（只为能登录）
#         settings.json     → symlink 到真实 settings（只为继承偏好）
#       .cache/                        ← insights-wiki skill 写缓存的地方
#     guide.log                        ← 左 pane tail -f
#     .env                             ← 右 pane source 的环境文件
#
# 启动 claude 时右 pane export HOME=$SANDBOX_HOME，
# 所以 claude 看到的 ~/.claude/ 就是沙箱目录，skill 和 cache 全部隔离。
# 退出时一口气 rm -rf 沙箱，真实 HOME 零污染。

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
TS="$(date +%Y%m%d-%H%M%S)"
SANDBOX="$(mktemp -d "/tmp/demo-sandbox-${TS}.XXXXXX")"
SANDBOX_HOME="$SANDBOX/home"
SANDBOX_CLAUDE="$SANDBOX_HOME/.claude"
SANDBOX_WORKDIR="$SANDBOX/workdir"   # claude 的 cwd — 只有项目级 skill，不放别的
GUIDE_LOG="$SANDBOX/guide.log"
ENV_FILE="$SANDBOX/.env"
SKILL_NAME="insights-wiki"
SKILL_SRC="$REPO_ROOT/insights-share/demo_codes/.claude/skills/$SKILL_NAME"
DEMO_CODES="$REPO_ROOT/insights-share/demo_codes"
DEMO_SETTINGS="$DEMO_CODES/.claude/settings.json"   # 注册 insights-wiki hook
DEMO_VENV_PY="$DEMO_CODES/.venv/bin/python"
DAEMON_PORT="7821"
DAEMON_LOG="$SANDBOX/insightsd.log"
DAEMON_PID_FILE="$SANDBOX/insightsd.pid"
TMUX_CONF="$REPO_ROOT/insights-share/validation/tmux.noob.conf"
GUIDE_SCRIPT="$REPO_ROOT/insights-share/validation/guide_loop.sh"

# ── 漂亮的进度条输出 ──────────────────────────────────
step() { printf '\033[32m🟢 [%s/7]\033[0m %s\n' "$1" "$2"; }
die()  { printf '\033[31m[错误]\033[0m %s\n' "$1" >&2; exit 1; }
note() { printf '\033[36m[提示]\033[0m %s\n' "$1"; }

# ── 前置检查 ───────────────────────────────────────────
[ -d "$SKILL_SRC" ]     || die "缺失 skill 源目录：$SKILL_SRC"
[ -f "$DEMO_SETTINGS" ] || die "缺失 hook 配置：$DEMO_SETTINGS"
[ -x "$DEMO_VENV_PY" ]  || die "缺失 demo venv：$DEMO_VENV_PY（请先 cd $DEMO_CODES && python -m venv .venv && .venv/bin/pip install -r requirements.txt）"
[ -f "$TMUX_CONF" ]     || die "缺失 tmux 配置：$TMUX_CONF"
[ -f "$GUIDE_SCRIPT" ]  || die "缺失 guide 脚本：$GUIDE_SCRIPT"
command -v tmux   >/dev/null 2>&1 || die "请先安装 tmux：brew install tmux"
command -v claude >/dev/null 2>&1 || die "请先安装 claude CLI"

# ── Stage 1: 准备沙箱目录 ─────────────────────────────
# 双层 skill 入口（user-level + project-level）保证 claude 无论读 HOME 还是 cwd 都能拿到 skill
mkdir -p "$SANDBOX_CLAUDE/skills" "$SANDBOX_HOME/.cache" "$SANDBOX_WORKDIR/.claude/skills"
: > "$GUIDE_LOG"
step 1 "创建沙箱 $SANDBOX ........ done"

# ── 决定认证模式：minimax / subscription / none ────────
# 优先级：
#   1. CLI 已 export 的 MINIMAX_TOKEN  > .env > ~/.claude/.credentials.json
# 规则：
#   - 任何 placeholder (sk-cp-PASTE_.../sk-cp-YOUR_.../空) 一律视为未设置
#   - 没 token 但有订阅登录 → 走订阅；两者都无 → die 并给出指引
REPO_ENV="$REPO_ROOT/.env"
if [ -z "${MINIMAX_TOKEN:-}" ] && [ -f "$REPO_ENV" ]; then
  # shellcheck disable=SC1090
  set -a; source "$REPO_ENV"; set +a
fi
TOKEN="${MINIMAX_TOKEN:-}"
case "$TOKEN" in
  ""|sk-cp-PASTE*|sk-cp-YOUR_*|PASTE*)
    TOKEN=""
    ;;
esac

AUTH_MODE="none"
if [ -n "$TOKEN" ]; then
  AUTH_MODE="minimax"
elif [ -f "$HOME/.claude/.credentials.json" ]; then
  AUTH_MODE="subscription"
else
  die "未找到可用的认证方式。二选一：
  1) cp .env.example .env  并把 MINIMAX_TOKEN 填成你的真实 token
  2) 或先执行 claude 订阅登录（让 ~/.claude/.credentials.json 存在）"
fi

# ── Stage 2: 写 settings.json（含 insights-wiki hook），订阅再软链 credentials ──
# 不 symlink 用户全局 settings.json —— 全局里注册的是 continuous-learning 等
# 其他用户 hook，在沙箱 HOME 下 claude 解析路径时找不到脚本，会报
# 　Stop hook error: evaluate-session.sh: No such file or directory
# 更关键：insights-wiki 的触发是 **hook 驱动**（UserPromptSubmit + Stop），
# 必须用 demo_codes/.claude/settings.json 这份注册，skill 才会被 claude 真正"用上"。
# user-level + project-level 各放一份，两条加载路径都能找到。
cp "$DEMO_SETTINGS" "$SANDBOX_CLAUDE/settings.json"
cp "$DEMO_SETTINGS" "$SANDBOX_WORKDIR/.claude/settings.json"
if [ "$AUTH_MODE" = "subscription" ]; then
  ln -s "$HOME/.claude/.credentials.json" "$SANDBOX_CLAUDE/.credentials.json"
  step 2 "装入 insights-wiki hook + 订阅 credentials . done"
else
  step 2 "装入 insights-wiki hook（走 MiniMax）....... done"
fi

# ── Stage 3: 拷贝 skill 到沙箱（双位置：user-level + project-level）─────────
# 用 cp 而不是 symlink：用户在 demo 里如果改了 skill，不影响源文件
cp -R "$SKILL_SRC" "$SANDBOX_CLAUDE/skills/$SKILL_NAME"
cp -R "$SKILL_SRC" "$SANDBOX_WORKDIR/.claude/skills/$SKILL_NAME"
step 3 "拷贝 $SKILL_NAME skill 到沙箱（user+project 双保险）... done"

# ── Stage 4: 按 AUTH_MODE 写环境文件 ────────────────────
# token 来源在 Stage 2 之前就已决定，这里只负责把它落到沙箱 .env：
#   - minimax 模式 → 注入全套 ANTHROPIC_*/CLAUDE_CODE_* 变量
#   - subscription 模式 → 只写基本沙箱变量，让 claude 走订阅登录
#
# 安全说明：token 只写进 /tmp/demo-sandbox-*/.env（chmod 600），
# 退出时随沙箱 rm -rf 一起删除，不会落到真实 ~/.claude/。
#
# 注意：heredoc 里凡是变量后面跟中文字符的，一律用 ${VAR} 花括号
# 否则在非 UTF-8 locale 下 bash 会把 UTF-8 字节当成变量名的一部分
cat > "$ENV_FILE" <<EOF
# sandbox env (ts=${TS}, auth_mode=${AUTH_MODE})
export SANDBOX_ROOT="${SANDBOX}"
export DEMO_GUIDE_LOG="${GUIDE_LOG}"
# KEY: override HOME so claude reads sandbox ~/.claude/
export HOME="${SANDBOX_HOME}"
EOF

if [ "$AUTH_MODE" = "minimax" ]; then
  cat >> "$ENV_FILE" <<EOF

# --- MiniMax 高速通道 -----------------
export ANTHROPIC_AUTH_TOKEN="${TOKEN}"
export ANTHROPIC_BASE_URL="https://api.minimaxi.com/anthropic"
export ANTHROPIC_MODEL="MiniMax-M2.7-highspeed"
export ANTHROPIC_DEFAULT_HAIKU_MODEL="MiniMax-M2.7-highspeed"
export ANTHROPIC_DEFAULT_OPUS_MODEL="MiniMax-M2.7-highspeed"
export ANTHROPIC_DEFAULT_SONNET_MODEL="MiniMax-M2.7-highspeed"
export API_TIMEOUT_MS="3000000"
export CLAUDE_CODE_DISABLE_ADAPTIVE_THINKING="1"
export CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC="1"
export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS="1"
EOF
  step 4 "注入 MiniMax 高速通道 ............... done"
else
  step 4 "走 Claude 订阅登录（未注入 MiniMax）.. done"
fi
# 让 hook 里的 urllib 走直连（本机 proxy 7897 会让 127.0.0.1:7821 也被代理）
cat >> "$ENV_FILE" <<EOF

# --- 绕开 http_proxy，让 hook 直连 insightsd -----------
export NO_PROXY="127.0.0.1,localhost"
export no_proxy="127.0.0.1,localhost"
EOF
chmod 600 "$ENV_FILE"

# ── Stage 5: 启动 insightsd daemon（如未在跑）──────────
# insights-wiki skill 的 hook 硬编码访问 http://127.0.0.1:7821。
# daemon 离线时 Stop hook 会报错并挂在 claude 输出里，demo 观感差。
# 策略：7821 已 LISTEN → 复用（不动）；否则用 demo_codes/.venv 后台启动，
# PID 写进沙箱文件；cleanup 只 kill 我们自己起的 daemon。
DAEMON_STARTED_BY_US=0
if lsof -iTCP:${DAEMON_PORT} -sTCP:LISTEN -nP >/dev/null 2>&1; then
  step 5 "insightsd :${DAEMON_PORT} 已在运行（复用）... done"
else
  (
    cd "$DEMO_CODES"
    nohup "$DEMO_VENV_PY" insights_cli.py serve \
      --host 127.0.0.1 --port "$DAEMON_PORT" \
      --store wiki.json --store-mode flat \
      > "$DAEMON_LOG" 2>&1 &
    echo $! > "$DAEMON_PID_FILE"
  )
  DAEMON_STARTED_BY_US=1
  # 给 daemon 最多 5 秒起来
  for i in 1 2 3 4 5; do
    if lsof -iTCP:${DAEMON_PORT} -sTCP:LISTEN -nP >/dev/null 2>&1; then
      break
    fi
    sleep 1
  done
  if lsof -iTCP:${DAEMON_PORT} -sTCP:LISTEN -nP >/dev/null 2>&1; then
    step 5 "后台启动 insightsd :${DAEMON_PORT}（PID $(cat "$DAEMON_PID_FILE")）... done"
  else
    die "insightsd 未能在 5s 内监听 ${DAEMON_PORT}，请看 $DAEMON_LOG"
  fi
fi

# ── Stage 6: tmux 检查 ─────────────────────────────────
step 6 "tmux $(tmux -V | awk '{print $2}') 已就绪 ............. done"

# ── Stage 7: 启动 tmux 双 pane ────────────────────────
step 7 "即将切入双 pane（3 秒后）........ done"
note "左=讲解（自动推进）│ 右=你的 Claude │ F12 整体退出"
note "鼠标拖选 = 自动复制到系统剪贴板（松开即复制，Cmd+V 可粘贴）"
sleep 3

# ── 清理钩子 ───────────────────────────────────────────
SESSION="demo-$$"
# 用独立 socket 而不是默认 socket，支持在已有 tmux（如 live_demo）里 nested
# 调用 —— 否则 `tmux attach` 会被拦截：sessions should be nested with care。
# -L 指向独立 socket = 独立 server，和外层 $TMUX 完全无关。
SOCK="demo-${TS}-$$"
tm() { tmux -L "$SOCK" "$@"; }

cleanup() {
  tm kill-session -t "$SESSION" 2>/dev/null || true
  tm kill-server 2>/dev/null || true
  # 只 kill 我们自己启动的 daemon；外部预先在跑的保留
  if [ "${DAEMON_STARTED_BY_US:-0}" = "1" ] && [ -f "$DAEMON_PID_FILE" ]; then
    kill "$(cat "$DAEMON_PID_FILE")" 2>/dev/null || true
  fi
  # 保存本次日志副本到仓库外部，方便事后翻看
  local final_log="$REPO_ROOT/insights-share/validation/reports/deliverables/start_demo.latest.txt"
  mkdir -p "$(dirname "$final_log")"
  cp -f "$GUIDE_LOG" "$final_log" 2>/dev/null || true
  # 整个沙箱直接删除 —— 真实 ~/.claude/ 无任何残留
  rm -rf "$SANDBOX"
  printf '\n\033[36m[cleanup]\033[0m 沙箱已删除，真实 ~/.claude/ 零污染。日志：\n  %s\n' "$final_log"
}
trap cleanup EXIT

# ── 组装左右 pane 命令 ─────────────────────────────────
# 左 pane：后台 guide_loop 写 log，前台 tail -f 显示（用沙箱 HOME 监听）
LEFT_SH="$SANDBOX/left.sh"
cat > "$LEFT_SH" <<EOF
#!/usr/bin/env bash
export HOME="$SANDBOX_HOME"
bash "$GUIDE_SCRIPT" "$SANDBOX" "$GUIDE_LOG" "$SKILL_NAME" "$SANDBOX_HOME" >/dev/null 2>&1 &
exec tail -f "$GUIDE_LOG"
EOF
chmod +x "$LEFT_SH"

# 右 pane：
#   1. cd 到沙箱 workdir（避免把仓库根目录当项目根）
#   2. source env（提供 MiniMax 相关变量）
#   3. 先用 bash 做一次自检（pwd / HOME / skills 列表）让用户肉眼看到隔离生效
#   4. 用 HOME=... exec claude 覆盖 HOME，exec 替换 shell 进程，彻底避免 rc 干扰
#
# 写成独立脚本而不是塞进 tmux split-window 的字符串参数 —— 多行 + 嵌套
# 双引号走 `bash -lc "..."` 链路时解析很脆，之前就因此翻车（pane 被 tmux
# 创建后命令立即 exit，引发后续 `can't find pane: 1`）。
RIGHT_SH="$SANDBOX/right.sh"
cat > "$RIGHT_SH" <<EOF
#!/usr/bin/env bash
cd "$SANDBOX_WORKDIR"
source "$ENV_FILE"
clear
echo "================ sandbox self-check ================"
echo "cwd  : $SANDBOX_WORKDIR"
echo "HOME : $SANDBOX_HOME"
echo "----- project-level skills (\\\$cwd/.claude/skills/) -----"
ls "$SANDBOX_WORKDIR/.claude/skills/" 2>/dev/null || echo "(none)"
echo "----- user-level skills (\\\$HOME/.claude/skills/) -----"
ls "$SANDBOX_HOME/.claude/skills/" 2>/dev/null || echo "(none)"
echo "===================================================="
echo "期望: 两边都只有 insights-wiki，看不到你全局的其他 skill。"
printf "按回车进入 claude…"
read _
HOME="$SANDBOX_HOME" exec claude
EOF
chmod +x "$RIGHT_SH"

# ── 启动 tmux（独立 socket）────────────────────────────
tm -f "$TMUX_CONF" new-session -d -s "$SESSION" -x 220 -y 55 \
  "bash '$LEFT_SH'"
tm select-pane -t "$SESSION:0.0" -T '📖 讲解（自动推进，只读） · 鼠标拖选=自动复制'

tm split-window -h -t "$SESSION:0.0" \
  "bash '$RIGHT_SH'"
tm select-pane -t "$SESSION:0.1" -T '🟠 Claude 会话（沙箱 HOME，安全操作）'

# 讲解 40%，Claude 60%
tm resize-pane -t "$SESSION:0.0" -x 45%

# 光标默认停右边
tm select-pane -t "$SESSION:0.1"

# ── attach ─────────────────────────────────────────────
# 用独立 socket attach，nested 场景（外层 live_demo tmux）也不会被拦。
tm attach -t "$SESSION"
