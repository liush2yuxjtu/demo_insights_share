"""insights-share 本地缓存模块。

把 LAN insightsd 命中的 insight 卡片落盘到 ~/.cache/insights-share/<id>.json,
同时维护 manifest.json,记录 last_sync_at 和已知 card id 列表。

仅 stdlib,不依赖 requests/pydantic,与 insights_cli.py 风格保持一致。
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
    """先写临时文件再 rename,避免半写状态被读取。"""
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
    """从 card dict 抽取一个稳定 id。

    优先 id 字段;否则用 wiki_type/item 拼接;再否则 fallback 到 hash。
    严禁返回空字符串。
    """
    cid = card.get("id")
    if isinstance(cid, str) and cid.strip():
        return cid.strip()
    wt = card.get("wiki_type") or ""
    item = card.get("item") or card.get("item_slug") or ""
    if wt or item:
        return f"{wt}_{item}".strip("_") or "unknown"
    # 极端情况:用 hash 兜底,但仍保证落盘可寻址
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
    """把 card 写入 ~/.cache/insights-share/<id>.json,并更新 manifest。

    返回写入的 card 文件绝对路径。

    Raises:
        TypeError: card 不是 dict
        OSError: 文件系统异常(disk full / permission denied)
    """
    if not isinstance(card, dict):
        raise TypeError(f"card must be dict, got {type(card).__name__}")

    safe_card = sanitize_for_cache(card)
    _ensure_cache_dir()
    card_id = _normalize_card_id(safe_card)
    card_path = CACHE_DIR / f"{card_id}.json"

    # 写入卡片本体(覆盖式,最新的就是权威的)
    _atomic_write_json(card_path, safe_card)

    # 更新 manifest:把 card_id 加入 cards 列表(去重),刷新 last_sync_at
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
    """返回 manifest 中已知的 card_id 列表。"""
    return list(_load_manifest().get("cards") or [])


def manifest_path() -> Path:
    return MANIFEST_PATH
