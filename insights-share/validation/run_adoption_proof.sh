#!/usr/bin/env bash
# AP-1 adoption proof:
#   1. clean-machine install can write an isolated ~/.cache/insights-share
#   2. first relevant hit cites the canonical Alice card
#   3. first publish stores both good and bad seed cards
#   4. day-2 return works from installed config without passing --wiki

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
SOURCE_DIR="${REPO_ROOT}/insights-share/demo_codes"
LOG_DIR="${REPO_ROOT}/insights-share/validation/reports/deliverables"
PORT="${PORT:-18821}"
WIKI_URL="http://127.0.0.1:${PORT}"
PROBLEM="Our checkout API is timing out, postgres is rejecting new connections during the lunch spike"
PYTHON_BIN="${PYTHON_BIN:-${SOURCE_DIR}/.venv/bin/python}"

WORKDIR=""
HOME_DIR=""
STORE_DIR=""
DAEMON_LOG=""
DAEMON_PID=""
REPORT_TXT="${LOG_DIR}/adoption_proof_latest.txt"
REPORT_JSON="${LOG_DIR}/adoption_proof_latest.json"

log() {
  printf '[adoption-proof] %s\n' "$*"
}

choose_python() {
  if [ -x "${PYTHON_BIN}" ]; then
    printf '%s\n' "${PYTHON_BIN}"
    return 0
  fi
  if command -v python3 >/dev/null 2>&1; then
    printf '%s\n' "$(command -v python3)"
    return 0
  fi
  log "missing Python runtime"
  return 127
}

cleanup() {
  if [ -n "${DAEMON_PID}" ]; then
    kill "${DAEMON_PID}" 2>/dev/null || true
  fi
  pkill -f "insights_cli.py serve --host 127.0.0.1 --port ${PORT}" 2>/dev/null || true
  if [ -n "${WORKDIR}" ] && [ -d "${WORKDIR}" ]; then
    rm -rf "${WORKDIR}"
  fi
}

run_cli() {
  (cd "${SOURCE_DIR}" && HOME="${HOME_DIR}" "${PYTHON_BIN}" insights_cli.py "$@")
}

assert_contains() {
  local label="$1"
  local haystack="$2"
  local needle="$3"
  if [[ "${haystack}" != *"${needle}"* ]]; then
    log "FAIL ${label}: expected to find ${needle}"
    printf '%s\n' "${haystack}"
    return 1
  fi
}

wait_for_healthz() {
  local attempt
  for attempt in 1 2 3 4 5 6 7 8 9 10; do
    if curl -fsS "${WIKI_URL}/healthz" >/dev/null 2>&1; then
      return 0
    fi
    sleep 1
  done
  log "daemon failed to become healthy"
  tail -n 80 "${DAEMON_LOG}" 2>/dev/null || true
  return 1
}

write_report() {
  local checked_at="$1"
  cat > "${REPORT_JSON}" <<EOF
{
  "pass": true,
  "checked_at": "${checked_at}",
  "signals": {
    "clean_machine_install": "ok",
    "first_relevant_hit": "alice-pgpool-2026-04-10",
    "first_publish": "alice-pgpool-2026-04-10,bob-pgpool-bad-2026-04-12",
    "day_2_return": "ok"
  },
  "wiki_url": "${WIKI_URL}",
  "report": "${REPORT_TXT}"
}
EOF
}

main() {
  mkdir -p "${LOG_DIR}"
  exec > >(tee "${REPORT_TXT}") 2>&1

  PYTHON_BIN="$(choose_python)"
  WORKDIR="$(mktemp -d "/tmp/insights-adoption-proof.XXXXXX")"
  HOME_DIR="${WORKDIR}/home"
  STORE_DIR="${WORKDIR}/wiki_tree"
  DAEMON_LOG="${WORKDIR}/daemon.log"
  mkdir -p "${HOME_DIR}" "${STORE_DIR}"
  trap cleanup EXIT

  log "workdir=${WORKDIR}"
  log "home=${HOME_DIR}"
  log "python=${PYTHON_BIN}"

  if [ -e "${HOME_DIR}/.cache/insights-share" ]; then
    log "FAIL clean machine home already has insights cache"
    return 1
  fi

  log "start isolated daemon on ${WIKI_URL}"
  (cd "${SOURCE_DIR}" && HOME="${HOME_DIR}" "${PYTHON_BIN}" insights_cli.py serve \
    --host 127.0.0.1 \
    --port "${PORT}" \
    --store "${STORE_DIR}" \
    --store-mode tree \
    > "${DAEMON_LOG}" 2>&1 & echo $! > "${WORKDIR}/daemon.pid")
  DAEMON_PID="$(cat "${WORKDIR}/daemon.pid")"
  wait_for_healthz

  log "assert initial wiki is empty"
  initial_list="$(run_cli list --wiki "${WIKI_URL}")"
  assert_contains "initial list" "${initial_list}" "(no insights yet)"

  log "first publish: Alice good + Bob bad"
  publish_good="$(run_cli publish seeds/alice_pgpool.json --wiki "${WIKI_URL}")"
  publish_bad="$(run_cli publish seeds/bob_pgpool_bad.json --wiki "${WIKI_URL}")"
  assert_contains "publish good" "${publish_good}" "published alice-pgpool-2026-04-10"
  assert_contains "publish bad" "${publish_bad}" "published bob-pgpool-bad-2026-04-12"

  log "first relevant hit / cite"
  first_solve="$(run_cli solve "${PROBLEM}" --wiki "${WIKI_URL}" --no-ai)"
  assert_contains "first relevant hit" "${first_solve}" "hot-loaded alice-pgpool-2026-04-10"
  assert_contains "first relevant fix" "${first_solve}" "idle_in_transaction_session_timeout"

  log "clean-machine install into isolated HOME"
  install_output="$(run_cli wiki-install --server "${WIKI_URL}")"
  assert_contains "wiki install" "${install_output}" "install ok server=${WIKI_URL}"
  assert_contains "wiki install cache count" "${install_output}" "cached=2 cards"

  cache_dir="${HOME_DIR}/.cache/insights-share"
  test -f "${cache_dir}/config.json"
  test -f "${cache_dir}/trusted_keys.json"
  test -f "${cache_dir}/alice-pgpool-2026-04-10.json"
  test -f "${cache_dir}/bob-pgpool-bad-2026-04-12.json"

  log "day-2 return: solve uses installed config without --wiki"
  mkdir -p "${WORKDIR}/day2"
  day2_solve="$(cd "${WORKDIR}/day2" && HOME="${HOME_DIR}" "${PYTHON_BIN}" "${SOURCE_DIR}/insights_cli.py" solve "${PROBLEM}" --no-ai)"
  assert_contains "day-2 return" "${day2_solve}" "hot-loaded alice-pgpool-2026-04-10"

  write_report "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  log "PASS clean_machine_install=ok first_relevant_hit=alice-pgpool-2026-04-10 first_publish=2 day_2_return=ok"
  log "report=${REPORT_JSON}"
}

main "$@"
