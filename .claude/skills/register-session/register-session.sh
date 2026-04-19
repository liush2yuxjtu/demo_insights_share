#!/usr/bin/env bash
set -euo pipefail

# register-session
# 把用户实机操作的 tmux session 注册到固定契约，让 agent 能 Read 到 pipe-pane 日志。
# 契约：
#   ~/.claude/live_terminal/CURRENT      单行文件，当前活跃 session 名
#   ~/.claude/live_terminal/<name>.log   tmux pipe-pane 镜像

LIVE_DIR="${HOME}/.claude/live_terminal"
CURRENT_FILE="${LIVE_DIR}/CURRENT"

mkdir -p "${LIVE_DIR}"

usage() {
  cat <<'EOF'
用法:
  register-session <name>              新建 tmux session + pipe-pane + 弹出 Terminal + 写 CURRENT
  register-session <name> --existing   仅绑定已有 session（补 pipe-pane + 写 CURRENT，不弹窗）
  register-session                     查询当前注册的 session + 最近日志
  register-session --clear             清空 CURRENT（不 kill session）
  register-session --help              打印本帮助
EOF
}

valid_name() {
  [[ "$1" =~ ^[A-Za-z0-9_-]+$ ]]
}

if ! command -v tmux >/dev/null 2>&1; then
  echo "错误：未安装 tmux。brew install tmux 后再试。" >&2
  exit 10
fi

mode="create"
name=""

if [[ $# -eq 0 ]]; then
  mode="query"
elif [[ "$1" == "--help" || "$1" == "-h" ]]; then
  usage; exit 0
elif [[ "$1" == "--clear" ]]; then
  mode="clear"
else
  name="$1"
  shift || true
  if [[ "${1:-}" == "--existing" ]]; then
    mode="existing"
  fi
fi

case "$mode" in
  query)
    if [[ -f "$CURRENT_FILE" ]]; then
      cur="$(cat "$CURRENT_FILE")"
      log="${LIVE_DIR}/${cur}.log"
      echo "当前 session: ${cur}"
      echo "日志路径:     ${log}"
      if tmux has-session -t "${cur}" 2>/dev/null; then
        echo "tmux 状态:    alive"
      else
        echo "tmux 状态:    NOT FOUND（已被 kill；可用 --clear 清 CURRENT）"
      fi
      if [[ -f "$log" ]]; then
        echo "日志行数:     $(wc -l < "$log" | tr -d ' ')"
        echo "--- 最近 10 行 ---"
        tail -n 10 "$log" 2>/dev/null || true
      fi
    else
      echo "未注册任何 session。用 register-session <name> 注册。"
    fi
    exit 0
    ;;
  clear)
    rm -f "$CURRENT_FILE"
    echo "已清空 CURRENT（session 本体未 kill）。"
    exit 0
    ;;
esac

if ! valid_name "$name"; then
  echo "无效 name：只允许字母、数字、下划线、连字符。" >&2
  exit 2
fi

LOG_FILE="${LIVE_DIR}/${name}.log"

if [[ "$mode" == "create" ]]; then
  if tmux has-session -t "${name}" 2>/dev/null; then
    echo "session '${name}' 已存在。用 --existing 绑定或先 tmux kill-session -t ${name}。" >&2
    exit 3
  fi
  tmux new-session -d -s "${name}" -x 220 -y 60
elif [[ "$mode" == "existing" ]]; then
  if ! tmux has-session -t "${name}" 2>/dev/null; then
    echo "session '${name}' 不存在。去掉 --existing 让脚本新建。" >&2
    exit 3
  fi
fi

: > "${LOG_FILE}"
tmux pipe-pane -o -t "${name}" "cat > ${LOG_FILE}"
echo "${name}" > "${CURRENT_FILE}"

if [[ "$mode" == "create" ]]; then
  osascript <<OSA >/dev/null 2>&1 || true
tell application "Terminal"
  activate
  do script "tmux attach -t ${name}"
end tell
OSA
fi

cat <<EOF
已注册 session: ${name}
日志文件:      ${LOG_FILE}
CURRENT:       ${CURRENT_FILE}
EOF

if [[ "$mode" == "create" ]]; then
  echo "已弹出 Terminal 窗口并 attach。之后在那个窗口里的一切都会实时写入日志。"
else
  echo "已绑定到现有 session。agent Read 上面的日志文件即可看到实时输出。"
fi
