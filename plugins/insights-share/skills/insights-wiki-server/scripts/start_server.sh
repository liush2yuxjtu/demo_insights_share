#!/usr/bin/env bash
# 启动 insightsd 前台守护进程（tree 模式 + 0.0.0.0:7821）
set -euo pipefail
cd "$(dirname "$0")/../../../.."
[ -d .venv ] && source .venv/bin/activate
exec python insights_cli.py serve --host 0.0.0.0 --port 7821 --store-mode tree
