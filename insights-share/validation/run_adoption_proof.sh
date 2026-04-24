#!/usr/bin/env bash
# AP-1 adoption proof:
#   1. clean-machine install can write an isolated ~/.cache/insights-share
#   2. first relevant hit cites the canonical Alice card
#   3. first publish stores both good and bad seed cards
#   4. day-2 return works from installed config without passing --wiki
# AP-2 adoption proof:
#   5. relevance-lift matrix returns the right top card across multiple incidents

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
RUN_STARTED_AT=""
RUN_STARTED_MS=""
CLEAN_STARTED_AT=""
CLEAN_FINISHED_AT=""
CLEAN_DURATION_MS="0"
PUBLISH_STARTED_AT=""
PUBLISH_FINISHED_AT=""
PUBLISH_DURATION_MS="0"
HIT_STARTED_AT=""
HIT_FINISHED_AT=""
HIT_DURATION_MS="0"
DAY2_STARTED_AT=""
DAY2_FINISHED_AT=""
DAY2_DURATION_MS="0"
AP2_STARTED_AT=""
AP2_FINISHED_AT=""
AP2_DURATION_MS="0"
BASELINE_SEARCH_JSON=""
AP2_MATRIX_JSON_PATH=""
PUBLISH_CELERY_OUTPUT=""
PUBLISH_REDIS_OUTPUT=""
INSTALL_OUTPUT=""
FIRST_SOLVE_OUTPUT=""
DAY2_SOLVE_OUTPUT=""
PUBLISH_GOOD_OUTPUT=""
PUBLISH_BAD_OUTPUT=""

log() {
  printf '[adoption-proof] %s\n' "$*"
}

iso_utc() {
  date -u +%Y-%m-%dT%H:%M:%SZ
}

epoch_ms() {
  "${PYTHON_BIN}" - <<'PY'
import time
print(int(time.time() * 1000))
PY
}

duration_ms() {
  local started_ms="$1"
  local finished_ms="$2"
  printf '%s\n' "$((finished_ms - started_ms))"
}

choose_python() {
  if [ -x "${PYTHON_BIN}" ] && "${PYTHON_BIN}" --version >/dev/null 2>&1; then
    printf '%s\n' "${PYTHON_BIN}"
    return 0
  fi
  local bootstrap_python=""
  for candidate in python3.11 python3.12 python3.13 python3; do
    if command -v "${candidate}" >/dev/null 2>&1; then
      bootstrap_python="$(command -v "${candidate}")"
      break
    fi
  done
  if [ -z "${bootstrap_python}" ]; then
    log "missing Python runtime"
    return 127
  fi
  "${bootstrap_python}" -m venv "${WORKDIR}/.venv"
  "${WORKDIR}/.venv/bin/python" -m pip install --upgrade pip >/dev/null
  "${WORKDIR}/.venv/bin/python" -m pip install -r "${SOURCE_DIR}/requirements.txt" >/dev/null
  printf '%s\n' "${WORKDIR}/.venv/bin/python"
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

search_json() {
  local query="$1"
  local k="${2:-3}"
  QUERY="${query}" K="${k}" WIKI_URL="${WIKI_URL}" "${PYTHON_BIN}" - <<'PY'
from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request

wiki_url = os.environ["WIKI_URL"].rstrip("/")
query = urllib.parse.urlencode({"q": os.environ["QUERY"], "k": os.environ.get("K", "3")})
with urllib.request.urlopen(f"{wiki_url}/search?{query}", timeout=5.0) as resp:
    print(json.dumps(json.loads(resp.read().decode("utf-8")), ensure_ascii=False))
PY
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
  local run_finished_ms
  run_finished_ms="$(epoch_ms)"
  export REPORT_JSON REPORT_TXT checked_at
  export RUN_STARTED_AT RUN_STARTED_MS run_finished_ms
  export REPO_ROOT SOURCE_DIR WORKDIR HOME_DIR STORE_DIR WIKI_URL PYTHON_BIN PROBLEM
  export CLEAN_STARTED_AT CLEAN_FINISHED_AT CLEAN_DURATION_MS INSTALL_OUTPUT
  export PUBLISH_STARTED_AT PUBLISH_FINISHED_AT PUBLISH_DURATION_MS PUBLISH_GOOD_OUTPUT PUBLISH_BAD_OUTPUT
  export HIT_STARTED_AT HIT_FINISHED_AT HIT_DURATION_MS FIRST_SOLVE_OUTPUT
  export DAY2_STARTED_AT DAY2_FINISHED_AT DAY2_DURATION_MS DAY2_SOLVE_OUTPUT
  export AP2_STARTED_AT AP2_FINISHED_AT AP2_DURATION_MS AP2_MATRIX_JSON_PATH BASELINE_SEARCH_JSON
  export PUBLISH_CELERY_OUTPUT PUBLISH_REDIS_OUTPUT
  "${PYTHON_BIN}" - <<'PY'
from __future__ import annotations

import json
import os
import shutil
import urllib.parse
import urllib.request
from pathlib import Path


def env(name: str, default: str = "") -> str:
    return os.environ.get(name, default)


def read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def http_json(url: str) -> dict:
    try:
        with urllib.request.urlopen(url, timeout=5.0) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return {}


def output_excerpt(value: str, limit: int = 800) -> str:
    value = value.strip()
    if len(value) <= limit:
        return value
    return value[:limit] + "...<truncated>"


def read_json_text(value: str) -> dict:
    try:
        data = json.loads(value)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def card_paths(store_dir: Path, card_id: str) -> dict[str, str]:
    slug = card_id.replace("-", "_")
    md_matches = sorted(store_dir.glob(f"*/{slug}.md"))
    raw_matches = sorted(store_dir.glob(f"*/raw/{card_id}.*"))
    return {
        "card_md": str(md_matches[0]) if md_matches else "",
        "raw_log": str(raw_matches[0]) if raw_matches else "",
    }


wiki_url = env("WIKI_URL").rstrip("/")
store_dir = Path(env("STORE_DIR"))
home_dir = Path(env("HOME_DIR"))
cache_dir = home_dir / ".cache" / "insights-share"
artifact_dir = Path(env("REPORT_JSON")).parent / "adoption_proof_artifacts" / "latest"
if artifact_dir.exists():
    shutil.rmtree(artifact_dir)
artifact_dir.mkdir(parents=True, exist_ok=True)
artifact_store_dir = artifact_dir / "wiki_tree"
artifact_cache_dir = artifact_dir / "cache" / "insights-share"
if store_dir.exists():
    shutil.copytree(store_dir, artifact_store_dir)
if cache_dir.exists():
    shutil.copytree(cache_dir, artifact_cache_dir, ignore=shutil.ignore_patterns("signing", "*private*"))
config_path = artifact_cache_dir / "config.json"
trusted_keys_path = artifact_cache_dir / "trusted_keys.json"
problem = env("PROBLEM")

cards_payload = http_json(f"{wiki_url}/insights")
cards = cards_payload.get("cards") or []
card_ids = sorted(str(card.get("id", "")) for card in cards if card.get("id"))
topics_payload = http_json(f"{wiki_url}/topics")
topics = topics_payload.get("topics") or []
topic_examples = http_json(f"{wiki_url}/topics/postgres-pool-exhaustion/examples").get("examples") or []
good_examples = [
    item for item in topic_examples
    if (item.get("label_override") or item.get("label", "good")) == "good"
]
bad_examples = [
    item for item in topic_examples
    if (item.get("label_override") or item.get("label", "good")) == "bad"
]
query = urllib.parse.urlencode({"q": problem, "k": 3})
hits = http_json(f"{wiki_url}/search?{query}").get("hits") or []
top_hit = hits[0] if hits else {}

config = read_json(config_path)
trusted_keys = read_json(trusted_keys_path)
cached_card_ids = sorted(path.stem for path in cache_dir.glob("*.json") if path.name not in {"config.json", "trusted_keys.json"})
baseline_search = read_json_text(env("BASELINE_SEARCH_JSON"))
ap2_matrix = read_json(Path(env("AP2_MATRIX_JSON_PATH"))) if env("AP2_MATRIX_JSON_PATH") else {}

report = {
    "schema_version": "adoption-proof/v2",
    "pass": True,
    "checked_at": env("checked_at"),
    "run": {
        "started_at": env("RUN_STARTED_AT"),
        "finished_at": env("checked_at"),
        "duration_ms": int(env("run_finished_ms", "0")) - int(env("RUN_STARTED_MS", "0")),
    },
    "wiki_url": wiki_url,
    "report": env("REPORT_TXT"),
    "environment": {
        "repo_root": env("REPO_ROOT"),
        "source_dir": env("SOURCE_DIR"),
        "workdir": env("WORKDIR"),
        "home_dir": str(home_dir),
        "store_dir": str(store_dir),
        "python": env("PYTHON_BIN"),
    },
    "artifacts": {
        "dir": str(artifact_dir),
        "wiki_tree": str(artifact_store_dir),
        "cache_dir": str(artifact_cache_dir),
    },
    "legacy_signals": {
        "clean_machine_install": "ok",
        "first_relevant_hit": "alice-pgpool-2026-04-10",
        "first_publish": "alice-pgpool-2026-04-10,bob-pgpool-bad-2026-04-12",
        "day_2_return": "ok",
        "relevance_lift_matrix": "ok",
    },
    "signals": {
        "clean_machine_install": {
            "status": "ok",
            "started_at": env("CLEAN_STARTED_AT"),
            "finished_at": env("CLEAN_FINISHED_AT"),
            "duration_ms": int(env("CLEAN_DURATION_MS", "0")),
            "command": ["insights_cli.py", "wiki-install", "--server", wiki_url],
            "evidence": {
                "isolated_home": str(home_dir),
                "ephemeral_cache_dir": str(cache_dir),
                "cache_dir": str(artifact_cache_dir),
                "config_path": str(config_path),
                "trusted_keys_path": str(trusted_keys_path),
                "config_server_url": config.get("server_url"),
                "cached_card_count": len(cached_card_ids),
                "cached_card_ids": cached_card_ids,
                "trusted_key_count": len(trusted_keys.get("keys") or []),
                "output_excerpt": output_excerpt(env("INSTALL_OUTPUT")),
            },
        },
        "first_relevant_hit": {
            "status": "ok",
            "started_at": env("HIT_STARTED_AT"),
            "finished_at": env("HIT_FINISHED_AT"),
            "duration_ms": int(env("HIT_DURATION_MS", "0")),
            "command": ["insights_cli.py", "solve", problem, "--wiki", wiki_url, "--no-ai"],
            "evidence": {
                "query": problem,
                "top_hit_id": top_hit.get("id"),
                "top_hit_author": top_hit.get("author"),
                "top_hit_score": top_hit.get("score"),
                "hit_count": len(hits),
                "hit_ids": [hit.get("id") for hit in hits if hit.get("id")],
                "required_phrase": "idle_in_transaction_session_timeout",
                "output_excerpt": output_excerpt(env("FIRST_SOLVE_OUTPUT")),
            },
        },
        "first_publish": {
            "status": "ok",
            "started_at": env("PUBLISH_STARTED_AT"),
            "finished_at": env("PUBLISH_FINISHED_AT"),
            "duration_ms": int(env("PUBLISH_DURATION_MS", "0")),
            "commands": [
                ["insights_cli.py", "publish", "seeds/alice_pgpool.json", "--wiki", wiki_url],
                ["insights_cli.py", "publish", "seeds/bob_pgpool_bad.json", "--wiki", wiki_url],
            ],
            "evidence": {
                "published_card_ids": [
                    "alice-pgpool-2026-04-10",
                    "bob-pgpool-bad-2026-04-12",
                ],
                "total_card_count": len(cards),
                "all_card_ids": card_ids,
                "topic_id": "postgres-pool-exhaustion",
                "topic_count": len(topics),
                "topic_example_count": len(topic_examples),
                "good_example_count": len(good_examples),
                "bad_example_count": len(bad_examples),
                "paths": {
                    "alice-pgpool-2026-04-10": card_paths(artifact_store_dir, "alice-pgpool-2026-04-10"),
                    "bob-pgpool-bad-2026-04-12": card_paths(artifact_store_dir, "bob-pgpool-bad-2026-04-12"),
                    "topics_json": str(artifact_store_dir / "topics.json"),
                    "topics_json_exists": (artifact_store_dir / "topics.json").is_file(),
                    "wiki_types_json": str(artifact_store_dir / "wiki_types.json"),
                },
                "outputs": {
                    "good": output_excerpt(env("PUBLISH_GOOD_OUTPUT")),
                    "bad": output_excerpt(env("PUBLISH_BAD_OUTPUT")),
                },
            },
        },
        "day_2_return": {
            "status": "ok",
            "started_at": env("DAY2_STARTED_AT"),
            "finished_at": env("DAY2_FINISHED_AT"),
            "duration_ms": int(env("DAY2_DURATION_MS", "0")),
            "command": ["insights_cli.py", "solve", problem, "--no-ai"],
            "evidence": {
                "cwd": str(Path(env("WORKDIR")) / "day2"),
                "used_installed_config": True,
                "config_path": str(config_path),
                "config_server_url": config.get("server_url"),
                "expected_card_id": "alice-pgpool-2026-04-10",
                "output_excerpt": output_excerpt(env("DAY2_SOLVE_OUTPUT")),
            },
        },
        "relevance_lift_matrix": {
            "status": "ok",
            "started_at": env("AP2_STARTED_AT"),
            "finished_at": env("AP2_FINISHED_AT"),
            "duration_ms": int(env("AP2_DURATION_MS", "0")),
            "commands": [
                ["insights_cli.py", "publish", "seeds/alice_celery_retry.json", "--wiki", wiki_url],
                ["insights_cli.py", "publish", "seeds/carol_redis_eviction.json", "--wiki", wiki_url],
                ["GET", "/search?q=<canonical>&k=3"],
            ],
            "evidence": {
                "baseline": {
                    "query": problem,
                    "hit_count": len(baseline_search.get("hits") or []),
                    "hit_ids": [hit.get("id") for hit in (baseline_search.get("hits") or []) if hit.get("id")],
                },
                "matrix": ap2_matrix,
                "published_card_ids": [
                    "alice-celery-retry-2026-04-08",
                    "carol-redis-eviction-2026-03-27",
                ],
                "outputs": {
                    "celery": output_excerpt(env("PUBLISH_CELERY_OUTPUT")),
                    "redis": output_excerpt(env("PUBLISH_REDIS_OUTPUT")),
                },
            },
        },
    },
}

Path(env("REPORT_JSON")).write_text(
    json.dumps(report, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)
PY
}

main() {
  mkdir -p "${LOG_DIR}"
  exec > >(tee "${REPORT_TXT}") 2>&1

  WORKDIR="$(mktemp -d "/tmp/insights-adoption-proof.XXXXXX")"
  HOME_DIR="${WORKDIR}/home"
  STORE_DIR="${WORKDIR}/wiki_tree"
  DAEMON_LOG="${WORKDIR}/daemon.log"
  mkdir -p "${HOME_DIR}" "${STORE_DIR}"
  trap cleanup EXIT
  PYTHON_BIN="$(choose_python)"
  RUN_STARTED_AT="$(iso_utc)"
  RUN_STARTED_MS="$(epoch_ms)"

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
  BASELINE_SEARCH_JSON="$(search_json "${PROBLEM}" 3)"

  log "first publish: Alice good + Bob bad"
  PUBLISH_STARTED_AT="$(iso_utc)"
  publish_started_ms="$(epoch_ms)"
  PUBLISH_GOOD_OUTPUT="$(run_cli publish seeds/alice_pgpool.json --wiki "${WIKI_URL}")"
  PUBLISH_BAD_OUTPUT="$(run_cli publish seeds/bob_pgpool_bad.json --wiki "${WIKI_URL}")"
  publish_finished_ms="$(epoch_ms)"
  PUBLISH_FINISHED_AT="$(iso_utc)"
  PUBLISH_DURATION_MS="$(duration_ms "${publish_started_ms}" "${publish_finished_ms}")"
  assert_contains "publish good" "${PUBLISH_GOOD_OUTPUT}" "published alice-pgpool-2026-04-10"
  assert_contains "publish bad" "${PUBLISH_BAD_OUTPUT}" "published bob-pgpool-bad-2026-04-12"

  log "first relevant hit / cite"
  HIT_STARTED_AT="$(iso_utc)"
  hit_started_ms="$(epoch_ms)"
  FIRST_SOLVE_OUTPUT="$(run_cli solve "${PROBLEM}" --wiki "${WIKI_URL}" --no-ai)"
  hit_finished_ms="$(epoch_ms)"
  HIT_FINISHED_AT="$(iso_utc)"
  HIT_DURATION_MS="$(duration_ms "${hit_started_ms}" "${hit_finished_ms}")"
  assert_contains "first relevant hit" "${FIRST_SOLVE_OUTPUT}" "hot-loaded alice-pgpool-2026-04-10"
  assert_contains "first relevant fix" "${FIRST_SOLVE_OUTPUT}" "idle_in_transaction_session_timeout"

  log "clean-machine install into isolated HOME"
  CLEAN_STARTED_AT="$(iso_utc)"
  clean_started_ms="$(epoch_ms)"
  INSTALL_OUTPUT="$(run_cli wiki-install --server "${WIKI_URL}")"
  clean_finished_ms="$(epoch_ms)"
  CLEAN_FINISHED_AT="$(iso_utc)"
  CLEAN_DURATION_MS="$(duration_ms "${clean_started_ms}" "${clean_finished_ms}")"
  assert_contains "wiki install" "${INSTALL_OUTPUT}" "install ok server=${WIKI_URL}"
  assert_contains "wiki install cache count" "${INSTALL_OUTPUT}" "cached=2 cards"

  cache_dir="${HOME_DIR}/.cache/insights-share"
  test -f "${cache_dir}/config.json"
  test -f "${cache_dir}/trusted_keys.json"
  test -f "${cache_dir}/alice-pgpool-2026-04-10.json"
  test -f "${cache_dir}/bob-pgpool-bad-2026-04-12.json"

  log "day-2 return: solve uses installed config without --wiki"
  mkdir -p "${WORKDIR}/day2"
  DAY2_STARTED_AT="$(iso_utc)"
  day2_started_ms="$(epoch_ms)"
  DAY2_SOLVE_OUTPUT="$(cd "${WORKDIR}/day2" && HOME="${HOME_DIR}" "${PYTHON_BIN}" "${SOURCE_DIR}/insights_cli.py" solve "${PROBLEM}" --no-ai)"
  day2_finished_ms="$(epoch_ms)"
  DAY2_FINISHED_AT="$(iso_utc)"
  DAY2_DURATION_MS="$(duration_ms "${day2_started_ms}" "${day2_finished_ms}")"
  assert_contains "day-2 return" "${DAY2_SOLVE_OUTPUT}" "hot-loaded alice-pgpool-2026-04-10"

  log "AP-2 relevance-lift matrix"
  AP2_STARTED_AT="$(iso_utc)"
  ap2_started_ms="$(epoch_ms)"
  PUBLISH_CELERY_OUTPUT="$(run_cli publish seeds/alice_celery_retry.json --wiki "${WIKI_URL}")"
  PUBLISH_REDIS_OUTPUT="$(run_cli publish seeds/carol_redis_eviction.json --wiki "${WIKI_URL}")"
  assert_contains "publish celery" "${PUBLISH_CELERY_OUTPUT}" "published alice-celery-retry-2026-04-08"
  assert_contains "publish redis" "${PUBLISH_REDIS_OUTPUT}" "published carol-redis-eviction-2026-03-27"
  AP2_MATRIX_JSON_PATH="${WORKDIR}/relevance_lift_matrix.json"
  export WIKI_URL AP2_MATRIX_JSON_PATH BASELINE_SEARCH_JSON PROBLEM
  "${PYTHON_BIN}" - <<'PY'
from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from pathlib import Path


def http_json(path: str, params: dict[str, str]) -> dict:
    query = urllib.parse.urlencode(params)
    url = f"{os.environ['WIKI_URL'].rstrip('/')}{path}?{query}"
    with urllib.request.urlopen(url, timeout=5.0) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data if isinstance(data, dict) else {}


def search(query: str) -> list[dict]:
    return list(http_json("/search", {"q": query, "k": "3"}).get("hits") or [])


def score_of(hit: dict) -> float:
    try:
        return float(hit.get("score") or 0.0)
    except Exception:
        return 0.0


baseline = json.loads(os.environ.get("BASELINE_SEARCH_JSON") or "{}")
baseline_hits = list(baseline.get("hits") or [])
if baseline_hits:
    raise SystemExit(f"expected empty baseline before first publish, got {[hit.get('id') for hit in baseline_hits]}")

cases = [
    {
        "name": "postgres_pool_exhaustion",
        "query": os.environ["PROBLEM"],
        "expected_top_id": "alice-pgpool-2026-04-10",
        "wrong_domain_ids": ["alice-celery-retry-2026-04-08", "carol-redis-eviction-2026-03-27"],
    },
    {
        "name": "celery_retry_storm",
        "query": "Celery retry storm is overwhelming Redis broker and workers loop immediate retry without backoff",
        "expected_top_id": "alice-celery-retry-2026-04-08",
        "wrong_domain_ids": ["alice-pgpool-2026-04-10", "bob-pgpool-bad-2026-04-12", "carol-redis-eviction-2026-03-27"],
    },
    {
        "name": "redis_session_eviction",
        "query": "Redis allkeys-lru is evicting session data and users are logged out during cache warm-up",
        "expected_top_id": "carol-redis-eviction-2026-03-27",
        "wrong_domain_ids": ["alice-pgpool-2026-04-10", "bob-pgpool-bad-2026-04-12", "alice-celery-retry-2026-04-08"],
    },
]

results = []
for case in cases:
    hits = search(case["query"])
    top = hits[0] if hits else {}
    top_id = top.get("id")
    if top_id != case["expected_top_id"]:
        raise SystemExit(f"{case['name']} expected top {case['expected_top_id']}, got {top_id}; hits={[hit.get('id') for hit in hits]}")
    if top_id in set(case["wrong_domain_ids"]):
        raise SystemExit(f"{case['name']} wrong-domain top hit {top_id}")
    results.append(
        {
            "name": case["name"],
            "query": case["query"],
            "expected_top_id": case["expected_top_id"],
            "top_hit_id": top_id,
            "top_hit_score": score_of(top),
            "hit_ids": [hit.get("id") for hit in hits if hit.get("id")],
            "wrong_domain_not_top": all(top_id != wrong_id for wrong_id in case["wrong_domain_ids"]),
        }
    )

matrix = {
    "status": "ok",
    "baseline_before_publish": {
        "query": os.environ["PROBLEM"],
        "hit_count": 0,
        "hit_ids": [],
    },
    "case_count": len(results),
    "cases": results,
}
Path(os.environ["AP2_MATRIX_JSON_PATH"]).write_text(
    json.dumps(matrix, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)
PY
  ap2_finished_ms="$(epoch_ms)"
  AP2_FINISHED_AT="$(iso_utc)"
  AP2_DURATION_MS="$(duration_ms "${ap2_started_ms}" "${ap2_finished_ms}")"

  write_report "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  log "PASS clean_machine_install=ok first_relevant_hit=alice-pgpool-2026-04-10 first_publish=2 day_2_return=ok relevance_lift_matrix=ok"
  log "report=${REPORT_JSON}"
}

main "$@"
