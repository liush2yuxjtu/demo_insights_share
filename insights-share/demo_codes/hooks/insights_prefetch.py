"""UserPromptSubmit hook：静默拉 LAN insightsd 卡片 + 注入 additionalContext。

每次 Bob 按下回车：
1. 从 stdin 读 hook event，拿到用户 prompt
2. GET 默认 LAN daemon http://192.168.22.42:7821/insights 拿全量卡片（2s 超时）
3. 调 insights_cache.persist(card) 把卡片落盘到 ~/.cache/insights-share/
4. 根据 prompt 关键词挑 top-K 相关卡片，按 Claude Code hook 协议输出
   `{"hookSpecificOutput": {"hookEventName": "UserPromptSubmit",
                            "additionalContext": "..."}}` 到 stdout
   → Claude 下一轮回答里就能引用这些卡片 ID / title

对用户无感：
- daemon 不通 / 网络失败 → stdout 空，退出码 0，不打断用户输入
- stderr 全部吞掉（避免污染终端）

注意：本脚本必须前台运行，command 末尾禁止加 `&`，否则 stdout 会被丢掉，
Claude 收不到 additionalContext。
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

DEMO_CODES = Path(__file__).resolve().parent.parent
DEFAULT_WIKI = "http://192.168.22.42:7821"
TIMEOUT_SECONDS = 2.0
TOP_K = 3
CACHE_CONFIG = Path.home() / ".cache" / "insights-share" / "config.json"


def _score_card(card: dict[str, Any], prompt_tokens: set[str]) -> int:
    """按 prompt 关键词与 card 的 title/tags/body 做 token 重叠计分。"""
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
    """P1 (2026-04-23): 调 daemon /search?q=<prompt> 拿 server-side ranking。

    daemon 已在 store.py::search_cards 实现 Jaccard + tag_bonus 打分，信号比
    本地 _score_card 的纯 token 重叠计数强。失败时返 []（上层用 fallback）。
    """
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
    # P1 优先用 daemon /search top hits（server-side scoring 含 tag_bonus）
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

        sys.path.insert(0, str(DEMO_CODES / "hooks"))
        from insights_cache import persist, sanitize_for_cache  # noqa: E402

        wiki_daemon_dir = DEMO_CODES.parent / "wiki_daemon"
        if wiki_daemon_dir.is_dir():
            sys.path.insert(0, str(wiki_daemon_dir))
        try:
            from today_count import bump as _bump_today  # noqa: E402
        except ImportError:
            _bump_today = None

        team = _resolve_team()
        url = f"{_resolve_wiki_url()}/insights"
        if team:
            url = f"{url}?{urllib.parse.urlencode({'team': team})}"

        # ETag delta sync: send If-None-Match, skip processing on 304
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

        def _load_cards_from_cache() -> list[dict[str, Any]]:
            """ETag 304 命中时，用本地 ~/.cache/insights-share/ 复建 cards 列表。"""
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
                            out.append(sanitize_for_cache(card))
                    except (OSError, json.JSONDecodeError):
                        continue
            return out

        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
                # urllib 对 304 通常直接抛 HTTPError，这里 if 分支只作兜底
                if resp.status == 304:
                    sys.stderr.write("[insights_prefetch] 304 Not Modified, using cached cards\n")
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
                    # Update manifest etag
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
            # urllib 的默认行为：任何非 2xx（含 304 Not Modified）都抛 HTTPError
            # Feature #2 要求：缓存命中时可二次使用、不重复全流程 → 这里必须用本地缓存兜住
            if http_err.code == 304:
                sys.stderr.write("[insights_prefetch] 304 Not Modified (HTTPError), using cached cards\n")
                cards = _load_cards_from_cache()
            else:
                # 其他 HTTP 错误继续被外层统一吞掉（保持无感失败契约）
                raise

        for card in cards:
            try:
                persist(card)
            except (OSError, TypeError):
                # 落盘失败不阻塞注入
                continue

        # P1 (2026-04-23): 先问 daemon /search 拿 server-side ranking 的 top hits，
        # daemon 失败/空 → fallback 到本地 _score_card
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
            # 命中卡片：递增 today_count.json，给 statusline badge 用
            if _bump_today is not None:
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
