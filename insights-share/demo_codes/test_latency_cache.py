"""latency_cache 单元测试。

运行：/usr/bin/python3 -m pytest test_latency_cache.py -q
不走网络，不加载 MiniMax SDK。
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

import pytest

from latency_cache import (
    CACHE_DIR_DEFAULT,
    cache_key,
    cached_search,
    compute_wiki_sha,
    load,
    store,
)


# ---------- fixtures ----------


@pytest.fixture
def fake_wiki(tmp_path: Path) -> Path:
    """最小可计算 sha 的 wiki_tree。"""
    root = tmp_path / "wiki_tree"
    (root / "database").mkdir(parents=True)
    (root / "shell_env").mkdir(parents=True)
    (root / "database" / "INDEX.md").write_text("# database\n", encoding="utf-8")
    (root / "shell_env" / "INDEX.md").write_text("# shell_env\n", encoding="utf-8")
    (root / "topics.json").write_text(
        json.dumps({"topic_a": {"cat": "database"}}, ensure_ascii=False),
        encoding="utf-8",
    )
    return root


@pytest.fixture
def cache_dir(tmp_path: Path) -> Path:
    d = tmp_path / "hits"
    return d


# ---------- compute_wiki_sha ----------


def test_wiki_sha_deterministic(fake_wiki: Path) -> None:
    a = compute_wiki_sha(fake_wiki)
    b = compute_wiki_sha(fake_wiki)
    assert a == b
    # 非空、长度稳定
    assert a and len(a) == 12


def test_wiki_sha_changes_on_topics_update(fake_wiki: Path) -> None:
    a = compute_wiki_sha(fake_wiki)
    (fake_wiki / "topics.json").write_text(
        json.dumps({"topic_a": {"cat": "database"}, "topic_b": {"cat": "shell_env"}}),
        encoding="utf-8",
    )
    b = compute_wiki_sha(fake_wiki)
    assert a != b


# ---------- cache_key ----------


def test_cache_key_deterministic_and_16_hex() -> None:
    k1 = cache_key("hello", "abc123")
    k2 = cache_key("hello", "abc123")
    assert k1 == k2
    assert len(k1) == 16
    assert all(c in "0123456789abcdef" for c in k1)


def test_cache_key_changes_with_query_or_sha() -> None:
    base = cache_key("q", "sha1")
    assert base != cache_key("q2", "sha1")
    assert base != cache_key("q", "sha2")


# ---------- store + load round-trip ----------


def test_store_load_round_trip(fake_wiki: Path, cache_dir: Path) -> None:
    sha = compute_wiki_sha(fake_wiki)
    hits = {
        "query": "postgres 连接池",
        "top_hits": [
            {"card": "database/postgres_连接池.md", "score": 0.91},
        ],
        "turns": 2,
    }
    path = store("postgres 连接池", sha, hits, cache_dir=cache_dir)
    assert path.exists()
    got = load("postgres 连接池", sha, cache_dir=cache_dir, ttl_seconds=300)
    assert got == hits


def test_load_miss_returns_none(fake_wiki: Path, cache_dir: Path) -> None:
    sha = compute_wiki_sha(fake_wiki)
    assert load("never stored", sha, cache_dir=cache_dir) is None


def test_load_on_wiki_sha_mismatch_returns_none(
    fake_wiki: Path, cache_dir: Path
) -> None:
    sha = compute_wiki_sha(fake_wiki)
    store("q", sha, {"x": 1}, cache_dir=cache_dir)
    # wiki 更新导致 sha 变
    (fake_wiki / "topics.json").write_text("{}", encoding="utf-8")
    new_sha = compute_wiki_sha(fake_wiki)
    assert new_sha != sha
    assert load("q", new_sha, cache_dir=cache_dir) is None


def test_load_corrupted_returns_none(fake_wiki: Path, cache_dir: Path) -> None:
    sha = compute_wiki_sha(fake_wiki)
    path = store("q", sha, {"hit": True}, cache_dir=cache_dir)
    path.write_text("{not valid json", encoding="utf-8")
    assert load("q", sha, cache_dir=cache_dir) is None


# ---------- TTL expiry ----------


def test_ttl_expiry_returns_none(fake_wiki: Path, cache_dir: Path) -> None:
    sha = compute_wiki_sha(fake_wiki)
    path = store("q-ttl", sha, {"hits": []}, cache_dir=cache_dir)
    # 把文件 mtime 回拨到 10 分钟前，ttl_seconds=300 应判过期
    old = time.time() - 600
    os.utime(path, (old, old))
    assert load("q-ttl", sha, cache_dir=cache_dir, ttl_seconds=300) is None
    # 但 ttl_seconds=1200 仍在有效期内
    assert load("q-ttl", sha, cache_dir=cache_dir, ttl_seconds=1200) == {"hits": []}


# ---------- cached_search hit/miss counters ----------


def test_cached_search_miss_then_hit(fake_wiki: Path, cache_dir: Path) -> None:
    calls = {"n": 0}

    def fake_runner(q: str, root) -> dict:
        calls["n"] += 1
        return {"query": q, "top_hits": [{"card": "database/pg.md", "score": 0.88}]}

    # 第 1 次：miss，counter ++
    hits1, was_hit1 = cached_search(
        "pg pool", fake_wiki, runner=fake_runner, cache_dir=cache_dir, ttl_seconds=300
    )
    assert was_hit1 is False
    assert calls["n"] == 1
    assert hits1["query"] == "pg pool"

    # 第 2 次：hit，counter 不增
    hits2, was_hit2 = cached_search(
        "pg pool", fake_wiki, runner=fake_runner, cache_dir=cache_dir, ttl_seconds=300
    )
    assert was_hit2 is True
    assert calls["n"] == 1
    assert hits2 == hits1


def test_cached_search_invalidates_on_wiki_change(
    fake_wiki: Path, cache_dir: Path
) -> None:
    calls = {"n": 0}

    def runner(q: str, root) -> dict:
        calls["n"] += 1
        return {"top_hits": [], "run": calls["n"]}

    cached_search("q", fake_wiki, runner=runner, cache_dir=cache_dir)
    assert calls["n"] == 1
    # 改 topics.json → sha 变 → 下一次必须 miss
    (fake_wiki / "topics.json").write_text(
        json.dumps({"new": True}), encoding="utf-8"
    )
    hits, was_hit = cached_search("q", fake_wiki, runner=runner, cache_dir=cache_dir)
    assert was_hit is False
    assert calls["n"] == 2
    assert hits["run"] == 2


def test_cached_search_runner_errors_propagate(
    fake_wiki: Path, cache_dir: Path
) -> None:
    class Boom(RuntimeError):
        pass

    def bad(q: str, root):
        raise Boom("search failed")

    with pytest.raises(Boom):
        cached_search("oops", fake_wiki, runner=bad, cache_dir=cache_dir)


# ---------- 默认常量契约 ----------


def test_cache_dir_default_is_under_insights_share() -> None:
    assert str(CACHE_DIR_DEFAULT).endswith(".cache/insights-share/hits")
