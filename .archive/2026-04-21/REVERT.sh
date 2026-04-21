#!/bin/bash
# 一键回滚本次归档
# 遍历 manifest-tier{1,2,3}.txt 把镜像路径 git mv 回原位
set -euo pipefail
ARCHIVE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(git -C "$ARCHIVE" rev-parse --show-toplevel)"
cd "$ROOT"

revert_one() {
  local manifest="$1"
  [ -f "$manifest" ] || { echo "skip: $manifest 不存在"; return 0; }
  while IFS= read -r line; do
    [ -z "$line" ] && continue
    src=".archive/2026-04-21/$line"
    [ -e "$src" ] || continue
    mkdir -p "$(dirname "$line")"
    git mv "$src" "$line"
  done < "$manifest"
}

revert_one "$ARCHIVE/manifest-tier1.txt"
revert_one "$ARCHIVE/manifest-tier2.txt"
revert_one "$ARCHIVE/manifest-tier3.txt"

echo "Revert done. Run start.demo.sh to verify."
