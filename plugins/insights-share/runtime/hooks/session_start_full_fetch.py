"""SessionStart full-card prefetch with delta sync.

Proposes to replace session-start.sh simple curl approach with full card
fetch + ETag-based delta sync.

Design:
- Fetches from GET /insights (full cards, not just topics metadata)
- Stores ETag in ~/.cache/insights-share/warm/etag.txt
- On subsequent calls, sends If-None-Match; server returns 304 when unchanged
- Persists all cards via insights_cache.persist()

Exit 0 always (soft skip on network/parse errors).
User-unaware: stderr only, no stdout干扰 Claude Code session start.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from insights_cache import persist

DEMO_CODES = Path(__file__).resolve().parent.parent
CACHE_DIR = Path.home() / ".cache" / "insights-share"
WARM_DIR = CACHE_DIR / "warm"
ETAG_FILE = WARM_DIR / "etag.txt"
MANIFEST_ETAG_KEY = "etag"
TIMEOUT_SECONDS = 2.0


def _resolve_wiki_url() -> str:
    env_url = os.environ.get("INSIGHTS_SHARE_URL", "").strip()
    if env_url:
        return env_url.rstrip("/")
    cfg_config = CACHE_DIR / "config.json"
    if cfg_config.is_file():
        try:
            data = json.loads(cfg_config.read_text(encoding="utf-8"))
            url = data.get("server_url")
            if isinstance(url, str) and url.strip():
                return url.strip().rstrip("/")
        except (OSError, json.JSONDecodeError):
            pass
    return os.environ.get("INSIGHTS_DAEMON_URL", "http://192.168.22.42:7821").rstrip("/")


def _resolve_team() -> str | None:
    env_team = os.environ.get("INSIGHTS_SHARE_TEAM", "").strip()
    if env_team:
        return env_team
    cfg_config = CACHE_DIR / "config.json"
    if cfg_config.is_file():
        try:
            data = json.loads(cfg_config.read_text(encoding="utf-8"))
            team = data.get("team")
            if isinstance(team, str) and team.strip():
                return team.strip()
        except (OSError, json.JSONDecodeError):
            pass
    return None


def _load_manifest() -> dict[str, Any]:
    manifest_path = CACHE_DIR / "manifest.json"
    if not manifest_path.is_file():
        return {}
    try:
        return json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _save_manifest(manifest: dict[str, Any]) -> None:
    import tempfile

    manifest_path = CACHE_DIR / "manifest.json"
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(
        prefix=".manifest.", suffix=".tmp", dir=str(CACHE_DIR)
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(manifest, fh, ensure_ascii=False, indent=2)
        os.replace(tmp, manifest_path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _persist_manifest_etag(etag: str | None) -> None:
    manifest = _load_manifest()
    if etag:
        manifest[MANIFEST_ETAG_KEY] = etag
    else:
        manifest.pop(MANIFEST_ETAG_KEY, None)
    _save_manifest(manifest)


def _load_cached_etag() -> str | None:
    # Try warm/etag.txt first, then manifest
    if ETAG_FILE.is_file():
        try:
            return ETAG_FILE.read_text(encoding="utf-8").strip() or None
        except OSError:
            pass
    manifest = _load_manifest()
    return manifest.get(MANIFEST_ETAG_KEY) or None


def _save_cached_etag(etag: str) -> None:
    WARM_DIR.mkdir(parents=True, exist_ok=True)
    try:
        ETAG_FILE.write_text(etag, encoding="utf-8")
    except OSError:
        pass
    _persist_manifest_etag(etag)


def _persist_card(card: dict[str, Any]) -> Path | None:
    try:
        card_path = persist(card)
        manifest = _load_manifest()
        manifest["session_start_fetch"] = True
        _save_manifest(manifest)
        return card_path
    except Exception:
        return None


def _do_fetch() -> int:
    wiki_url = _resolve_wiki_url()
    team = _resolve_team()

    url = f"{wiki_url}/insights"
    if team:
        url = f"{url}?{urllib.parse.urlencode({'team': team})}"

    cached_etag = _load_cached_etag()

    req = urllib.request.Request(url)
    req.add_header("Accept", "application/json")
    if cached_etag:
        req.add_header("If-None-Match", cached_etag)

    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
            status = resp.status
            etag = resp.headers.get("ETag") or resp.headers.get("Last-Modified") or None

            if status == 304:
                # Not modified - update cached etag from manifest, skip card persist
                if cached_etag:
                    _save_cached_etag(cached_etag)
                sys.stderr.write(
                    f"[session_start_full_fetch] 304 Not Modified, cache stays valid\n"
                )
                return 0

            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code == 304:
            sys.stderr.write(
                f"[session_start_full_fetch] 304 from daemon, cache stays valid\n"
            )
            return 0
        sys.stderr.write(
            f"[session_start_full_fetch] HTTP {exc.code} fetching {url}: {exc}\n"
        )
        return 0
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        sys.stderr.write(
            f"[session_start_full_fetch] network error {url}: {exc}\n"
        )
        return 0
    except json.JSONDecodeError as exc:
        sys.stderr.write(
            f"[session_start_full_fetch] JSON parse error: {exc}\n"
        )
        return 0

    cards_raw = payload.get("cards") or []
    cards: list[dict[str, Any]] = [
        c for c in cards_raw if isinstance(c, dict)
    ]

    # Always persist cards and update etag when server returned full data
    if etag:
        _save_cached_etag(etag)

    persisted = 0
    for card in cards:
        path = _persist_card(card)
        if path:
            persisted += 1

    sys.stderr.write(
        f"[session_start_full_fetch] fetched {len(cards)} cards, "
        f"persisted {persisted}, etag={etag or 'none'}\n"
    )
    return 0


def main() -> int:
    try:
        return _do_fetch()
    except Exception as exc:
        # All errors are soft - stderr only, exit 0
        sys.stderr.write(f"[session_start_full_fetch] unexpected error: {exc}\n")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
