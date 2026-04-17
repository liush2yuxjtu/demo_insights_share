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


class FakeTerminal:
    def __init__(self) -> None:
        self.inputs: list[dict[str, object]] = []

    def tmux_summary(self, *, input_enabled: bool) -> dict:
        return {
            "available": True,
            "connected": True,
            "input_enabled": input_enabled,
            "panes": [
                {
                    "target": "demo:0.0",
                    "session": "demo",
                    "window": "main",
                    "command": "claude",
                    "title": "Claude Code",
                }
            ],
        }

    def capture_tmux(self, target: str, *, lines: int = 240) -> dict:
        return {
            "target": target,
            "content": "❯ hello from tmux\n\n⏺ HI！",
            "updated_at": "2026-04-16T18:00:00+08:00",
            "lines": lines,
        }

    def send_tmux_input(
        self,
        target: str,
        *,
        text: str | None = None,
        enter: bool = True,
        control: str | None = None,
    ) -> None:
        self.inputs.append(
            {
                "target": target,
                "text": text,
                "enter": enter,
                "control": control,
            }
        )


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
def terminal() -> FakeTerminal:
    return FakeTerminal()


@pytest.fixture
def httpd(
    store: TreeInsightStore,
    runtime: RuntimeStore,
    terminal: FakeTerminal,
) -> tuple[ThreadingHTTPServer, str, int]:
    handler_cls = _make_handler(
        store,
        runtime=runtime,
        app_root=Path(__file__).resolve().parents[1],
        terminal=terminal,
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


def test_cli_page_and_tmux_routes(
    httpd: tuple[ThreadingHTTPServer, str, int],
    terminal: FakeTerminal,
) -> None:
    _, host, port = httpd

    conn = HTTPConnection(host, port, timeout=5)
    conn.request("GET", "/cli")
    page = conn.getresponse()
    html = page.read().decode("utf-8")
    conn.close()
    assert page.status == 200
    assert "Claude Code CLI 窗口" in html
    assert "tmux 直播" in html

    conn = HTTPConnection(host, port, timeout=5)
    conn.request("GET", "/api/cli/tmux/summary")
    summary = conn.getresponse()
    payload = _body_json(summary)
    conn.close()
    assert summary.status == 200
    assert payload["connected"] is True
    assert payload["panes"][0]["target"] == "demo:0.0"

    conn = HTTPConnection(host, port, timeout=5)
    conn.request("GET", "/api/cli/tmux?target=demo%3A0.0&lines=120")
    capture = conn.getresponse()
    capture_payload = _body_json(capture)
    conn.close()
    assert capture.status == 200
    assert "hello from tmux" in capture_payload["content"]

    conn = HTTPConnection(host, port, timeout=5)
    conn.request(
        "POST",
        "/api/cli/tmux/input",
        body=json.dumps({"target": "demo:0.0", "text": "status", "enter": True}).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
    )
    sent = conn.getresponse()
    sent.read()
    conn.close()
    assert sent.status == 202
    assert terminal.inputs[-1]["text"] == "status"
