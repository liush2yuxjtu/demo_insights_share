"""轻量 JSON 卡片存储 + bag-of-words Jaccard 检索。"""

from __future__ import annotations

import json
import re
import threading
from pathlib import Path
from typing import Any

_TOKEN_RE = re.compile(r"[^a-z0-9]+")


def _tokenize(text: str) -> set[str]:
    return {tok for tok in _TOKEN_RE.split(text.lower()) if tok}


def _card_tokens(card: dict[str, Any]) -> set[str]:
    parts: list[str] = [str(card.get("title", ""))]
    tags = card.get("tags") or []
    if isinstance(tags, list):
        parts.extend(str(t) for t in tags)
    for field in ("context", "symptom", "root_cause", "fix", "body"):
        value = card.get(field)
        if value:
            parts.append(str(value))
    return _tokenize(" ".join(parts))


class InsightStore:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self._lock = threading.Lock()

    def load(self) -> list[dict[str, Any]]:
        with self._lock:
            return self._load_unlocked()

    def _load_unlocked(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        with self.path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and isinstance(data.get("cards"), list):
            return list(data["cards"])
        return []

    def save(self, cards: list[dict[str, Any]]) -> None:
        with self._lock:
            self._save_unlocked(cards)

    def _save_unlocked(self, cards: list[dict[str, Any]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        with tmp.open("w", encoding="utf-8") as fh:
            json.dump(cards, fh, ensure_ascii=False, indent=2)
        tmp.replace(self.path)

    def add(self, card: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(card, dict) or not card.get("id"):
            raise ValueError("card must be a dict with non-empty 'id'")
        with self._lock:
            cards = self._load_unlocked()
            cid = card["id"]
            replaced = False
            for idx, existing in enumerate(cards):
                if existing.get("id") == cid:
                    cards[idx] = card
                    replaced = True
                    break
            if not replaced:
                cards.append(card)
            self._save_unlocked(cards)
            return card

    def list_all(self) -> list[dict[str, Any]]:
        cards = self.load()
        return [
            {
                "id": c.get("id"),
                "title": c.get("title"),
                "tags": c.get("tags") or [],
                "author": c.get("author"),
            }
            for c in cards
        ]

    def search(self, q: str, k: int = 3) -> list[dict[str, Any]]:
        query_tokens = _tokenize(q or "")
        if not query_tokens:
            return []
        cards = self.load()
        scored: list[tuple[float, dict[str, Any]]] = []
        for card in cards:
            card_tokens = _card_tokens(card)
            if not card_tokens:
                continue
            union = query_tokens | card_tokens
            if not union:
                continue
            inter = query_tokens & card_tokens
            score = len(inter) / len(union)
            if score <= 0:
                continue
            scored.append((score, card))
        scored.sort(key=lambda item: item[0], reverse=True)
        results: list[dict[str, Any]] = []
        for score, card in scored[: max(1, int(k))]:
            enriched = dict(card)
            enriched["score"] = round(score, 4)
            results.append(enriched)
        return results
