#!/usr/bin/env bash
# start.demo.sh — tmux noob 友好的 insights-share demo 入口（真沙箱版）
#
# 沙箱设计（绝不污染真实 ~/.claude/）：
#   /tmp/demo-sandbox-<ts>.XXXX/
#     home/
#       .claude/
#         plugins/                     ← claude plugin install 写入的真实 plugin cache
#         .credentials.json            ← 订阅模式下软链到真实 auth
#         settings.json                ← plugin marketplace + enabledPlugins
#       .cache/                        ← insights-share plugin 写缓存的地方
#     guide.log                        ← 左 pane tail -f
#     right.log                        ← 右 pane self-check 证据
#     .env                             ← 右 pane source 的环境文件
#
# 启动 claude 时右 pane export HOME=$SANDBOX_HOME，
# 所以 claude 看到的 ~/.claude/ 就是沙箱目录，plugin install 和 cache 全部隔离。
# 退出时一口气 rm -rf 沙箱，真实 HOME 零污染。

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
TS="$(date +%Y%m%d-%H%M%S)"
SANDBOX="$(mktemp -d "/tmp/demo-sandbox-${TS}.XXXXXX")"
SANDBOX_HOME="$SANDBOX/home"
SANDBOX_CLAUDE="$SANDBOX_HOME/.claude"
SANDBOX_WORKDIR="$SANDBOX/workdir"   # claude 的 cwd — 只有项目级 skill，不放别的
GUIDE_LOG="$SANDBOX/guide.log"
RIGHT_LOG="$SANDBOX/right.log"
ENV_FILE="$SANDBOX/.env"
DEMO_CODES="$REPO_ROOT/insights-share/demo_codes"
PLUGIN_DIR="$REPO_ROOT/plugins/insights-share"
PLUGIN_NAME="insights-share"
INSTALLED_PLUGIN_DIR=""
PLUGIN_SERVER_START=""
DAEMON_PORT="7821"
DAEMON_LOG="$SANDBOX/insightsd.log"
DAEMON_PID_FILE="$SANDBOX/insightsd.pid"
TMUX_CONF="$REPO_ROOT/insights-share/validation/tmux.noob.conf"
GUIDE_SCRIPT="$REPO_ROOT/insights-share/validation/guide_loop.sh"

# ── dry-run flag 解析（D6：为 test_start_scripts.py 提供白盒断言入口）───
# DRY_RUN=1 时跳过 Stage 5 daemon 启动 + Stage 7 tmux attach，
# 但保留 Stage 1-4（沙箱/settings/skill/env 真跑），最后 dump LEFT_SH+RIGHT_SH。
# 沙箱仍被 cleanup trap 删除，无残留。
DRY_RUN=0
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=1 ;;
    --help|-h) echo "Usage: start.demo.sh [--dry-run]"; exit 0 ;;
  esac
done
[ "${DRY_RUN:-0}" = "1" ] && DRY_RUN=1

# ── 漂亮的进度条输出 ──────────────────────────────────
step() { printf '\033[32m🟢 [%s/7]\033[0m %s\n' "$1" "$2"; }
die()  { printf '\033[31m[错误]\033[0m %s\n' "$1" >&2; exit 1; }
note() { printf '\033[36m[提示]\033[0m %s\n' "$1"; }

resolve_installed_plugin_dir() {
  python3 - "$SANDBOX_HOME" "$PLUGIN_NAME" <<'PY'
import json
import sys
from pathlib import Path

home = Path(sys.argv[1])
plugin_name = sys.argv[2]
cache_root = home / ".claude" / "plugins" / "cache"
for manifest in sorted(cache_root.glob("**/.claude-plugin/plugin.json")):
    try:
        payload = json.loads(manifest.read_text(encoding="utf-8"))
    except Exception:
        continue
    if payload.get("name") == plugin_name:
        print(manifest.parents[1])
        raise SystemExit(0)
raise SystemExit(1)
PY
}

# ── 前置检查 ───────────────────────────────────────────
[ -d "$PLUGIN_DIR/.claude-plugin" ] || die "缺失 plugin 根目录：$PLUGIN_DIR"
[ -f "$TMUX_CONF" ]     || die "缺失 tmux 配置：$TMUX_CONF"
[ -f "$GUIDE_SCRIPT" ]  || die "缺失 guide 脚本：$GUIDE_SCRIPT"
command -v tmux   >/dev/null 2>&1 || die "请先安装 tmux：brew install tmux"
command -v claude >/dev/null 2>&1 || die "请先安装 claude CLI"
command -v python3 >/dev/null 2>&1 || die "请先安装 python3"

# ── Stage 0: raw secret gate ──────────────────────────
secret_gate() {
  local findings=""
  findings="$(rg -n -S --glob '**/raw/*' \
    'sk-[A-Za-z0-9_-]{10,}|ghp_[A-Za-z0-9]{20,}|Bearer[[:space:]]+[A-Za-z0-9._~+/-]{10,}|AKIA[0-9A-Z]{16}' \
    "$DEMO_CODES/wiki_tree" "$PLUGIN_DIR/runtime/wiki_tree" 2>/dev/null || true)"
  if [ -n "$findings" ]; then
    printf '%s\n' "$findings" >&2
    rm -rf "$SANDBOX"
    die "Stage 0 secret gate failed：wiki_tree/**/raw 含疑似明文 secret，请先脱敏再跑 demo"
  fi
  note "Stage 0 secret gate passed（wiki_tree/**/raw 无明文 secret）"
}
secret_gate

# ── Stage 1: 准备沙箱目录 ─────────────────────────────
mkdir -p "$SANDBOX_CLAUDE" "$SANDBOX_HOME/.cache" "$SANDBOX_WORKDIR"
: > "$GUIDE_LOG"
: > "$RIGHT_LOG"
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

# ── Stage 2: 认证准备（订阅 credentials 软链；MiniMax 不落 settings） ─────
if [ "$AUTH_MODE" = "subscription" ]; then
  ln -s "$HOME/.claude/.credentials.json" "$SANDBOX_CLAUDE/.credentials.json"
  step 2 "准备订阅 credentials ................ done"
else
  step 2 "MiniMax 模式无需 credentials ........ done"
fi

# ── Stage 3: 真实 plugin install（user-scope, sandbox HOME）──────────────
HOME="$SANDBOX_HOME" claude plugin marketplace add "$PLUGIN_DIR" --scope user >/dev/null
HOME="$SANDBOX_HOME" claude plugin install "${PLUGIN_NAME}@${PLUGIN_NAME}" --scope user >/dev/null
INSTALLED_PLUGIN_DIR="$(resolve_installed_plugin_dir)" || die "无法定位 sandbox 已安装 plugin cache"
PLUGIN_SERVER_START="$INSTALLED_PLUGIN_DIR/skills/insights-share-server/scripts/start_server.sh"
[ -x "$PLUGIN_SERVER_START" ] || die "已安装 plugin 缺少 server 启动脚本：$PLUGIN_SERVER_START"
step 3 "claude plugin install ${PLUGIN_NAME}@${PLUGIN_NAME} ... done"

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

# --- demo 沙箱强制走本机 daemon，不跟随 plugin 默认 LAN 地址 ---
export INSIGHTS_SHARE_URL="http://127.0.0.1:${DAEMON_PORT}"
export INSIGHTS_DAEMON_URL="http://127.0.0.1:${DAEMON_PORT}"
EOF
chmod 600 "$ENV_FILE"

# ── Stage 5: 启动 insightsd daemon（如未在跑）──────────
# insights-share plugin 默认指向固定 LAN 地址；demo 沙箱通过上面的
# INSIGHTS_SHARE_URL / INSIGHTS_DAEMON_URL 显式改回本机 127.0.0.1。
# daemon 离线时 Stop hook 会报错并挂在 claude 输出里，demo 观感差。
# 策略：7821 已 LISTEN → 复用（不动）；否则用 sandbox 已安装 plugin 的
# bundle-local runtime 后台启动，
# PID 写进沙箱文件；cleanup 只 kill 我们自己起的 daemon。
DAEMON_STARTED_BY_US=0
if [ "$DRY_RUN" = "1" ]; then
  step 5 "DRY RUN: would start insightsd :${DAEMON_PORT} via installed plugin runtime ........ skipped"
elif lsof -iTCP:${DAEMON_PORT} -sTCP:LISTEN -nP >/dev/null 2>&1; then
  step 5 "insightsd :${DAEMON_PORT} 已在运行（复用）... done"
else
  HOME="$SANDBOX_HOME" \
  INSIGHTS_SHARE_HOST="127.0.0.1" \
  INSIGHTS_SHARE_PORT="$DAEMON_PORT" \
  INSIGHTS_SHARE_STORE="$INSTALLED_PLUGIN_DIR/runtime/wiki_tree" \
  INSIGHTS_UI_ENABLE_RUNNERS=1 \
    nohup bash "$PLUGIN_SERVER_START" > "$DAEMON_LOG" 2>&1 &
  echo $! > "$DAEMON_PID_FILE"
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
  if [ "$DRY_RUN" != "1" ]; then
    {
      echo "===== LEFT PANE GUIDE LOG ====="
      cat "$GUIDE_LOG" 2>/dev/null || true
      echo
      echo "===== RIGHT PANE SELF-CHECK LOG ====="
      cat "$RIGHT_LOG" 2>/dev/null || true
    } > "$final_log" 2>/dev/null || true
  fi
  # 整个沙箱直接删除 —— 真实 ~/.claude/ 无任何残留
  rm -rf "$SANDBOX"
  if [ "$DRY_RUN" = "1" ]; then
    printf '\n\033[36m[cleanup]\033[0m 沙箱已删除，真实 ~/.claude/ 零污染。dry-run 不覆盖 latest 日志。\n'
  else
    printf '\n\033[36m[cleanup]\033[0m 沙箱已删除，真实 ~/.claude/ 零污染。日志：\n  %s\n' "$final_log"
  fi
}
trap cleanup EXIT

# ── 组装左右 pane 命令 ─────────────────────────────────
# 左 pane：后台 guide_loop 写 log，前台 tail -f 显示（用沙箱 HOME 监听）
LEFT_SH="$SANDBOX/left.sh"
cat > "$LEFT_SH" <<EOF
#!/usr/bin/env bash
# 只加 set -u 不加 -e/-pipefail：exec tail -f 下 -e 无意义，下游 lossy pipe 无。
set -u
# 入口预检 4 项资源（feedback_real_sandbox.md: 沙箱隔离不可退化）
for _p in "$SANDBOX" "$GUIDE_LOG" "$GUIDE_SCRIPT" "$SANDBOX_HOME"; do
  if [ ! -e "\$_p" ]; then
    echo "[left pane FATAL] 缺资源: \$_p" >&2
    echo "(pane 保留 60s 供查看, 然后退出)" >&2
    sleep 60
    exit 1
  fi
done
export HOME="$SANDBOX_HOME"
bash "$GUIDE_SCRIPT" "$SANDBOX" "$GUIDE_LOG" "$PLUGIN_NAME" "$SANDBOX_HOME" >/dev/null 2>&1 &
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
# 只加 set -u 不加 -e/-pipefail：RIGHT_SH 里大量故意 lossy pipe (| head | sed | xargs)，
# pipefail 会把 benign miss 变 pane killer；-u 只防未定义变量，是最小诚实防护。
set -u
exec > >(tee -a "$RIGHT_LOG") 2>&1
# 入口预检 5 项资源
for _p in "$SANDBOX_WORKDIR" "$ENV_FILE" "$SANDBOX_HOME" "$REPO_ROOT" "$INSTALLED_PLUGIN_DIR"; do
  if [ ! -e "\$_p" ]; then
    echo "[right pane FATAL] 缺资源: \$_p" >&2
    echo "(pane 保留 60s 供查看, 然后退出)" >&2
    sleep 60
    exit 1
  fi
done
cd "$SANDBOX_WORKDIR"
source "$ENV_FILE"
clear
echo "================ sandbox self-check ================"
echo "cwd  : $SANDBOX_WORKDIR"
echo "HOME : $SANDBOX_HOME"
echo "tmux : F1=左pane(讲解) / F2=右pane(Claude) / F12=退出"
echo "----- installed plugins (\\\$HOME/.claude/plugins/installed_plugins.json) -----"
cat "$SANDBOX_HOME/.claude/plugins/installed_plugins.json" 2>/dev/null || echo "(missing)"
echo "----- plugin cache roots (\\\$HOME/.claude/plugins/cache/) -----"
find "$SANDBOX_HOME/.claude/plugins/cache" -maxdepth 4 -mindepth 1 2>/dev/null | sed 's#^#  #' || echo "(none)"
echo "----- repo *.sh (\\\$REPO_ROOT/*.sh) -----"
ls "$REPO_ROOT"/*.sh 2>/dev/null | xargs -n1 basename 2>/dev/null || echo "(none)"
echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  📋 CANONICAL FEATURE MANIFEST (source: FEATURES.md)          ║"
echo "╚══════════════════════════════════════════════════════════════╝"
if [ -f "$REPO_ROOT/FEATURES.md" ]; then
  cat "$REPO_ROOT/FEATURES.md"
else
  echo "(FEATURES.md 缺失 — canonical 源丢失, 请 checkout main)"
fi
echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  🔬 LIVE RUNTIME EVIDENCE (per-feature)                      ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "┌─ [F1] wiki_tree 数据 ─────────────────────────────────────────"
if [ -f "$INSTALLED_PLUGIN_DIR/runtime/wiki_tree/topics.json" ]; then
  topic_n=\$(python3 -c 'import json,sys;print(len(json.load(open(sys.argv[1]))))' "$INSTALLED_PLUGIN_DIR/runtime/wiki_tree/topics.json" 2>/dev/null || echo "?")
  card_n=\$(find "$INSTALLED_PLUGIN_DIR/runtime/wiki_tree" -name "*.md" -not -name "INDEX.md" 2>/dev/null | wc -l | tr -d ' ')
  echo "│  Topics: \${topic_n} · Cards: \${card_n}"
else
  echo "│  (wiki_tree 未就绪)"
fi
echo ""
echo "┌─ [F2] 实机 statusline 徽章 ───────────────────────────────────"
printf  "│  "
INSIGHTS_SHARE_URL=http://127.0.0.1:${DAEMON_PORT} SHARE_STATUSLINE_NO_COLOR=1 \
  bash "$INSTALLED_PLUGIN_DIR/statusline/insights_share_statusline.sh" \
  2>&1 | head -1 || echo "(statusline exit non-zero)"
echo ""
echo "┌─ [F3] plugin manifest ────────────────────────────────────────"
plugin_json="$INSTALLED_PLUGIN_DIR/.claude-plugin/plugin.json"
if [ -f "\$plugin_json" ]; then
  ver=\$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["version"])' "\$plugin_json" 2>/dev/null || echo "?")
  echo "│  version: \${ver}"
else
  echo "│  (plugin.json 未找到)"
fi
echo ""
echo "┌─ [F4] slash 命令 + agent 文件存在性 ──────────────────────────"
cmd_dir="$INSTALLED_PLUGIN_DIR/commands"
if [ -d "\$cmd_dir" ]; then
  for f in share-install share-search share-publish share-review share-diff; do
    if [ -f "\$cmd_dir/\${f}.md" ]; then
      echo "│  /\${f}   ✓"
    else
      echo "│  /\${f}   ✗ MISSING"
    fi
  done
  agent_dir="$INSTALLED_PLUGIN_DIR/agents"
  echo "│  agents: share-validator(\$([ -f "\$agent_dir/share-validator.md" ] && echo ✓ || echo ✗)) · share-curator(\$([ -f "\$agent_dir/share-curator.md" ] && echo ✓ || echo ✗))"
else
  echo "│  (commands 目录未找到)"
fi
echo ""
echo "┌─ [F5] 签名 + marketplace ─────────────────────────────────────"
if grep -q "sig-fail" "$INSTALLED_PLUGIN_DIR/statusline/insights_share_statusline.sh" 2>/dev/null; then
  echo "│  ed25519 sig-fail state: ✓ 支持"
else
  echo "│  ed25519 sig-fail state: ? 未找到"
fi
mp_json="$INSTALLED_PLUGIN_DIR/.claude-plugin/marketplace.json"
if [ -f "\$mp_json" ]; then
  echo "│  LAN marketplace: ✓"
else
  echo "│  LAN marketplace: ✗"
fi
echo ""
echo "┌─ [F6] 样例 Example schema 字段 ───────────────────────────────"
sample="$INSTALLED_PLUGIN_DIR/runtime/wiki_tree/database/postgres_pool.md"
if [ -f "\$sample" ]; then
  grep -E '"(id|topic_id|label|applies_when|do_not_apply_when|raw_log_type|raw_log)"' "\$sample" 2>/dev/null | head -6 | sed 's/^/│  /'
else
  echo "│  (sample 未找到)"
fi
echo ""
echo "----- plugin self-check (sandbox installed plugin cache) -----"
bash "$INSTALLED_PLUGIN_DIR/scripts/self_check.sh" \
  || echo "(plugin self-check exit non-zero)"
echo "===================================================="
echo "期望: 6/6 feature 全 ✓；sandbox 内已完成真实 plugin install；plugin self-check ALL GREEN。"
echo "按 F1 看左 pane 讲解 · F2 回来进 claude · F12 退出 demo。"
printf "按回车进入 claude…"
read _
HOME="$SANDBOX_HOME" exec claude
EOF
chmod +x "$RIGHT_SH"

# ── dry-run 分支：打印 LEFT_SH + RIGHT_SH dump，不 spawn tmux，不 attach ─
# test_start_scripts.py 走 `bash start.demo.sh --dry-run` → 断言 stdout schema。
if [ "$DRY_RUN" = "1" ]; then
  echo ""
  echo "==== DRY RUN: provider=demo auth_mode=$AUTH_MODE sandbox=$SANDBOX ===="
  echo "==== 固定步骤数=7 ===="
  echo "==== would spawn tmux session '$SESSION' on socket '$SOCK' ===="
  echo ""
  echo "==== LEFT_SH ($LEFT_SH) ===="
  cat "$LEFT_SH"
  echo ""
  echo "==== RIGHT_SH ($RIGHT_SH) ===="
  cat "$RIGHT_SH"
  echo ""
  echo "==== ENV_FILE ($ENV_FILE, secrets REDACTED) ===="
  sed -E \
    -e 's/(ANTHROPIC_AUTH_TOKEN=")[^"]*/\1<REDACTED>/' \
    -e 's/(ANTHROPIC_API_KEY=")[^"]*/\1<REDACTED>/' \
    -e 's/(MINIMAX_TOKEN=")[^"]*/\1<REDACTED>/' \
    -e 's/(Bearer )[A-Za-z0-9._~+/-]+/\1<REDACTED>/g' \
    "$ENV_FILE"
  echo ""
  echo "==== 输出日志归档路径 (D5 pending): $REPO_ROOT/insights-share/validation/reports/deliverables/ ===="
  echo "==== DRY RUN END — trap cleanup 将删除沙箱 ===="
  exit 0
fi

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
