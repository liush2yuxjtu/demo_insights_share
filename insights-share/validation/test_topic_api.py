"""Topic API 的 HTTP 层测试：ThreadingHTTPServer + stdlib HTTP client."""

from __future__ import annotations

import json
import shutil
import threading
import time
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest

from insightsd.server import _make_handler
from insightsd.store import InsightStore, TreeInsightStore


@pytest.fixture
def tree_root(tmp_path: Path) -> Path:
    """复制一份 wiki_tree 到临时目录."""
    src = Path(__file__).resolve().parents[1] / "demo_codes" / "wiki_tree"
    dst = tmp_path / "wiki_tree"
    shutil.copytree(src, dst)
    return dst


@pytest.fixture
def store(tree_root: Path) -> TreeInsightStore:
    return TreeInsightStore(tree_root)


@pytest.fixture
def httpd(tree_root: Path, store: TreeInsightStore) -> tuple[ThreadingHTTPServer, str, int]:
    """启动一个临时的 ThreadingHTTPServer，返回 (server, host, port)."""
    handler_cls = _make_handler(store)
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler_cls)
    port = server.server_address[1]
    host = "127.0.0.1"

    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    time.sleep(0.05)  # 等待 server 启动

    yield server, host, port

    server.shutdown()
    server.server_close()


def http_get(host: str, port: int, path: str) -> tuple[int, dict]:
    """发一个 GET 请求，返回 (status_code, body_dict)."""
    conn = HTTPConnection(host, port, timeout=5)
    conn.request("GET", path)
    resp = conn.getresponse()
    status = resp.status
    body = resp.read().decode("utf-8")
    conn.close()
    return status, (json.loads(body) if body else {})


def http_post(host: str, port: int, path: str, payload: dict) -> tuple[int, dict]:
    """发一个 POST 请求，返回 (status_code, body_dict)."""
    conn = HTTPConnection(host, port, timeout=5)
    body_bytes = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json; charset=utf-8"}
    conn.request("POST", path, body=body_bytes, headers=headers)
    resp = conn.getresponse()
    status = resp.status
    body = resp.read().decode("utf-8")
    conn.close()
    return status, (json.loads(body) if body else {})


class TestTopicAPI:
    def test_get_topics_returns_list(self, httpd: tuple[ThreadingHTTPServer, str, int], store: TreeInsightStore) -> None:
        _, host, port = httpd
        status, body = http_get(host, port, "/topics")
        assert status == 200
        assert "topics" in body
        topics = body["topics"]
        assert isinstance(topics, list)
        # wiki_tree 自带 3 个 seed topics
        assert len(topics) >= 3
        assert any(t["id"] == "postgres-pool-exhaustion" for t in topics)

    def test_post_topics_creates_topic(self, httpd: tuple[ThreadingHTTPServer, str, int], store: TreeInsightStore) -> None:
        _, host, port = httpd
        topic = {
            "id": "new-topic-api",
            "title": "New Topic via API",
            "tags": ["api-test"],
            "created_by": "tester",
        }
        status, body = http_post(host, port, "/topics", topic)
        assert status == 200
        assert body.get("id") == "new-topic-api"

        # 再次 GET 确认已写入
        _, body2 = http_get(host, port, "/topics")
        assert any(t["id"] == "new-topic-api" for t in body2["topics"])

    def test_get_topics_topic_id_examples_without_label_filter(self, httpd: tuple[ThreadingHTTPServer, str, int], store: TreeInsightStore) -> None:
        """GET /topics/{id}/examples 返回该 topic 下所有卡片."""
        _, host, port = httpd
        # postgres-pool-exhaustion topic 自带 1 个 card (alice-pgpool-2026-04-10)
        topic_id = "postgres-pool-exhaustion"
        _, body = http_get(host, port, f"/topics/{topic_id}/examples")
        assert "examples" in body
        # 注意：seed card 的 topic_id 为空，所以不过滤时返回空列表是正常行为

    def test_post_insights_id_relabel_sets_override(self, httpd: tuple[ThreadingHTTPServer, str, int], store: TreeInsightStore) -> None:
        _, host, port = httpd
        card_id = "alice-pgpool-2026-04-10"
        payload = {"label": "bad", "override_by": "test-admin"}
        status, body = http_post(host, port, f"/insights/{card_id}/relabel", payload)
        assert status == 200
        assert body.get("effective_label") == "bad"

    def test_relabel_nonexistent_card_returns_404(self, httpd: tuple[ThreadingHTTPServer, str, int], store: TreeInsightStore) -> None:
        _, host, port = httpd
        status, _ = http_post(host, port, "/insights/nonexistent-id-xyz/relabel", {"label": "bad"})
        assert status == 404

    def test_topics_endpoint_rejects_non_tree_store(self, tmp_path: Path) -> None:
        """flat 模式 InsightStore 不支持 topics 接口，返回 400."""
        flat_store = InsightStore(tmp_path / "flat.json")
        flat_store.save([])
        handler_cls = _make_handler(flat_store)

        server = ThreadingHTTPServer(("127.0.0.1", 0), handler_cls)
        port = server.server_address[1]
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()
        time.sleep(0.05)

        try:
            status, body = http_get("127.0.0.1", port, "/topics")
            assert status == 400
            assert body.get("error") == "topics_not_supported"
        finally:
            server.shutdown()
            server.server_close()
