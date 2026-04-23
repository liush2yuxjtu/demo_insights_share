"""insights-share 本地缓存模块。

Bundle-local runtime。给已安装 plugin 的 hook 用，不再依赖 repo checkout。
仅 stdlib。
"""
from __future__ import annotations

import json
import os
import tempfile
import time
from pathlib import Path
from typing import Any

CACHE_DIR = Path(os.path.expanduser("~/.cache/insights-share"))
MANIFEST_PATH = CACHE_DIR / "manifest.json"
_PUBLIC_CARD_FIELDS = frozenset(
    {
        "id",
        "title",
        "author",
        "wiki_type",
        "item",
        "item_slug",
        "tags",
        "team",
        "status",
        "topic_id",
        "label",
        "label_override",
        "effective_label",
        "signature_status",
        "signature_key_id",
        "signature_signed_at",
        "score",
    }
)


def _ensure_cache_dir() -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    _ensure_cache_dir()
    fd, tmp_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent)
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2)
        os.replace(tmp_name, path)
    except Exception:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def _load_manifest() -> dict[str, Any]:
    if not MANIFEST_PATH.is_file():
        return {"last_sync_at": None, "cards": [], "signature": {"failures": []}}
    try:
        return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"last_sync_at": None, "cards": [], "signature": {"failures": []}}


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime())


def _normalize_card_id(card: dict[str, Any]) -> str:
    cid = card.get("id")
    if isinstance(cid, str) and cid.strip():
        return cid.strip()
    wt = card.get("wiki_type") or ""
    item = card.get("item") or card.get("item_slug") or ""
    if wt or item:
        return f"{wt}_{item}".strip("_") or "unknown"
    return f"anon_{abs(hash(json.dumps(card, sort_keys=True, ensure_ascii=False))) % 10**10}"


def sanitize_for_cache(card: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(card, dict):
        raise TypeError(f"card must be dict, got {type(card).__name__}")
    sanitized = {
        key: card[key]
        for key in _PUBLIC_CARD_FIELDS
        if key in card
    }
    sanitized["id"] = _normalize_card_id(card)
    effective_label = card.get("label_override") or card.get("label")
    if effective_label not in (None, ""):
        sanitized["effective_label"] = effective_label
    return sanitized


def persist(card: dict[str, Any]) -> Path:
    if not isinstance(card, dict):
        raise TypeError(f"card must be dict, got {type(card).__name__}")

    safe_card = sanitize_for_cache(card)
    _ensure_cache_dir()
    card_id = _normalize_card_id(safe_card)
    card_path = CACHE_DIR / f"{card_id}.json"
    _atomic_write_json(card_path, safe_card)

    manifest = _load_manifest()
    cards: list[str] = manifest.get("cards") or []
    if card_id not in cards:
        cards.append(card_id)
    manifest["cards"] = cards
    manifest["last_sync_at"] = _now_iso()
    signature_meta = manifest.get("signature") or {}
    failures = [item for item in signature_meta.get("failures") or [] if item != card_id]
    signature_status = str(safe_card.get("signature_status") or "legacy-unsigned")
    if signature_status == "invalid":
        failures.append(card_id)
    manifest["signature"] = {
        "failures": failures,
        "last_status": signature_status,
        "last_card_id": card_id,
        "updated_at": _now_iso(),
    }
    _atomic_write_json(MANIFEST_PATH, manifest)
    return card_path


def list_cached() -> list[str]:
    return list(_load_manifest().get("cards") or [])


def manifest_path() -> Path:
    return MANIFEST_PATH
