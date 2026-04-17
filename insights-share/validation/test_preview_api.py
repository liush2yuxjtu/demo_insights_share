from __future__ import annotations

import json
import shutil
import threading
import time
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest

from insightsd.runtime import RuntimeStore
from insightsd.server import _make_handler
from insightsd.store import TreeInsightStore


def _body_json(resp) -> dict:
    raw = resp.read().decode("utf-8")
    return json.loads(raw) if raw else {}


@pytest.fixture
def tree_root(tmp_path: Path) -> Path:
    src = Path(__file__).resolve().parents[1] / "demo_codes" / "wiki_tree"
    dst = tmp_path / "wiki_tree"
    shutil.copytree(src, dst)
    return dst


@pytest.fixture
def store(tree_root: Path) -> TreeInsightStore:
    return TreeInsightStore(tree_root)


@pytest.fixture
def runtime(tmp_path: Path) -> RuntimeStore:
    return RuntimeStore(tmp_path / "runtime", runner_enabled=True, internal_token="test-token")


@pytest.fixture
def httpd(
    tree_root: Path,
    store: TreeInsightStore,
    runtime: RuntimeStore,
) -> tuple[ThreadingHTTPServer, str, int]:
    handler_cls = _make_handler(
        store,
        runtime=runtime,
        app_root=Path(__file__).resolve().parents[1],
    )
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler_cls)
    port = server.server_address[1]
    host = "127.0.0.1"

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.05)

    yield server, host, port

    server.shutdown()
    server.server_close()


def test_preview_and_ops_pages_are_served(httpd: tuple[ThreadingHTTPServer, str, int]) -> None:
    _, host, port = httpd

    conn = HTTPConnection(host, port, timeout=5)
    conn.request("GET", "/")
    home = conn.getresponse()
    home_html = home.read().decode("utf-8")
    conn.close()
    assert home.status == 200
    assert "Web 控制台" in home_html
    assert "Claude Code CLI" in home_html

    conn = HTTPConnection(host, port, timeout=5)
    conn.request("GET", "/preview")
    preview = conn.getresponse()
    preview_html = preview.read().decode("utf-8")
    conn.close()
    assert preview.status == 200
    assert "Preview 模式" in preview_html
    assert "/api/stream" in preview_html
    assert "Claude Code CLI" in preview_html

    conn = HTTPConnection(host, port, timeout=5)
    conn.request("GET", "/ops")
    ops = conn.getresponse()
    ops_html = ops.read().decode("utf-8")
    conn.close()
    assert ops.status == 200
    assert "Ops 模式" in ops_html
    assert "Claude Code CLI" in ops_html

    conn = HTTPConnection(host, port, timeout=5)
    conn.request("GET", "/dashboard")
    dash = conn.getresponse()
    dash_html = dash.read().decode("utf-8")
    conn.close()
    assert dash.status == 200
    assert "Web 控制台" in dash_html


def test_session_endpoints_return_runtime_state(
    httpd: tuple[ThreadingHTTPServer, str, int],
    runtime: RuntimeStore,
) -> None:
    _, host, port = httpd
    session = runtime.start_session(kind="demo", title="实时演示")
    runtime.append_event(
        session["id"],
        stage="search",
        status="ok",
        source="search",
        message="命中 alice-pgpool-2026-04-10",
        metrics={"score": 0.87},
    )

    conn = HTTPConnection(host, port, timeout=5)
    conn.request("GET", "/api/sessions?kind=demo&limit=5")
    resp = conn.getresponse()
    payload = _body_json(resp)
    conn.close()
    assert resp.status == 200
    assert payload["sessions"][0]["id"] == session["id"]

    conn = HTTPConnection(host, port, timeout=5)
    conn.request("GET", f"/api/sessions/{session['id']}")
    resp = conn.getresponse()
    session_payload = _body_json(resp)
    conn.close()
    assert resp.status == 200
    assert session_payload["session"]["current_stage"] == "search"

    conn = HTTPConnection(host, port, timeout=5)
    conn.request("GET", f"/api/sessions/{session['id']}/events")
    resp = conn.getresponse()
    events_payload = _body_json(resp)
    conn.close()
    assert resp.status == 200
    assert events_payload["events"][0]["stage"] == "search"


def test_system_summary_and_internal_event_endpoint(
    httpd: tuple[ThreadingHTTPServer, str, int],
    runtime: RuntimeStore,
) -> None:
    _, host, port = httpd
    session = runtime.start_session(kind="validation", title="Phase 运行")

    conn = HTTPConnection(host, port, timeout=5)
    conn.request("GET", "/api/system/summary")
    resp = conn.getresponse()
    summary = _body_json(resp)
    conn.close()
    assert resp.status == 200
    assert summary["runner_enabled"] is True
    assert summary["counts"]["total"] >= 1

    conn = HTTPConnection(host, port, timeout=5)
    conn.request(
        "POST",
        "/_events",
        body=json.dumps(
            {
                "session_id": session["id"],
                "stage": "phase1",
                "status": "running",
                "source": "runner",
                "message": "phase1 检查中",
            }
        ).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
    )
    forbidden = conn.getresponse()
    forbidden.read()
    conn.close()
    assert forbidden.status == 403

    conn = HTTPConnection(host, port, timeout=5)
    conn.request(
        "POST",
        "/_events",
        body=json.dumps(
            {
                "session_id": session["id"],
                "stage": "phase1",
                "status": "running",
                "source": "runner",
                "message": "phase1 检查中",
            }
        ).encode("utf-8"),
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "X-Insights-Token": "test-token",
        },
    )
    accepted = conn.getresponse()
    accepted.read()
    conn.close()
    assert accepted.status == 202

    events = runtime.get_events(session["id"])
    assert events[-1]["stage"] == "phase1"


def test_stream_and_run_endpoints_emit_live_updates(
    httpd: tuple[ThreadingHTTPServer, str, int],
) -> None:
    _, host, port = httpd

    stream_conn = HTTPConnection(host, port, timeout=5)
    stream_conn.request("GET", "/api/stream")
    stream_resp = stream_conn.getresponse()
    assert stream_resp.status == 200

    conn = HTTPConnection(host, port, timeout=5)
    conn.request(
        "POST",
        "/api/runs/demo",
        body=json.dumps({"problem": "postgres 连接池耗尽"}).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
    )
    demo_resp = conn.getresponse()
    demo_payload = _body_json(demo_resp)
    conn.close()
    assert demo_resp.status == 202
    demo_session_id = demo_payload["session_id"]

    deadline = time.time() + 3
    stream_text = ""
    while time.time() < deadline and "session.update" not in stream_text:
        stream_text += stream_resp.fp.readline().decode("utf-8")
    assert "session.update" in stream_text

    deadline = time.time() + 3
    stages: set[str] = set()
    while time.time() < deadline:
        conn = HTTPConnection(host, port, timeout=5)
        conn.request("GET", f"/api/sessions/{demo_session_id}/events")
        resp = conn.getresponse()
        payload = _body_json(resp)
        conn.close()
        stages = {event["stage"] for event in payload["events"]}
        if {"bootstrap", "search", "result", "summary"} <= stages:
            break
        time.sleep(0.1)
    assert {"bootstrap", "search", "result", "summary"} <= stages

    conn = HTTPConnection(host, port, timeout=5)
    conn.request(
        "POST",
        "/api/runs/validation",
        body=json.dumps({}).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
    )
    validation_resp = conn.getresponse()
    validation_payload = _body_json(validation_resp)
    conn.close()
    assert validation_resp.status == 202
    validation_session_id = validation_payload["session_id"]

    deadline = time.time() + 3
    validation_stages: set[str] = set()
    while time.time() < deadline:
        conn = HTTPConnection(host, port, timeout=5)
        conn.request("GET", f"/api/sessions/{validation_session_id}/events")
        resp = conn.getresponse()
        payload = _body_json(resp)
        conn.close()
        validation_stages = {event["stage"] for event in payload["events"]}
        if {"phase0", "phase5", "summary"} <= validation_stages:
            break
        time.sleep(0.1)
    assert {"phase0", "phase5", "summary"} <= validation_stages

    stream_resp.close()
    stream_conn.close()


def test_demo_runner_does_not_mutate_tree_store(
    httpd: tuple[ThreadingHTTPServer, str, int],
    tree_root: Path,
) -> None:
    _, host, port = httpd
    before = {
        path.relative_to(tree_root).as_posix(): path.read_text(encoding="utf-8")
        for path in tree_root.rglob("*")
        if path.is_file()
    }

    conn = HTTPConnection(host, port, timeout=5)
    conn.request(
        "POST",
        "/api/runs/demo",
        body=json.dumps({"problem": "postgres 连接池耗尽"}).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
    )
    resp = conn.getresponse()
    payload = _body_json(resp)
    conn.close()
    assert resp.status == 202
    session_id = payload["session_id"]

    deadline = time.time() + 3
    status = ""
    while time.time() < deadline:
        conn = HTTPConnection(host, port, timeout=5)
        conn.request("GET", f"/api/sessions/{session_id}")
        session_resp = conn.getresponse()
        session_payload = _body_json(session_resp)
        conn.close()
        status = session_payload["session"]["status"]
        if status in {"completed", "failed"}:
            break
        time.sleep(0.1)
    assert status == "completed"

    after = {
        path.relative_to(tree_root).as_posix(): path.read_text(encoding="utf-8")
        for path in tree_root.rglob("*")
        if path.is_file()
    }
    assert after == before
