#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
OUT_DIR="${REPO_ROOT}/insights-share/validation/reports/deliverables"
mkdir -p "${OUT_DIR}"

run_one() {
  local provider="$1"
  local script_path="${REPO_ROOT}/start.${provider}.sh"
  local session="start_${provider}_smoke"
  local raw="${OUT_DIR}/tmux_${provider}_smoke.txt"
  local timeout_sec=900
  local elapsed=0

  rm -f "${raw}"
  tmux kill-session -t "${session}" 2>/dev/null || true
  tmux new-session -d -s "${session}" -x 220 -y 60
  tmux pipe-pane -o -t "${session}" "cat > ${raw}"
  tmux send-keys -t "${session}" "cd ${REPO_ROOT}" Enter
  tmux send-keys -t "${session}" "bash ${script_path} --auto-approve; printf '\\n__SCRIPT_DONE__:%s\\n' \$?" Enter

  while [ "${elapsed}" -lt "${timeout_sec}" ]; do
    sleep 5
    elapsed=$((elapsed + 5))
    if [ -f "${raw}" ] && grep -q "__SCRIPT_DONE__:0" "${raw}" 2>/dev/null; then
      break
    fi
  done

  tmux capture-pane -pt "${session}" -S -2000 >> "${raw}" 2>/dev/null || true
  tmux kill-session -t "${session}" 2>/dev/null || true

  if ! grep -q "__SCRIPT_DONE__:0" "${raw}"; then
    printf 'tmux smoke failed: %s 未在 %s 秒内成功结束\n' "${provider}" "${timeout_sec}" >&2
    return 1
  fi

  grep -q "RESULT healthz=ok" "${raw}"
  grep -q "RESULT publish_good=ok" "${raw}"
  grep -q "RESULT publish_bad=ok" "${raw}"
  grep -q "RESULT solve=ok" "${raw}"
  grep -q "RESULT install=ok" "${raw}"
  grep -q "RESULT cache=ok" "${raw}"

  printf 'tmux smoke pass: %s -> %s\n' "${provider}" "${raw}"
}

run_one "claude"
run_one "codex"
