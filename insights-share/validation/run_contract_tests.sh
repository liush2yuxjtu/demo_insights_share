#!/usr/bin/env bash
# P3 合同测试入口：不依赖全局 pytest，也不复用 demo_codes/.venv。

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-}"
TEST_VENV="$SCRIPT_DIR/.test-venv"

DEFAULT_TESTS=(
  "insights-share/validation/test_start_scripts.py"
  "insights-share/validation/test_plugin_contract.py"
  "insights-share/validation/test_release_package.py"
  "insights-share/validation/test_adoption_proof.py"
  "insights-share/validation/test_ci_gate.py"
)

choose_python() {
  if [[ -n "$PYTHON_BIN" ]]; then
    printf '%s\n' "$PYTHON_BIN"
    return
  fi
  for candidate in python3.11 python3.12 python3.13 python3; do
    if command -v "$candidate" >/dev/null 2>&1; then
      printf '%s\n' "$candidate"
      return
    fi
  done
  echo "缺少可用 Python，请安装 Python 3.11+" >&2
  return 1
}

run_with_uv() {
  local python_cmd="$1"
  shift
  command -v uv >/dev/null 2>&1 || return 127
  uv run --python "$python_cmd" --with pytest -- python -m pytest "$@"
}

run_with_test_venv() {
  local python_cmd="$1"
  shift
  if [[ ! -x "$TEST_VENV/bin/python" ]]; then
    "$python_cmd" -m venv "$TEST_VENV"
    "$TEST_VENV/bin/python" -m pip install --upgrade pip >/dev/null
    "$TEST_VENV/bin/python" -m pip install pytest >/dev/null
  fi
  "$TEST_VENV/bin/python" -m pytest "$@"
}

main() {
  cd "$REPO_ROOT"

  local python_cmd
  python_cmd="$(choose_python)"

  local args=("-q")
  if [[ "$#" -gt 0 ]]; then
    args+=("$@")
  else
    args+=("${DEFAULT_TESTS[@]}")
  fi

  if run_with_uv "$python_cmd" "${args[@]}"; then
    return 0
  fi

  echo "[run_contract_tests] uv 不可用或执行失败，改用 $TEST_VENV" >&2
  run_with_test_venv "$python_cmd" "${args[@]}"
}

main "$@"
