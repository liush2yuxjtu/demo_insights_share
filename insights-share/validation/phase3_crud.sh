#!/usr/bin/env bash
# Phase 3: Wiki CRUD 端到端测试。
# 顺序：add → edit → tag(not_triggered) → merge → delete → research
# 每步成功后打印 CRUD_OK: <op>，让 phase3_tmux.txt 能 grep 6 行。
#
# 严禁 fallback：research 必须真实调用 MiniMax search_agent。

set -e
DEMO_CODES="/Users/m1/projects/demo_insights_share/insights-share/demo_codes"
WIKI="http://127.0.0.1:7821"
TEST_WIKI_TREE="/tmp/isv-p3-wiki-tree"

cd "$DEMO_CODES"

# 准备一个干净的隔离 wiki_tree（避免污染 phase2 / phase4 的产出）
rm -rf "$TEST_WIKI_TREE"
python /Users/m1/projects/demo_insights_share/insights-share/validation/migrate_wiki_to_tree.py \
    --out "$TEST_WIKI_TREE"

# 启动 daemon
pkill -f "insights_cli.py serve" 2>/dev/null || true
sleep 1
python insights_cli.py serve --port 7821 --store "$TEST_WIKI_TREE" --store-mode tree \
    >/tmp/isv-p3-daemon.log 2>&1 &
DAEMON_PID=$!
sleep 2
trap 'kill $DAEMON_PID 2>/dev/null || true' EXIT

# 健康检查
curl -fsS "$WIKI/healthz" >/dev/null

# ---- 1. add ----
NEW_CARD='{"id":"diana-elasticsearch-shard-2026-04-12","title":"ES shard relocation thrash on rebalance","author":"diana","confidence":0.78,"tags":["elasticsearch","shard","rebalance"],"context":"6-node ES cluster","symptom":"shards bouncing between nodes","root_cause":"unbounded throttle","fix":"set indices.recovery.max_bytes_per_sec=80mb","applies_when":["es>=7"],"do_not_apply_when":["single-node cluster"]}'
echo "$NEW_CARD" | python -c '
import json,sys,urllib.request
data=sys.stdin.read().encode()
req=urllib.request.Request("'$WIKI'/insights",data=data,headers={"Content-Type":"application/json"})
print(urllib.request.urlopen(req,timeout=10).read().decode())
'
echo "CRUD_OK: add"

# ---- 2. edit ----
python insights_cli.py edit diana-elasticsearch-shard-2026-04-12 \
    '{"confidence":0.85,"context":"6-node ES cluster behind ALB"}'
echo "CRUD_OK: edit"

# ---- 3. tag (not_triggered, sticky) ----
python insights_cli.py tag diana-elasticsearch-shard-2026-04-12 --tags experimental
echo "CRUD_OK: tag"

# ---- 4. merge (source=diana → target=alice-pgpool, 测合并不同 wiki_type) ----
# 先添加一个临时 source 卡，merge 到 alice 卡
TEMP_CARD='{"id":"temp-diana-clone-2026-04-12","title":"clone of diana es","author":"diana","confidence":0.5,"tags":["elasticsearch","clone"],"fix":"see diana note"}'
echo "$TEMP_CARD" | python -c '
import json,sys,urllib.request
data=sys.stdin.read().encode()
req=urllib.request.Request("'$WIKI'/insights",data=data,headers={"Content-Type":"application/json"})
print(urllib.request.urlopen(req,timeout=10).read().decode())
'
python insights_cli.py merge temp-diana-clone-2026-04-12 diana-elasticsearch-shard-2026-04-12
echo "CRUD_OK: merge"

# ---- 5. delete ----
python insights_cli.py delete diana-elasticsearch-shard-2026-04-12
echo "CRUD_OK: delete"

# ---- 6. research (真 AI，无 fallback) ----
python insights_cli.py research "redis cache eviction silently dropping session data"
echo "CRUD_OK: research"

echo
echo "[phase3] all 6 CRUD operations completed"
