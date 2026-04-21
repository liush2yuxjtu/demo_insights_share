#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SOURCE_DIR="${REPO_ROOT}/insights-share/demo_codes"
LOG_DIR="${REPO_ROOT}/insights-share/validation/reports/deliverables"
PORT="${PORT:-17821}"
WORKDIR=""
RUN_DIR=""
ENV_FILE=""
PYTHON_BIN="${SOURCE_DIR}/.venv/bin/python"
CACHE_DIR="${HOME}/.cache/insights-share"
CACHE_BACKUP=""
DAEMON_PID=""
AUTO_APPROVE=0
DRY_RUN=0
NEXT_NOTE_PID=""
NEXT_NOTE_FILE=""
NEXT_NOTE_RAW=""
LAST_STEP_OUTPUT=""
CURRENT_STEP=0
LOG_FILE=""
PROVIDER_NAME=""
COACH_STDOUT_DIR=""
GUIDE_PID=""
GUIDE_FILE=""
GUIDE_RAW=""

STEP_TITLES=(
  "确认自己在隔离副本里"
  "确认 demo CLI 可以运行"
  "启动本地 wiki 服务"
  "确认服务健康检查通过"
  "查看初始 wiki 列表"
  "发布 Alice 的 good 案例"
  "发布 Bob 的 bad 案例"
  "用真实事故问题做一次 solve"
  "安装 insights-share 到本机缓存"
  "确认缓存文件已经落地"
)

STEP_COMMANDS=(
  "pwd && printf '\n' && ls -la"
  "\"${PYTHON_BIN}\" insights_cli.py version"
  "mkdir -p ./runtime-start && \"${PYTHON_BIN}\" insights_cli.py serve --host 127.0.0.1 --port ${PORT} --store ./runtime-start/wiki_tree --store-mode tree >/tmp/start_${START_PROVIDER}_daemon.${PORT}.log 2>&1 & echo \$! > .start_demo_daemon.pid && cat .start_demo_daemon.pid"
  "for attempt in 1 2 3 4 5 6 7 8 9 10; do curl -fsS \"http://127.0.0.1:${PORT}/healthz\" && exit 0; sleep 1; done; exit 1"
  "\"${PYTHON_BIN}\" insights_cli.py list --wiki \"http://127.0.0.1:${PORT}\""
  "\"${PYTHON_BIN}\" insights_cli.py publish seeds/alice_pgpool.json --wiki \"http://127.0.0.1:${PORT}\""
  "\"${PYTHON_BIN}\" insights_cli.py publish seeds/bob_pgpool_bad.json --wiki \"http://127.0.0.1:${PORT}\""
  "\"${PYTHON_BIN}\" insights_cli.py solve \"Our checkout API is timing out, postgres is rejecting new connections during the lunch spike\" --wiki \"http://127.0.0.1:${PORT}\" --no-ai"
  "\"${PYTHON_BIN}\" insights_cli.py wiki-install --server \"http://127.0.0.1:${PORT}\""
  "ls -la ~/.cache/insights-share && printf '\n' && find ~/.cache/insights-share -maxdepth 1 -type f | sort"
)

STEP_WHYS=(
  "先确认你看到的是临时副本，不会污染正式仓库。"
  "先看 CLI 版本，能最快证明可执行文件和 Python 运行时是通的。"
  "没有服务端就没有后续发布、搜索和安装，所以它是整条链路的起点。"
  "健康检查通过，后面所有 HTTP 命令才有意义。"
  "先看空表，PM 才能直观看到“发布前”和“发布后”的差异。"
  "先放入一个 good 实战案例，让 solve 有正确经验可命中。"
  "再放入一个 bad 案例，展示 wiki 同时能容纳反例。"
  "这一步最像真实使用场景：用户问问题，系统热加载经验并直接给出答案。"
  "安装步骤会把服务端内容写入本机缓存，模拟普通用户接入 LAN wiki。"
  "最后确认缓存文件真的落盘，给 PM 一个可以截图的成功证据。"
)

HEALTHZ_OK=0
PUBLISH_GOOD_OK=0
PUBLISH_BAD_OK=0
SOLVE_OK=0
INSTALL_OK=0
CACHE_OK=0

usage() {
  cat <<EOF
用法：
  bash start.${START_PROVIDER}.sh
  bash start.${START_PROVIDER}.sh --auto-approve
  bash start.${START_PROVIDER}.sh --dry-run

说明：
  1. 脚本会复制一份隔离 demo_codes，不会改你的正式源码。
  2. 每一步都先由 ${PROVIDER_NAME} 在后台生成“小白也能看懂”的下一步说明。
  3. 默认会等待你按回车才继续；加 --auto-approve 则全自动跑完整条链路。
  4. 完整输出会保存到 ${LOG_DIR}/start_${START_PROVIDER}.latest.txt
EOF
}

log() {
  printf '[start.%s] %s\n' "${START_PROVIDER}" "$*"
}

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    printf '缺少命令：%s\n' "$1" >&2
    exit 127
  fi
}

setup_logging() {
  LOG_FILE="${LOG_DIR}/start_${START_PROVIDER}.latest.txt"
  mkdir -p "${LOG_DIR}"
  exec > >(tee "${LOG_FILE}") 2>&1
}

cleanup() {
  if [ -n "${NEXT_NOTE_PID}" ]; then
    wait "${NEXT_NOTE_PID}" 2>/dev/null || true
  fi
  if [ -z "${DAEMON_PID}" ] && [ -n "${RUN_DIR}" ] && [ -f "${RUN_DIR}/.start_demo_daemon.pid" ]; then
    DAEMON_PID="$(cat "${RUN_DIR}/.start_demo_daemon.pid" 2>/dev/null || true)"
  fi
  if [ -n "${DAEMON_PID}" ]; then
    kill "${DAEMON_PID}" 2>/dev/null || true
  fi
  pkill -f "python insights_cli.py serve --host 127.0.0.1 --port ${PORT}" 2>/dev/null || true
  if [ -n "${CACHE_BACKUP}" ] && [ -d "${CACHE_BACKUP}" ]; then
    rm -rf "${CACHE_DIR}"
    mkdir -p "$(dirname "${CACHE_DIR}")"
    mv "${CACHE_BACKUP}" "${CACHE_DIR}"
  else
    rm -rf "${CACHE_DIR}"
  fi
  if [ -n "${WORKDIR}" ] && [ -d "${WORKDIR}" ]; then
    rm -rf "${WORKDIR}"
  fi
}

prepare_workspace() {
  WORKDIR="$(mktemp -d "/tmp/start-${START_PROVIDER}.XXXXXX")"
  RUN_DIR="${WORKDIR}/demo_codes"
  ENV_FILE="${RUN_DIR}/.env"
  COACH_STDOUT_DIR="${WORKDIR}/coach_raw"
  mkdir -p "${COACH_STDOUT_DIR}"
  rsync -a \
    --exclude '.venv' \
    --exclude '.pytest_cache' \
    --exclude '__pycache__' \
    --exclude '.coverage' \
    --exclude 'runtime' \
    --exclude 'runtime-live' \
    --exclude 'runtime-smoke' \
    --exclude 'runtime-web' \
    "${SOURCE_DIR}/" "${RUN_DIR}/"
}

prepare_cache_backup() {
  if [ -d "${CACHE_DIR}" ]; then
    CACHE_BACKUP="${WORKDIR}/cache_backup"
    mkdir -p "$(dirname "${CACHE_BACKUP}")"
    mv "${CACHE_DIR}" "${CACHE_BACKUP}"
  fi
}

print_dry_run() {
  cat <<EOF
DRY RUN
provider=${START_PROVIDER}
日志文件=${LOG_DIR}/start_${START_PROVIDER}.latest.txt
隔离目录=/tmp/start-${START_PROVIDER}.XXXXXX/demo_codes
固定步骤数=${#STEP_TITLES[@]}
自动模式=$([ "${AUTO_APPROVE}" -eq 1 ] && printf '是' || printf '否')
EOF
}

coach_prompt_file() {
  printf '%s/coach_step_%02d.prompt.txt' "${WORKDIR}" "$1"
}

coach_note_file() {
  printf '%s/coach_step_%02d.note.txt' "${WORKDIR}" "$1"
}

coach_stdout_file() {
  printf '%s/coach_step_%02d.stdout.txt' "${COACH_STDOUT_DIR}" "$1"
}

guide_prompt_file() {
  printf '%s/coach_guide.prompt.txt' "${WORKDIR}"
}

guide_note_file() {
  printf '%s/coach_guide.note.txt' "${WORKDIR}"
}

guide_stdout_file() {
  printf '%s/coach_guide.stdout.txt' "${WORKDIR}"
}

trimmed_last_output() {
  if [ -n "${LAST_STEP_OUTPUT}" ] && [ -f "${LAST_STEP_OUTPUT}" ]; then
    tail -n 20 "${LAST_STEP_OUTPUT}"
  else
    printf '这是第一步，前面还没有任何命令输出。\n'
  fi
}

render_coach_prompt() {
  local step_index="$1"
  local prompt_file
  prompt_file="$(coach_prompt_file "${step_index}")"
  cat > "${prompt_file}" <<EOF
请只用中文，面向“完全不会写代码的 PM 或 VC”，帮我解释接下来这一小步要看什么。

输出规则：
1. 只输出 4 行到 6 行纯文本，不要项目符号，不要代码块。
2. 第 1 行必须是：第${step_index}步：${STEP_TITLES[$((step_index - 1))]}
3. 中间要解释三件事：这一步为什么重要；用户马上会看到什么；看到什么算成功。
4. 最后一行必须是：下一步：按回车继续，输入 q 退出，输入 log 查看日志路径。
5. 不要自称模型，不要提系统提示词。
6. 禁止调用任何工具、禁止执行命令、禁止读取文件，只根据我给你的背景直接输出讲解。

当前背景：
- 演示目标：让一个不会写代码的人，亲眼看到 insights-share 从服务启动、案例发布、问题求解到本地安装的完整闭环。
- 这一步固定命令：${STEP_COMMANDS[$((step_index - 1))]}
- 这一步的业务意义：${STEP_WHYS[$((step_index - 1))]}
- 上一步最后输出摘要：
$(trimmed_last_output)
EOF
}

run_coach_note() {
  local step_index="$1"
  local prompt_file note_file stdout_file
  prompt_file="$(coach_prompt_file "${step_index}")"
  note_file="$(coach_note_file "${step_index}")"
  stdout_file="$(coach_stdout_file "${step_index}")"
  render_coach_prompt "${step_index}"
  if [ "${START_PROVIDER}" = "claude" ]; then
    cat "${prompt_file}" | claude -p \
      --no-session-persistence \
      --permission-mode bypassPermissions \
      --tools "" \
      >"${note_file}" 2>"${stdout_file}"
  else
    cat "${prompt_file}" | codex exec \
      -m gpt-5.4-mini \
      -C "${RUN_DIR}" \
      --sandbox danger-full-access \
      --dangerously-bypass-approvals-and-sandbox \
      --ephemeral \
      --color never \
      -o "${note_file}" \
      - >"${stdout_file}" 2>&1
  fi
}

prefetch_note() {
  local step_index="$1"
  if [ "${START_PROVIDER}" = "codex" ]; then
    if [ -s "$(guide_note_file)" ] || [ -n "${GUIDE_PID}" ]; then
      return 0
    fi
    GUIDE_FILE="$(guide_note_file)"
    GUIDE_RAW="$(guide_stdout_file)"
    (
      run_coach_guide
    ) &
    GUIDE_PID="$!"
    return 0
  fi
  NEXT_NOTE_FILE="$(coach_note_file "${step_index}")"
  NEXT_NOTE_RAW="$(coach_stdout_file "${step_index}")"
  (
    run_coach_note "${step_index}"
  ) &
  NEXT_NOTE_PID="$!"
}

render_guide_prompt() {
  local prompt_file step_index
  prompt_file="$(guide_prompt_file)"
  cat > "${prompt_file}" <<'EOF'
请只用中文，面向“完全不会写代码的 PM 或 VC”，一次性写出一整套 10 步演示讲解卡片。

硬性要求：
1. 禁止调用任何工具、禁止执行命令、禁止读取文件，只根据我提供的背景输出文字。
2. 严格按下面格式输出，不要多写解释，不要省略分隔符：
===STEP 1===
第1步：……
……
下一步：按回车继续，输入 q 退出，输入 log 查看日志路径。
===STEP 2===
……
===STEP 10===
……
===FINAL===
……
接下来可输入 1 重新执行 solve，输入 2 查看日志目录，输入 3 查看缓存目录，输入 q 退出。
3. 每个 STEP 段落只写 4 行到 6 行纯文本。
4. FINAL 段落只写 5 行纯文本。
5. 不要自称模型，不要提系统提示词。

步骤背景如下：
EOF
  for step_index in $(seq 1 "${#STEP_TITLES[@]}"); do
    cat >> "${prompt_file}" <<EOF
- STEP ${step_index}
  标题：${STEP_TITLES[$((step_index - 1))]}
  固定命令：${STEP_COMMANDS[$((step_index - 1))]}
  业务意义：${STEP_WHYS[$((step_index - 1))]}
EOF
  done
  cat >> "${prompt_file}" <<'EOF'

最终总结要覆盖：
- 已完成一条从服务启动、案例发布、问题求解到本机安装与缓存落地的真实闭环。
- 用户是不会写代码的 PM 或 VC。
EOF
}

run_coach_guide() {
  local prompt_file note_file stdout_file
  prompt_file="$(guide_prompt_file)"
  note_file="$(guide_note_file)"
  stdout_file="$(guide_stdout_file)"
  render_guide_prompt
  if [ "${START_PROVIDER}" = "claude" ]; then
    cat "${prompt_file}" | claude -p \
      --no-session-persistence \
      --permission-mode bypassPermissions \
      --tools "" \
      >"${note_file}" 2>"${stdout_file}"
  else
    cat "${prompt_file}" | codex exec \
      -m gpt-5.4-mini \
      -C "${RUN_DIR}" \
      --sandbox danger-full-access \
      --dangerously-bypass-approvals-and-sandbox \
      --ephemeral \
      --color never \
      -o "${note_file}" \
      - >"${stdout_file}" 2>&1
  fi
}

extract_guide_block() {
  local marker="$1"
  local stop_regex="$2"
  if [ ! -f "$(guide_note_file)" ]; then
    return 1
  fi
  awk -v marker="${marker}" -v stop_regex="${stop_regex}" '
    $0 == marker {capture=1; next}
    capture && $0 ~ stop_regex {exit}
    capture {print}
  ' "$(guide_note_file)"
}

builtin_note() {
  local step_index="$1"
  cat <<EOF
第${step_index}步：${STEP_TITLES[$((step_index - 1))]}
这一步的目的很简单：${STEP_WHYS[$((step_index - 1))]}
你马上会看到脚本执行一条固定命令，并把原始结果完整打印出来。
只要命令退出成功，而且输出和这一步的目标一致，就说明我们继续往下走是安全的。
下一步：按回车继续，输入 q 退出，输入 log 查看日志路径。
EOF
}

show_note() {
  local step_index="$1"
  local note_ready=0
  local marker
  local block=""
  if [ "${START_PROVIDER}" = "codex" ]; then
    if [ -n "${GUIDE_PID}" ]; then
      if wait "${GUIDE_PID}"; then
        note_ready=1
      fi
      GUIDE_PID=""
    elif [ -s "$(guide_note_file)" ]; then
      note_ready=1
    fi
    marker=$(printf '===STEP %d===' "${step_index}")
    if [ "${note_ready}" -eq 1 ]; then
      block="$(extract_guide_block "${marker}" '^===' || true)"
    fi
    if [ -n "${block}" ]; then
      printf '%s\n' "${block}"
      return 0
    fi
    builtin_note "${step_index}"
    if [ -n "${GUIDE_RAW}" ] && [ -f "${GUIDE_RAW}" ]; then
      log "Codex 教练卡片生成失败，已回退到内置说明：${GUIDE_RAW}"
    fi
    return 0
  fi
  if [ -n "${NEXT_NOTE_PID}" ]; then
    if wait "${NEXT_NOTE_PID}"; then
      if [ -s "${NEXT_NOTE_FILE}" ]; then
        note_ready=1
      fi
    fi
  fi
  if [ "${note_ready}" -eq 1 ]; then
    sed -n '1,8p' "${NEXT_NOTE_FILE}"
  else
    builtin_note "${step_index}"
    if [ -n "${NEXT_NOTE_RAW}" ] && [ -f "${NEXT_NOTE_RAW}" ]; then
      log "后台讲解生成失败，已回退到内置说明：${NEXT_NOTE_RAW}"
    fi
  fi
  NEXT_NOTE_PID=""
  NEXT_NOTE_FILE=""
  NEXT_NOTE_RAW=""
}

wait_for_user() {
  if [ "${AUTO_APPROVE}" -eq 1 ]; then
    printf '[自动模式] 继续执行下一步。\n'
    return 0
  fi
  while true; do
    printf '你的选择：'
    IFS= read -r answer || answer="q"
    case "${answer}" in
      "")
        return 0
        ;;
      q|quit|exit)
        printf '你选择了退出，脚本会收尾并关闭临时服务。\n'
        return 1
        ;;
      log)
        printf '日志文件：%s\n' "${LOG_FILE}"
        printf '隔离副本：%s\n' "${RUN_DIR}"
        ;;
      *)
        printf '只支持三种输入：直接回车继续，q 退出，log 查看路径。\n'
        ;;
    esac
  done
}

run_step_command() {
  local command_string="$1"
  (
    cd "${RUN_DIR}"
    set -a
    # shellcheck disable=SC1091
    source "${ENV_FILE}"
    set +a
    bash -lc "${command_string}"
  )
}

remember_step_status() {
  local step_index="$1"
  case "${step_index}" in
    4)
      HEALTHZ_OK=1
      ;;
    6)
      PUBLISH_GOOD_OK=1
      ;;
    7)
      PUBLISH_BAD_OK=1
      ;;
    8)
      SOLVE_OK=1
      ;;
    9)
      INSTALL_OK=1
      ;;
    10)
      CACHE_OK=1
      ;;
  esac
}

run_step() {
  local step_index="$1"
  local title command_string output_file
  title="${STEP_TITLES[$((step_index - 1))]}"
  command_string="${STEP_COMMANDS[$((step_index - 1))]}"
  output_file="${WORKDIR}/step_${step_index}.command.txt"
  CURRENT_STEP="${step_index}"

  printf '\n'
  show_note "${step_index}"
  if ! wait_for_user; then
    return 1
  fi

  printf '固定命令：%s\n' "${command_string}"
  if run_step_command "${command_string}" >"${output_file}" 2>&1; then
    cat "${output_file}"
    LAST_STEP_OUTPUT="${output_file}"
    remember_step_status "${step_index}"
    if [ "${step_index}" -eq 3 ] && [ -f "${RUN_DIR}/.start_demo_daemon.pid" ]; then
      DAEMON_PID="$(cat "${RUN_DIR}/.start_demo_daemon.pid" 2>/dev/null || true)"
    fi
    printf '这一步完成：%s\n' "${title}"
    return 0
  fi

  cat "${output_file}"
  LAST_STEP_OUTPUT="${output_file}"
  printf '这一步失败：%s\n' "${title}"
  printf '请先查看上面的原始输出；日志文件也已经保存到 %s\n' "${LOG_FILE}"
  return 1
}

render_final_note_prompt() {
  local prompt_file
  prompt_file="${WORKDIR}/coach_final.prompt.txt"
  cat > "${prompt_file}" <<EOF
请只用中文，面向不会写代码的 PM 或 VC，总结一次 insights-share CLI 演示。

输出要求：
1. 只输出 5 行纯文本。
2. 第 1 行说明我们已经跑完整个真实闭环。
3. 第 2 到第 4 行分别概括：看到的业务价值、最关键的成功证据、下一次可以继续做什么。
4. 最后一行必须是：接下来可输入 1 重新执行 solve，输入 2 查看日志目录，输入 3 查看缓存目录，输入 q 退出。
5. 禁止调用任何工具、禁止执行命令、禁止读取文件，只根据给定状态直接输出总结。

成功状态：
- healthz=${HEALTHZ_OK}
- publish_good=${PUBLISH_GOOD_OK}
- publish_bad=${PUBLISH_BAD_OK}
- solve=${SOLVE_OK}
- install=${INSTALL_OK}
- cache=${CACHE_OK}
EOF
}

show_final_note() {
  local prompt_file note_file raw_file
  local block=""
  if [ "${START_PROVIDER}" = "codex" ]; then
    if [ -n "${GUIDE_PID}" ]; then
      wait "${GUIDE_PID}" 2>/dev/null || true
      GUIDE_PID=""
    fi
    block="$(extract_guide_block '===FINAL===' '^===DO_NOT_STOP===' || true)"
    if [ -n "${block}" ]; then
      printf '%s\n' "${block}"
      return 0
    fi
  fi
  prompt_file="${WORKDIR}/coach_final.prompt.txt"
  note_file="${WORKDIR}/coach_final.note.txt"
  raw_file="${WORKDIR}/coach_final.stdout.txt"
  render_final_note_prompt
  if [ "${START_PROVIDER}" = "claude" ]; then
    if cat "${prompt_file}" | claude -p \
      --no-session-persistence \
      --permission-mode bypassPermissions \
      --tools "" \
      >"${note_file}" 2>"${raw_file}"; then
      sed -n '1,8p' "${note_file}"
      return 0
    fi
  else
    if cat "${prompt_file}" | codex exec \
      -m gpt-5.4-mini \
      -C "${RUN_DIR}" \
      --sandbox danger-full-access \
      --dangerously-bypass-approvals-and-sandbox \
      --ephemeral \
      --color never \
      -o "${note_file}" \
      - >"${raw_file}" 2>&1; then
      sed -n '1,8p' "${note_file}"
      return 0
    fi
  fi
  cat <<EOF
完整真实闭环已经跑完，你现在看到的是脚本的内置总结。
业务价值：用户不用改代码，只要接入 wiki，就能复用团队经验。
成功证据：healthz、publish、solve、install、cache 五个信号都已经在日志里留下了原始输出。
下一次可以继续做的事：换一个问题重跑 solve，或者拿日志给 PM/VC 做演示。
接下来可输入 1 重新执行 solve，输入 2 查看日志目录，输入 3 查看缓存目录，输入 q 退出。
EOF
}

interactive_after_demo() {
  while true; do
    printf '你的选择：'
    IFS= read -r answer || answer="q"
    case "${answer}" in
      1)
        printf '重新执行 solve 这一步。\n'
        if ! run_step 8; then
          return 1
        fi
        ;;
      2)
        ls -la "${LOG_DIR}"
        ;;
      3)
        ls -la "${CACHE_DIR}" 2>/dev/null || printf '缓存目录当前不存在。\n'
        ;;
      q|quit|exit)
        printf '演示结束，开始清理临时资源。\n'
        return 0
        ;;
      *)
        printf '只支持 1、2、3、q。\n'
        ;;
    esac
  done
}

print_result_lines() {
  printf '\n结果摘要：\n'
  printf 'RESULT healthz=%s\n' "$([ "${HEALTHZ_OK}" -eq 1 ] && printf 'ok' || printf 'fail')"
  printf 'RESULT publish_good=%s\n' "$([ "${PUBLISH_GOOD_OK}" -eq 1 ] && printf 'ok' || printf 'fail')"
  printf 'RESULT publish_bad=%s\n' "$([ "${PUBLISH_BAD_OK}" -eq 1 ] && printf 'ok' || printf 'fail')"
  printf 'RESULT solve=%s\n' "$([ "${SOLVE_OK}" -eq 1 ] && printf 'ok' || printf 'fail')"
  printf 'RESULT install=%s\n' "$([ "${INSTALL_OK}" -eq 1 ] && printf 'ok' || printf 'fail')"
  printf 'RESULT cache=%s\n' "$([ "${CACHE_OK}" -eq 1 ] && printf 'ok' || printf 'fail')"
  printf '日志文件：%s\n' "${LOG_FILE}"
  printf '隔离副本：%s\n' "${RUN_DIR}"
}

main() {
  if [ "${START_PROVIDER}" = "claude" ]; then
    PROVIDER_NAME="Claude"
  else
    PROVIDER_NAME="Codex"
  fi

  for arg in "$@"; do
    case "${arg}" in
      --auto-approve)
        AUTO_APPROVE=1
        ;;
      --dry-run)
        DRY_RUN=1
        ;;
      -h|--help)
        usage
        exit 0
        ;;
      *)
        printf '未知参数：%s\n' "${arg}" >&2
        usage >&2
        exit 2
        ;;
    esac
  done

  if [ "${DRY_RUN}" -eq 1 ]; then
    print_dry_run
    exit 0
  fi

  require_cmd rsync
  require_cmd curl
  require_cmd tmux
  require_cmd "${START_PROVIDER}"

  if [ ! -x "${PYTHON_BIN}" ]; then
    printf '缺少 Python 运行时：%s\n' "${PYTHON_BIN}" >&2
    exit 1
  fi

  prepare_workspace
  prepare_cache_backup
  trap cleanup EXIT

  if [ ! -f "${ENV_FILE}" ]; then
    printf '缺少环境文件：%s\n' "${ENV_FILE}" >&2
    exit 1
  fi

  setup_logging
  log "隔离副本：${RUN_DIR}"
  log "日志文件：${LOG_FILE}"
  log "当前模式：$([ "${AUTO_APPROVE}" -eq 1 ] && printf '自动' || printf '手动')"
}

main_loop() {
  local step_index next_step
  prefetch_note 1
  for step_index in $(seq 1 "${#STEP_TITLES[@]}"); do
    if ! run_step "${step_index}"; then
      print_result_lines
      return 1
    fi
    next_step=$((step_index + 1))
    if [ "${next_step}" -le "${#STEP_TITLES[@]}" ]; then
      prefetch_note "${next_step}"
    fi
  done

  printf '\n'
  show_final_note
  print_result_lines
  if [ "${AUTO_APPROVE}" -eq 0 ]; then
    interactive_after_demo
  fi
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
  main "$@"
  main_loop
fi
