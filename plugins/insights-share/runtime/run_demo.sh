#!/usr/bin/env bash
# insights-share 一键演示脚本。
# 启动本地 insightsd，加载 seeds，清屏后跑 solve。

set -euo pipefail

cd "$(dirname "$0")"

NO_AI_FLAG=""
for arg in "$@"; do
  case "$arg" in
    --no-ai)
      NO_AI_FLAG="--no-ai"
      ;;
    *)
      echo "unknown arg: $arg" >&2
      exit 2
      ;;
  esac
done

YELLOW="\033[33m"
RESET="\033[0m"

if [ ! -f .env ]; then
  cp .env.example .env
  printf "${YELLOW}[warn] .env missing, copied from .env.example — please fill in real tokens${RESET}\n"
fi

if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
pip install -q -r requirements.txt

python insights_cli.py serve --port 7821 >/tmp/insightsd.log 2>&1 &
DAEMON_PID=$!
trap 'kill "$DAEMON_PID" 2>/dev/null || true' EXIT

for _ in 1 2 3 4 5 6 7 8 9 10; do
  if curl -fs http://127.0.0.1:7821/healthz >/dev/null 2>&1; then
    break
  fi
  sleep 0.5
done

if ! curl -fs http://127.0.0.1:7821/healthz >/dev/null 2>&1; then
  echo "insightsd failed to come up, see /tmp/insightsd.log" >&2
  exit 1
fi

python -m insightsd.emitter --stage bootstrap --status ok --source run_demo.sh --message "demo daemon 已启动" >/dev/null 2>&1 || true

for seed in seeds/*.json; do
  python insights_cli.py publish "$seed" >/dev/null
done

python -m insightsd.emitter --stage publish --status ok --source run_demo.sh --message "run_demo.sh 已完成 seed 加载" >/dev/null 2>&1 || true

clear
python insights_cli.py solve \
  "Our checkout API is timing out, postgres is rejecting new connections during the lunch spike" \
  $NO_AI_FLAG

python -m insightsd.emitter --stage summary --status completed --source run_demo.sh --message "run_demo.sh 执行完成" >/dev/null 2>&1 || true

echo
echo "demo finished"
