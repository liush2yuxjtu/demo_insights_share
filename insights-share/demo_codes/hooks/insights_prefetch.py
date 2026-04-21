"""UserPromptSubmit hook：静默拉 LAN insightsd 卡片 + 注入 additionalContext。

每次 Bob 按下回车：
1. 从 stdin 读 hook event，拿到用户 prompt
2. GET http://127.0.0.1:7821/insights 拿全量卡片（本地 daemon，2s 超时）
3. 调 insights_cache.persist(card) 把卡片落盘到 ~/.cache/insights-wiki/
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
DEFAULT_WIKI = "http://127.0.0.1:7821"
TIMEOUT_SECONDS = 2.0
TOP_K = 3
CACHE_CONFIG = Path.home() / ".cache" / "insights-wiki" / "config.json"


def _score_card(card: dict[str, Any], prompt_tokens: set[str]) -> int:
    """按 prompt 关键词与 card 的 title/tags/body 做 token 重叠计分。"""
    haystack_parts: list[str] = []
    for key in ("title", "wiki_type", "item", "rationale", "author"):
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


def _resolve_team() -> str | None:
    env_team = os.environ.get("INSIGHTS_WIKI_TEAM", "").strip()
    if env_team:
        return env_team
    cfg_team = _load_install_config().get("team")
    if isinstance(cfg_team, str) and cfg_team.strip():
        return cfg_team.strip()
    return None


def _build_context(prompt: str, cards: list[dict[str, Any]]) -> str:
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
        "[insights-share auto-hint] 下列是团队 LAN wiki 里已沉淀的相关实战卡片（已静默缓存到 ~/.cache/insights-wiki/）。",
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
        from insights_cache import persist  # noqa: E402

        wiki_daemon_dir = DEMO_CODES.parent / "wiki_daemon"
        if wiki_daemon_dir.is_dir():
            sys.path.insert(0, str(wiki_daemon_dir))
        try:
            from today_count import bump as _bump_today  # noqa: E402
        except ImportError:
            _bump_today = None

        team = _resolve_team()
        url = f"{DEFAULT_WIKI}/insights"
        if team:
            url = f"{url}?{urllib.parse.urlencode({'team': team})}"
        with urllib.request.urlopen(url, timeout=TIMEOUT_SECONDS) as resp:
            payload = json.loads(resp.read().decode("utf-8"))

        cards_raw = payload.get("cards") or []
        cards: list[dict[str, Any]] = [c for c in cards_raw if isinstance(c, dict)]
        for card in cards:
            try:
                persist(card)
            except (OSError, TypeError):
                # 落盘失败不阻塞注入
                continue

        additional = _build_context(prompt, cards)
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
