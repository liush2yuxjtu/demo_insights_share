#!/usr/bin/env bash
set -euo pipefail

START_PROVIDER="claude"
source "$(cd "$(dirname "$0")" && pwd)/insights-share/validation/start_demo_driver.sh"

main "$@"
main_loop
