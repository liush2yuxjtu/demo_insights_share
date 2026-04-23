"""insightsd search_cards ranking 单元测试（P1 修 Jaccard-only → coverage + tag bonus）。

运行：./.venv/bin/python -m pytest test_search_ranking.py -q
不走网络，不启 daemon，直接对 search_cards 传 fixture cards 做排序断言。

背景：原 search_cards 纯 Jaccard `|inter|/|union|` 对长卡惩罚过重。
postgres prompt 下本该命中的 alice-pgpool-2026-04-10（内容丰富=union 大）
被短卡如 m1-project-001 超越，导致 trigger_rate FN 大量堆积。

修法：
- 主分 = max(Jaccard, coverage=|inter|/|query|)，长卡也能靠 coverage 爬上来
- 辅分 = 0.3 * (|query ∩ card_tags| / |query|)，tag 高信号加权

本文件用 20 cases 中的 postgres/celery/redis canonical + 2 条 negative，
锁"修完以后 alice-pgpool / alice-celery-retry / carol-redis-eviction
必须是对应 query 的 top1，无关 query 不得伪命中"的契约。
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from insightsd.store import search_cards


SEEDS_DIR = Path(__file__).resolve().parent / "seeds"


def _load_seed(name: str) -> dict:
    return json.loads((SEEDS_DIR / name).read_text(encoding="utf-8"))


@pytest.fixture
def canonical_cards() -> list[dict]:
    """cases.yml 里期望命中的 3 张 canonical cards + 2 张干扰短卡。"""
    alice_pg = _load_seed("alice_pgpool.json")
    alice_celery = _load_seed("alice_celery_retry.json")
    carol_redis = _load_seed("carol_redis_eviction.json")
    # 干扰短卡：tokens 少、但与无关 query 高 Jaccard 易造 FP
    distractor_short_1 = {
        "id": "m1-project-001",
        "title": "Demo project bootstrap",
        "tags": ["demo", "bootstrap"],
        "body": "Run start.demo.sh",
    }
    distractor_short_2 = {
        "id": "m1-error-fix-002",
        "title": "Shell error fix",
        "tags": ["shell", "error"],
        "body": "zsh rc typo",
    }
    return [alice_pg, alice_celery, carol_redis, distractor_short_1, distractor_short_2]


def test_postgres_pool_query_ranks_alice_pgpool_top1(canonical_cards):
    """t01: 典型 postgres 连接池耗尽 query → alice-pgpool top1"""
    hits = search_cards(
        canonical_cards,
        "Our checkout API is timing out, postgres is rejecting new connections during the lunch spike",
        k=3,
    )
    assert hits, "expect non-empty hits"
    assert hits[0]["id"] == "alice-pgpool-2026-04-10", (
        f"top1 should be alice-pgpool, got {hits[0]['id']} score={hits[0]['score']}"
    )


def test_pgbouncer_query_ranks_alice_pgpool_top1(canonical_cards):
    """t02: pgbouncer + p99 spike query → alice-pgpool top1"""
    hits = search_cards(
        canonical_cards,
        "pgbouncer transaction pooling mode 下 p99 飙高，日志里 remaining connection slots reserved",
        k=3,
    )
    assert hits
    assert hits[0]["id"] == "alice-pgpool-2026-04-10"


def test_celery_retry_query_ranks_alice_celery_top1(canonical_cards):
    """t05: celery retry storm query → alice-celery-retry top1"""
    hits = search_cards(
        canonical_cards,
        "celery workers stuck in retry loop hammering redis broker, queue backlog is exploding",
        k=3,
    )
    assert hits
    assert hits[0]["id"] == "alice-celery-retry-2026-04-08"


def test_redis_eviction_query_ranks_carol_redis_top1(canonical_cards):
    """t08: redis lru session evict query → carol-redis-eviction top1"""
    hits = search_cards(
        canonical_cards,
        "用户随机被登出，redis 的 allkeys-lru 把 session key 也给 evict 了",
        k=3,
    )
    assert hits
    assert hits[0]["id"] == "carol-redis-eviction-2026-03-27"


def test_tailwind_query_does_not_trigger_canonical(canonical_cards):
    """t11 negative: 纯前端样式 query → 不应把 alice/carol 卡顶到高分（score 应 < 0.15）"""
    hits = search_cards(
        canonical_cards,
        "Tailwind dark mode 切换后按钮 hover 态失效，要改哪些 class",
        k=3,
    )
    # 允许有 hit（干扰短卡可能命中），但 canonical 3 张不得 top1 且分数必须低
    canonical_ids = {
        "alice-pgpool-2026-04-10",
        "alice-celery-retry-2026-04-08",
        "carol-redis-eviction-2026-03-27",
    }
    if hits:
        top = hits[0]
        # 契约：canonical 不得被 tailwind query 触发到高分 top1
        if top["id"] in canonical_ids:
            assert top["score"] < 0.15, (
                f"canonical {top['id']} should not hit tailwind query with score {top['score']}"
            )


def test_git_rebase_query_stays_low(canonical_cards):
    """t12 negative: git rebase query → canonical 卡分数必须 < 0.15"""
    hits = search_cards(
        canonical_cards,
        "git rebase onto main 之后怎么把一堆 fixup commits squash 成一个",
        k=3,
    )
    canonical_ids = {
        "alice-pgpool-2026-04-10",
        "alice-celery-retry-2026-04-08",
        "carol-redis-eviction-2026-03-27",
    }
    for hit in hits:
        if hit["id"] in canonical_ids:
            assert hit["score"] < 0.15, (
                f"canonical {hit['id']} leaked into git rebase query score={hit['score']}"
            )
