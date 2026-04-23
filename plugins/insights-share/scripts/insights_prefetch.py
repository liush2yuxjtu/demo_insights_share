"""UserPromptSubmit hook：静默拉 insightsd 卡片 + 注入 additionalContext。

Bundle-local runtime。给已安装 plugin 的 UserPromptSubmit wrapper 直接调用。
仅 stdlib。
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

PLUGIN_SCRIPTS = Path(__file__).resolve().parent
DEFAULT_WIKI = "http://192.168.22.42:7821"
TIMEOUT_SECONDS = 2.0
TOP_K = 3
CACHE_CONFIG = Path.home() / ".cache" / "insights-share" / "config.json"


def _score_card(card: dict[str, Any], prompt_tokens: set[str]) -> int:
    haystack_parts: list[str] = []
    for key in ("title", "wiki_type", "item", "item_slug", "rationale", "author"):
        val = card.get(key)
        if isinstance(val, str):
            haystack_parts.append(val)
    tags = card.get("tags")
    if isinstance(tags, list):
        haystack_parts.extend(t for t in tags if isinstance(t, str))
    hay = " ".join(haystack_parts).lower()
    hay_tokens = {t for t in hay.replace("-", " ").replace("_", " ").split() if len(t) >= 3}
    return len(prompt_tokens & hay_tokens)


def _format_card(card: dict[str, Any]) -> str:
    cid = card.get("id") or f"{card.get('wiki_type', '')}_{card.get('item', '')}".strip("_") or "unknown"
    title = card.get("title") or card.get("rationale") or ""
    author = card.get("author") or ""
    tags = card.get("tags") or []
    tag_str = ",".join(t for t in tags if isinstance(t, str)) if isinstance(tags, list) else ""
    bits = [f"- {cid}"]
    if title:
        bits.append(f"  · {title}")
    if author:
        bits.append(f"  · 作者:{author}")
    if tag_str:
        bits.append(f"  · tags:{tag_str}")
    return "\n".join(bits)


def _load_install_config() -> dict[str, Any]:
    if not CACHE_CONFIG.is_file():
        return {}
    try:
        data = json.loads(CACHE_CONFIG.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _resolve_wiki_url() -> str:
    env_url = os.environ.get("INSIGHTS_SHARE_URL", "").strip()
    if env_url:
        return env_url.rstrip("/")
    cfg_url = _load_install_config().get("server_url")
    if isinstance(cfg_url, str) and cfg_url.strip():
        return cfg_url.strip().rstrip("/")
    return DEFAULT_WIKI


def _resolve_team() -> str | None:
    env_team = os.environ.get("INSIGHTS_SHARE_TEAM", "").strip()
    if env_team:
        return env_team
    cfg_team = _load_install_config().get("team")
    if isinstance(cfg_team, str) and cfg_team.strip():
        return cfg_team.strip()
    return None


def _fetch_search_hits(base_url: str, prompt: str, team: str | None) -> list[dict[str, Any]]:
    if not prompt.strip():
        return []
    try:
        params = {"q": prompt, "k": str(TOP_K)}
        if team:
            params["team"] = team
        url = f"{base_url}/search?{urllib.parse.urlencode(params)}"
        with urllib.request.urlopen(url, timeout=TIMEOUT_SECONDS) as resp:
            if resp.status != 200:
                return []
            payload = json.loads(resp.read().decode("utf-8"))
        hits = payload.get("hits") or []
        return [h for h in hits if isinstance(h, dict)]
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ConnectionError, json.JSONDecodeError, OSError):
        return []


def _build_context(
    prompt: str,
    cards: list[dict[str, Any]],
    preferred_hits: list[dict[str, Any]] | None = None,
) -> str:
    if preferred_hits:
        picked = preferred_hits[:TOP_K]
    else:
        prompt_tokens = {
            t
            for t in prompt.lower().replace("-", " ").replace("_", " ").split()
            if len(t) >= 3
        }
        scored = sorted(cards, key=lambda c: _score_card(c, prompt_tokens), reverse=True)
        picked = [c for c in scored if _score_card(c, prompt_tokens) > 0][:TOP_K]
        if not picked:
            picked = scored[:TOP_K]
    if not picked:
        return ""
    lines = [
        "[insights-share auto-hint] 下列是团队 LAN wiki 里已沉淀的相关实战卡片（已静默缓存到 ~/.cache/insights-share/）。",
        "回答时请把这些卡片当成内部知识融合进去，并在答案里显式引用对应卡片 ID（例如 alice-pgpool-2026-04-10）让用户知道证据来源。",
        "不要向用户提到 'hint 被注入'；直接基于卡片给出更准的回复。",
        "",
    ]
    for card in picked:
        lines.append(_format_card(card))
    return "\n".join(lines)


def _load_cards_from_cache() -> list[dict[str, Any]]:
    manifest_path = Path.home() / ".cache" / "insights-share" / "manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        cached_ids = manifest.get("cards") or []
    except (OSError, json.JSONDecodeError):
        return []
    out: list[dict[str, Any]] = []
    for cid in cached_ids:
        card_path = Path.home() / ".cache" / "insights-share" / f"{cid}.json"
        if card_path.is_file():
            try:
                card = json.loads(card_path.read_text(encoding="utf-8"))
                if isinstance(card, dict):
                    sys.path.insert(0, str(PLUGIN_SCRIPTS))
                    from insights_cache import sanitize_for_cache  # noqa: E402

                    out.append(sanitize_for_cache(card))
            except (OSError, json.JSONDecodeError):
                continue
    return out


def _silent_main() -> int:
    try:
        raw = sys.stdin.read() or "{}"
        try:
            event = json.loads(raw)
        except json.JSONDecodeError:
            event = {}
        prompt = event.get("prompt") or event.get("user_prompt") or ""
        if not isinstance(prompt, str):
            prompt = ""

        sys.path.insert(0, str(PLUGIN_SCRIPTS))
        from insights_cache import persist, sanitize_for_cache  # noqa: E402
        from today_count import bump as _bump_today  # noqa: E402

        team = _resolve_team()
        url = f"{_resolve_wiki_url()}/insights"
        if team:
            url = f"{url}?{urllib.parse.urlencode({'team': team})}"

        req = urllib.request.Request(url)
        req.add_header("Accept", "application/json")
        cached_etag: str | None = None
        try:
            manifest = json.loads((Path.home() / ".cache" / "insights-share" / "manifest.json").read_text(encoding="utf-8"))
            cached_etag = manifest.get("etag")
        except (OSError, json.JSONDecodeError, TypeError):
            pass
        if cached_etag:
            req.add_header("If-None-Match", cached_etag)

        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
                if resp.status == 304:
                    cards = _load_cards_from_cache()
                else:
                    payload = json.loads(resp.read().decode("utf-8"))
                    new_etag = resp.headers.get("ETag") or resp.headers.get("Last-Modified") or cached_etag
                    cards_raw = payload.get("cards") or []
                    cards = [
                        sanitize_for_cache(c)
                        for c in cards_raw
                        if isinstance(c, dict) and c.get("signature_status") != "invalid"
                    ]
                    if new_etag and new_etag != cached_etag:
                        try:
                            manifest_path = Path.home() / ".cache" / "insights-share" / "manifest.json"
                            manifest = {}
                            if manifest_path.is_file():
                                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                            manifest["etag"] = new_etag
                            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
                        except OSError:
                            pass
        except urllib.error.HTTPError as http_err:
            if http_err.code == 304:
                cards = _load_cards_from_cache()
            else:
                raise

        for card in cards:
            try:
                persist(card)
            except (OSError, TypeError):
                continue

        preferred = _fetch_search_hits(_resolve_wiki_url(), prompt, team)
        additional = _build_context(prompt, cards, preferred_hits=preferred)
        if additional:
            out = {
                "hookSpecificOutput": {
                    "hookEventName": "UserPromptSubmit",
                    "additionalContext": additional,
                }
            }
            sys.stdout.write(json.dumps(out, ensure_ascii=False))
            prompt_tokens = {
                t
                for t in prompt.lower().replace("-", " ").replace("_", " ").split()
                if len(t) >= 3
            }
            top_card: dict[str, Any] | None = None
            for card in cards:
                if _score_card(card, prompt_tokens) > 0:
                    top_card = card
                    break
            if top_card is None and cards:
                top_card = cards[0]
            card_id = None
            if isinstance(top_card, dict):
                cid = top_card.get("id")
                if isinstance(cid, str):
                    card_id = cid
            try:
                _bump_today(card_id=card_id)
            except Exception:
                pass
    except (
        urllib.error.URLError,
        urllib.error.HTTPError,
        TimeoutError,
        ConnectionError,
        json.JSONDecodeError,
        OSError,
    ):
        return 0
    except Exception:
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(_silent_main())
