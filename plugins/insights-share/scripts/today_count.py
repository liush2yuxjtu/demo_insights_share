"""insights-share 今日触发计数器。

Bundle-local runtime。给已安装 plugin 的 statusline / hook 用。
仅 stdlib。
"""
from __future__ import annotations

import datetime as _dt
import json
import os
import tempfile
from pathlib import Path
from typing import Any

CACHE_DIR = Path(os.path.expanduser("~/.cache/insights-share"))
TODAY_COUNT_PATH = CACHE_DIR / "today_count.json"
BACKUP_PATH = CACHE_DIR / "today_count.json.bak"


def _ensure_cache_dir() -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _today_iso() -> str:
    return _dt.date.today().isoformat()


def _now_local_iso() -> str:
    now = _dt.datetime.now().astimezone()
    return now.strftime("%Y-%m-%dT%H:%M:%S%z")


def _atomic_write(path: Path, payload: dict[str, Any]) -> None:
    _ensure_cache_dir()
    fd, tmp_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent)
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_name, path)
    except Exception:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def _empty_record(date: str) -> dict[str, Any]:
    return {
        "date": date,
        "count": 0,
        "last_card_id": None,
        "last_trigger_at": None,
    }


def read() -> dict[str, Any]:
    today = _today_iso()
    if not TODAY_COUNT_PATH.is_file():
        return _empty_record(today)
    try:
        data = json.loads(TODAY_COUNT_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return _empty_record(today)

    if not isinstance(data, dict):
        return _empty_record(today)
    if data.get("date") != today:
        _rollover(data)
        return _empty_record(today)

    data.setdefault("count", 0)
    data.setdefault("last_card_id", None)
    data.setdefault("last_trigger_at", None)
    return data


def _rollover(old: dict[str, Any]) -> None:
    try:
        _atomic_write(BACKUP_PATH, old)
        try:
            os.unlink(TODAY_COUNT_PATH)
        except OSError:
            pass
    except OSError:
        pass


def bump(card_id: str | None = None, *, disabled: bool | None = None) -> dict[str, Any]:
    if disabled is None:
        disabled = os.environ.get("SHARE_STATUSLINE", "").strip().lower() == "off"
    if disabled:
        return read()

    record = read()
    record["count"] = int(record.get("count", 0)) + 1
    if card_id:
        record["last_card_id"] = card_id
    record["last_trigger_at"] = _now_local_iso()
    try:
        _atomic_write(TODAY_COUNT_PATH, record)
    except OSError:
        return record
    return record


def reset() -> dict[str, Any]:
    record = _empty_record(_today_iso())
    try:
        _atomic_write(TODAY_COUNT_PATH, record)
    except OSError:
        pass
    return record


def mark_in_flight() -> None:
    return None
