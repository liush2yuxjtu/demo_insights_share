#!/usr/bin/env bash
# Deterministic E2E gate for CI/pre-commit style runs.
#
# Always runs:
#   - contract tests
#   - AP-1 adoption proof
#
# Auto-runs when available:
#   - start.demo.sh --dry-run (requires local claude + tmux)
#
# Optional local gates:
#   RUN_HANDOUT_VERIFY=1  npm run handout:verify
#   RUN_TMUX_SMOKE=1      run_start_tmux_smoke.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
RUN_START_DEMO="${RUN_START_DEMO:-auto}"
RUN_HANDOUT_VERIFY="${RUN_HANDOUT_VERIFY:-0}"
RUN_TMUX_SMOKE="${RUN_TMUX_SMOKE:-0}"

log() {
  printf '[ci-gate] %s\n' "$*"
}

have_cmd() {
  command -v "$1" >/dev/null 2>&1
}

should_run_start_demo() {
  case "${RUN_START_DEMO}" in
    1|true|yes|on) return 0 ;;
    0|false|no|off) return 1 ;;
    auto)
      have_cmd claude && have_cmd tmux
      return
      ;;
    *)
      log "invalid RUN_START_DEMO=${RUN_START_DEMO}; expected auto/1/0"
      return 2
      ;;
  esac
}

main() {
  cd "${REPO_ROOT}"

  log "contract tests"
  bash insights-share/validation/run_contract_tests.sh

  log "adoption proof"
  bash insights-share/validation/run_adoption_proof.sh

  if should_run_start_demo; then
    log "start.demo.sh --dry-run"
    bash start.demo.sh --dry-run
  else
    log "skip start.demo.sh --dry-run (requires claude + tmux; set RUN_START_DEMO=1 to require it)"
  fi

  if [ "${RUN_HANDOUT_VERIFY}" = "1" ]; then
    log "handout verify"
    (cd insights-share/validation && npm run handout:verify)
  fi

  if [ "${RUN_TMUX_SMOKE}" = "1" ]; then
    log "tmux smoke"
    bash insights-share/validation/run_start_tmux_smoke.sh
  fi

  log "PASS"
}

main "$@"
