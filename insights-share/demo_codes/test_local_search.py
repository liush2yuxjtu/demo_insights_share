"""local_search 单元测试。

对齐 proposal_generation_latency.md M7 cache-miss 优化：
- 分词覆盖 ASCII + CJK bigram
- topics.json + INDEX.md 候选合并、去重
- Jaccard 排序稳定 + priority desc 作为 tiebreak
- threshold 切 local / local_low 两档

运行：./.venv/bin/python -m pytest test_local_search.py -q
不走网络、不加载 MiniMax SDK。
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from local_search import (
    DEFAULT_SCORE_THRESHOLD,
    _jaccard,
    _tokenize,
    search,
)


# ---------- fixtures ----------


@pytest.fixture
def tiny_wiki(tmp_path: Path) -> Path:
    root = tmp_path / "wiki_tree"
    (root / "database").mkdir(parents=True)
    (root / "shell_env").mkdir(parents=True)
    (root / "database" / "INDEX.md").write_text(
        "# database · INDEX\n\n"
        "| name | description | trigger when | docs |\n"
        "|------|-------------|--------------|------|\n"
        "| postgres_pool | PostgreSQL pool exhaustion | postgres,latency | [x](x.md) |\n"
        "| mysql_deadlock | MySQL row-lock deadlock | mysql,deadlock | [x](x.md) |\n",
        encoding="utf-8",
    )
    (root / "shell_env" / "INDEX.md").write_text(
        "# shell_env · INDEX\n\n"
        "| name | description | trigger when | docs |\n"
        "|------|-------------|--------------|------|\n"
        "| tmux嵌套环境变量 | tmux nested unset | nested,tmux | [x](x.md) |\n",
        encoding="utf-8",
    )
    (root / "topics.json").write_text(
        json.dumps(
            {
                "topics": [
                    {
                        "id": "postgres-pool-exhaustion",
                        "title": "PostgreSQL 连接池耗尽",
                        "tags": ["postgres", "connection-pool", "latency"],
                        "wiki_type": "database",
                        "created_at": "2026-04-10T08:00:00Z",
                        "priority": 5,
                    },
                    {
                        "id": "m1-tmux嵌套环境变量",
                        "title": "tmux嵌套环境变量",
                        "tags": ["tmux", "nested"],
                        "wiki_type": "shell_env",
                        "created_at": "2026-04-18T00:00:00Z",
                    },
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return root


# ---------- tokenize / jaccard ----------


def test_tokenize_ascii_only_keeps_slugs():
    toks = _tokenize("postgres connection pool")
    assert "postgres" in toks
    assert "connection" in toks
    assert "pool" in toks


def test_tokenize_cjk_emits_bigrams():
    toks = _tokenize("连接池耗尽")
    assert "连接" in toks
    assert "接池" in toks
    assert "池耗" in toks
    assert "耗尽" in toks


def test_tokenize_drops_stopwords_and_short_ascii():
    toks = _tokenize("the a big cat")
    assert "the" not in toks
    assert "a" not in toks
    assert "big" in toks
    assert "cat" in toks


def test_jaccard_identical_sets_is_one():
    s = {"a", "b", "c"}
    assert _jaccard(s, s) == 1.0


def test_jaccard_disjoint_sets_is_zero():
    assert _jaccard({"a"}, {"b"}) == 0.0


# ---------- search: short-circuit path ----------


def test_search_high_overlap_hits_topics_json(tiny_wiki):
    result = search("PostgreSQL 连接池耗尽", tiny_wiki)
    assert result["source"] == "local"
    top = result["hits"][0]
    assert top["wiki_type"] == "database"
    assert top["item"] == "postgres-pool-exhaustion"
    assert top["score"] >= DEFAULT_SCORE_THRESHOLD


def test_search_english_query_falls_to_index_md(tiny_wiki):
    result = search("postgres pool", tiny_wiki)
    top = result["hits"][0]
    # 任一来源都可，只要命中对的 card
    assert top["wiki_type"] == "database"
    assert top["item"] in ("postgres-pool-exhaustion", "postgres_pool")


def test_search_low_overlap_marks_local_low(tiny_wiki):
    result = search("totally unrelated quantum foo bar baz", tiny_wiki)
    assert result["source"] == "local_low"


def test_search_empty_query_returns_empty(tiny_wiki):
    result = search("", tiny_wiki)
    assert result["hits"] == []
    assert result["source"] == "local_low"


def test_search_is_stable_across_calls(tiny_wiki):
    """Determinism gate for proposal_ceo_next_steps.md multi-topic priority."""
    r1 = search("postgres pool", tiny_wiki)
    r2 = search("postgres pool", tiny_wiki)
    r3 = search("postgres pool", tiny_wiki)
    keys1 = [(h["wiki_type"], h["item"]) for h in r1["hits"]]
    keys2 = [(h["wiki_type"], h["item"]) for h in r2["hits"]]
    keys3 = [(h["wiki_type"], h["item"]) for h in r3["hits"]]
    assert keys1 == keys2 == keys3


# ---------- priority tiebreak ----------


def test_priority_breaks_score_ties(tmp_path: Path):
    """两张 topic 分数完全相同时，priority 高的在前。"""
    root = tmp_path / "wt"
    (root / "a").mkdir(parents=True)
    (root / "b").mkdir(parents=True)
    (root / "a" / "INDEX.md").write_text("# a\n", encoding="utf-8")
    (root / "b" / "INDEX.md").write_text("# b\n", encoding="utf-8")
    (root / "topics.json").write_text(
        json.dumps(
            {
                "topics": [
                    {
                        "id": "t-low",
                        "title": "shared-title-token",
                        "tags": ["one", "two"],
                        "wiki_type": "a",
                        "priority": 0,
                        "created_at": "2026-01-01T00:00:00Z",
                    },
                    {
                        "id": "t-high",
                        "title": "shared-title-token",
                        "tags": ["one", "two"],
                        "wiki_type": "b",
                        "priority": 10,
                        "created_at": "2026-04-01T00:00:00Z",
                    },
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    result = search("shared-title-token one two", root)
    # 分数相同 → priority=10 的 t-high 必在前
    assert result["hits"][0]["item"] == "t-high"
    assert result["hits"][1]["item"] == "t-low"


def test_missing_priority_defaults_to_zero(tmp_path: Path):
    """没写 priority 的 topic 当 0 处理；不得抛。"""
    root = tmp_path / "wt"
    (root / "a").mkdir(parents=True)
    (root / "a" / "INDEX.md").write_text("# a\n", encoding="utf-8")
    (root / "topics.json").write_text(
        json.dumps({"topics": [
            {"id": "t", "title": "hello", "tags": ["world"], "wiki_type": "a"}
        ]}, ensure_ascii=False),
        encoding="utf-8",
    )
    result = search("hello world", root)
    assert result["source"] == "local"
    assert result["hits"][0]["item"] == "t"


# ---------- latency budget ----------


def test_search_is_fast(tiny_wiki):
    """Sanity: ≤ 200ms on tiny fixture — real wiki is ~10ms on dev box."""
    import time

    t0 = time.perf_counter()
    for _ in range(5):
        search("PostgreSQL 连接池", tiny_wiki)
    dt_ms = (time.perf_counter() - t0) * 1000 / 5
    assert dt_ms < 200, f"local_search took {dt_ms:.1f}ms per call (> 200ms budget)"
