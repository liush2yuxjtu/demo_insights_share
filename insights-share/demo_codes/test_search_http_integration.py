"""HTTP 端到端 integration test：起真 daemon + 查 canonical 卡片 + 验证 top1。

运行：./.venv/bin/python -m pytest test_search_http_integration.py -q

背景（P3 回归防护）：
- validation.md §1 要求 20 触发用例（12 训 / 8 测）持续优化触发率
- P1 修复后 train recall=1.0 (6/6 canonical 全 TP)，test recall=0.75
- 本文件只断言 3 条核心 canonical top1 命中，守住最低底线不回退

跑的是独立端口 7841 的 tree-mode daemon，避免污染实机 :7821 / demo :7831。
"""
from __future__ import annotations

import json
import os
import signal
import socket
import subprocess
import time
import urllib.parse
import urllib.request
from pathlib import Path

import pytest


DEMO_CODES = Path(__file__).resolve().parent
TEST_PORT = 7841
TEST_HOST = "127.0.0.1"


def _port_listening(port: int) -> bool:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.3)
    try:
        s.connect((TEST_HOST, port))
        return True
    except OSError:
        return False
    finally:
        s.close()


@pytest.fixture(scope="module")
def tree_daemon():
    """起真 daemon 进 tree mode 指向 wiki_tree/，测试结束 kill。"""
    venv_py = DEMO_CODES / ".venv" / "bin" / "python"
    if not venv_py.is_file():
        pytest.skip("demo venv 不在（未 bootstrap）")
    log_path = Path("/tmp/test_search_http_integration.log")
    proc = subprocess.Popen(
        [
            str(venv_py),
            "insights_cli.py",
            "serve",
            "--host",
            TEST_HOST,
            "--port",
            str(TEST_PORT),
            "--store",
            "wiki_tree",
            "--store-mode",
            "tree",
        ],
        cwd=str(DEMO_CODES),
        stdout=log_path.open("w"),
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    for _ in range(25):
        if _port_listening(TEST_PORT):
            break
        time.sleep(0.2)
    else:
        proc.kill()
        pytest.fail(f"tree daemon 未起（log: {log_path}）")
    yield f"http://{TEST_HOST}:{TEST_PORT}"
    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
    except ProcessLookupError:
        pass
    proc.wait(timeout=5)


def _search(base: str, q: str, k: int = 3) -> list[dict]:
    url = f"{base}/search?" + urllib.parse.urlencode({"q": q, "k": k})
    with urllib.request.urlopen(url, timeout=5.0) as resp:
        return json.loads(resp.read().decode("utf-8")).get("hits") or []


def test_healthz_alive(tree_daemon):
    url = f"{tree_daemon}/healthz"
    with urllib.request.urlopen(url, timeout=5.0) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    assert body.get("ok") is True


def test_insights_returns_canonical_seeds(tree_daemon):
    """tree mode 必须把 canonical 3 张 seed 卡片加载进 store。"""
    url = f"{tree_daemon}/insights"
    with urllib.request.urlopen(url, timeout=5.0) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    ids = {c.get("id") for c in (data.get("cards") or [])}
    assert "alice-pgpool-2026-04-10" in ids, "alice-pgpool canonical 未加载"
    assert "alice-celery-retry-2026-04-08" in ids, "alice-celery-retry canonical 未加载"
    assert "carol-redis-eviction-2026-03-27" in ids, "carol-redis-eviction canonical 未加载"


def test_postgres_checkout_query_top1_alice_pgpool(tree_daemon):
    """t01（cases.yml）：postgres 午餐高峰连接池 query → alice-pgpool top1"""
    hits = _search(
        tree_daemon,
        "Our checkout API is timing out, postgres is rejecting new connections during the lunch spike",
    )
    assert hits, "daemon 必须返非空 hits"
    assert hits[0]["id"] == "alice-pgpool-2026-04-10", (
        f"top1 应为 alice-pgpool，实际 {hits[0]['id']} score={hits[0]['score']}"
    )


def test_celery_retry_query_top1_alice_celery(tree_daemon):
    """t05: celery retry storm → alice-celery-retry top1"""
    hits = _search(
        tree_daemon,
        "celery workers stuck in retry loop hammering redis broker, queue backlog is exploding",
    )
    assert hits
    assert hits[0]["id"] == "alice-celery-retry-2026-04-08"


def test_redis_eviction_query_top1_carol_redis(tree_daemon):
    """t08: redis allkeys-lru 踢 session → carol-redis-eviction top1"""
    hits = _search(
        tree_daemon,
        "用户随机被登出，redis 的 allkeys-lru 把 session key 也给 evict 了",
    )
    assert hits
    assert hits[0]["id"] == "carol-redis-eviction-2026-03-27"


def test_unrelated_tailwind_query_no_canonical_top1(tree_daemon):
    """t11 negative: 纯前端样式不得把 canonical 顶 top1"""
    hits = _search(
        tree_daemon,
        "Tailwind dark mode 切换后按钮 hover 态失效，要改哪些 class",
    )
    canonical = {
        "alice-pgpool-2026-04-10",
        "alice-celery-retry-2026-04-08",
        "carol-redis-eviction-2026-03-27",
    }
    if hits:
        assert hits[0]["id"] not in canonical, (
            f"Tailwind query 不得把 canonical 顶 top1，实际 {hits[0]['id']}"
        )
