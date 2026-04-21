"""insights-wiki 今日触发计数器。

契约（proposal_statusline.md）：
- 存储：~/.cache/insights-wiki/today_count.json
- 结构：{"date": "YYYY-MM-DD", "count": N, "last_card_id": str|null, "last_trigger_at": iso8601}
- 日切：本地时区 00:00 自然日重置
- 写入：原子 rename，避免 statusline 读到半写
- 调用方：UserPromptSubmit hook 命中任意卡片后 bump(+1)
- A/B 开关：WIKI_STATUSLINE=off 时静默跳过写入

仅 stdlib，和 insights_cache.py 风格一致。
"""
from __future__ import annotations

import datetime as _dt
import json
import os
import tempfile
from pathlib import Path
from typing import Any

CACHE_DIR = Path(os.path.expanduser("~/.cache/insights-wiki"))
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
    """读取当前计数。若文件不存在或日期过期返回今日空记录。

    过期判定：存档 date != 本地今天。此时把旧文件原子 rename 到 .bak，
    然后返回今日空记录。下次 bump 会落盘新记录。
    """
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
    """日切：把昨天的记录 atomic rename 到 .bak。"""
    try:
        _atomic_write(BACKUP_PATH, old)
        try:
            os.unlink(TODAY_COUNT_PATH)
        except OSError:
            pass
    except OSError:
        # rollover 失败不阻塞，下次 bump 仍会正常覆盖
        pass


def bump(card_id: str | None = None, *, disabled: bool | None = None) -> dict[str, Any]:
    """命中一次卡片：count += 1，记录 last_card_id / last_trigger_at，落盘。

    Args:
        card_id: 命中的卡片 ID（可选）
        disabled: 若 True 则不落盘，返回当前 read()。默认从 WIKI_STATUSLINE 环境变量推导
                  （WIKI_STATUSLINE=off 时 disabled=True）

    Returns:
        写入后的 record dict
    """
    if disabled is None:
        disabled = os.environ.get("WIKI_STATUSLINE", "").strip().lower() == "off"
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
        # 写入失败不阻塞上层 hook
        return record
    return record


def reset() -> dict[str, Any]:
    """清零今日记录，主要用于测试。"""
    record = _empty_record(_today_iso())
    try:
        _atomic_write(TODAY_COUNT_PATH, record)
    except OSError:
        pass
    return record


def mark_in_flight() -> None:
    """prompt 正在 prefetch/match 的占位信号。

    statusline 不直接依赖此字段；保留接口给未来 ✓/… 过渡态扩展。
    当前实现：无副作用。
    """
    return None


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="insights-wiki today_count CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("read", help="打印当前 record JSON")
    p_bump = sub.add_parser("bump", help="+1 并落盘")
    p_bump.add_argument("--card-id", default=None)
    sub.add_parser("reset", help="清零今日记录")

    args = parser.parse_args()
    if args.cmd == "read":
        print(json.dumps(read(), ensure_ascii=False, indent=2))
    elif args.cmd == "bump":
        print(json.dumps(bump(args.card_id), ensure_ascii=False, indent=2))
    elif args.cmd == "reset":
        print(json.dumps(reset(), ensure_ascii=False, indent=2))
