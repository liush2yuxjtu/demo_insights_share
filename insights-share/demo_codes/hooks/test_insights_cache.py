"""insights_cache.persist 的 smoke test。

直接 python 跑(无需 pytest):
    python insights-share/demo_codes/hooks/test_insights_cache.py

断言:
1. persist 写入的卡片文件确实存在
2. manifest.json 的 cards 包含该 id,last_sync_at 非空
3. 重复 persist 同一 id 不会重复入 cards 列表
4. 缺 id 字段时用 wiki_type/item 拼接出 id
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# 让脚本能 import 同目录的 insights_cache
sys.path.insert(0, str(Path(__file__).resolve().parent))

from insights_cache import (  # noqa: E402
    CACHE_DIR,
    MANIFEST_PATH,
    list_cached,
    persist,
)


def _read_manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def test_persist_basic() -> None:
    card = {
        "id": "t1",
        "title": "Bob 午饭尖峰 PgBouncer 连接池耗尽",
        "wiki_type": "incident",
        "item": "postgres-pool-exhaustion",
        "score": 0.87,
    }
    path = persist(card)
    assert path.exists(), f"card file not created: {path}"
    expected = CACHE_DIR / "t1.json"
    assert path == expected, f"path mismatch: {path} != {expected}"

    saved = json.loads(path.read_text(encoding="utf-8"))
    assert saved["title"] == card["title"], "card content mismatch"

    manifest = _read_manifest()
    assert "t1" in manifest["cards"], f"t1 not in manifest cards: {manifest}"
    assert manifest["last_sync_at"], "last_sync_at empty"
    print(f"[OK] test_persist_basic: {path}")


def test_persist_dedupe() -> None:
    card = {"id": "t1", "title": "更新版本", "wiki_type": "incident", "item": "x"}
    persist(card)
    persist(card)
    cards = list_cached()
    assert cards.count("t1") == 1, f"t1 duplicated in manifest: {cards}"
    print("[OK] test_persist_dedupe: t1 仅出现一次")


def test_persist_without_id() -> None:
    card = {
        "wiki_type": "playbook",
        "item": "pgbouncer-tuning",
        "title": "PgBouncer 调优手册",
    }
    path = persist(card)
    assert path.exists(), f"card file not created: {path}"
    expected_id = "playbook_pgbouncer-tuning"
    assert path.name == f"{expected_id}.json", f"unexpected filename: {path.name}"
    assert expected_id in list_cached(), "manifest missing fallback id"
    print(f"[OK] test_persist_without_id: {path.name}")


def test_persist_rejects_non_dict() -> None:
    try:
        persist("not a dict")  # type: ignore[arg-type]
    except TypeError as exc:
        print(f"[OK] test_persist_rejects_non_dict: {exc}")
        return
    raise AssertionError("expected TypeError for non-dict card")


def main() -> int:
    print(f"cache dir: {CACHE_DIR}")
    print(f"manifest:  {MANIFEST_PATH}")
    test_persist_basic()
    test_persist_dedupe()
    test_persist_without_id()
    test_persist_rejects_non_dict()
    print("\n[ALL PASSED] insights_cache smoke test")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
