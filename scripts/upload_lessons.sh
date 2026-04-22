#!/usr/bin/env bash
# 把 staging 抽出的卡片按 mapper 转 daemon schema 并上传。
set -uo pipefail

STAGING="${1:-/tmp/insights_upload_staging}"
DAEMON="${2:-http://127.0.0.1:7821}"
PY=/usr/bin/python3
NOPROXY=(--noproxy '127.0.0.1,localhost')

[[ -d "$STAGING" ]] || { echo "FAIL: staging $STAGING 不存在"; exit 1; }

# 1) 列 daemon 已知 topic
KNOWN=$(curl -s "${NOPROXY[@]}" "$DAEMON/topics" \
  | $PY -c "import json,sys;[print(t['id']) for t in json.load(sys.stdin)['topics']]")

for topic_dir in "$STAGING"/*/; do
  [[ -d "$topic_dir" ]] || continue
  topic=$(basename "$topic_dir")
  tid="auto-${topic}"
  if ! grep -qx "$tid" <<<"$KNOWN"; then
    echo "REGISTER topic $tid"
    curl -s "${NOPROXY[@]}" -X POST "$DAEMON/topics" \
      -H "Content-Type: application/json" \
      -d "{\"id\":\"$tid\",\"title\":\"自动抽取: $topic\",\"tags\":[\"auto-extracted\",\"$topic\"],\"created_by\":\"extract_lessons.py\",\"wiki_type\":\"$topic\"}" \
      | head -c 200; echo
  fi
done

# 2) 遍历每张卡，mapper + POST /insights
SUCCESS=0; FAIL=0
TMP_RESP=$(mktemp)
for card_json in "$STAGING"/*/*.json; do
  topic=$(basename "$(dirname "$card_json")")
  tid="auto-${topic}"
  payload=$($PY - "$card_json" "$tid" "$topic" <<'PY'
import json,sys
src,tid,topic=sys.argv[1],sys.argv[2],sys.argv[3]
c=json.load(open(src))
mapped={
  "id": c["id"],
  "title": (c.get("scenario") or "")[:60] or "auto-card",
  "author": c.get("author","auto"),
  "confidence": 0.4,
  "tags": c.get("labels",[]),
  "status": "active",
  "topic_id": tid,
  "label": c.get("decision","good"),
  "label_note": (c.get("rationale") or "")[:200],
  "wiki_type": topic,
  "raw_log_type": "export",
}
print(json.dumps(mapped, ensure_ascii=False))
PY
)
  code=$(curl -s "${NOPROXY[@]}" -o "$TMP_RESP" -w "%{http_code}" \
    -X POST "$DAEMON/insights" \
    -H "Content-Type: application/json" -d "$payload")
  body=$(cat "$TMP_RESP")
  if [[ "$code" == "200" || "$code" == "201" ]]; then
    SUCCESS=$((SUCCESS+1))
    echo "OK [$code] $card_json"
  else
    FAIL=$((FAIL+1))
    echo "FAIL [$code] $card_json => $body"
  fi
done
rm -f "$TMP_RESP"
echo "---"
echo "TOTAL success=$SUCCESS fail=$FAIL"
[[ $FAIL -eq 0 && $SUCCESS -gt 0 ]] && exit 0 || exit 2
