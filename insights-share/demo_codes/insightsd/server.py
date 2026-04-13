"""Stdlib ThreadingHTTPServer daemon for insight-card sharing."""

from __future__ import annotations

import json
import socket
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit

from .store import InsightStore


def _detect_lan_ip() -> str:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        sock.close()


class InsightHandler(BaseHTTPRequestHandler):
    store: InsightStore  # injected by run()

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        sys.stderr.write(
            f"[insightsd] {self.command} {self.path} -> {args[1] if len(args) > 1 else ''}\n"
        )

    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_404(self) -> None:
        self._send_json(404, {"error": "not_found", "path": self.path})

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlsplit(self.path)
        path = parsed.path
        if path == "/healthz":
            self._send_json(200, {"ok": True})
            return
        if path == "/insights":
            self._send_json(200, {"cards": self.store.list_all()})
            return
        if path == "/search":
            params = parse_qs(parsed.query)
            q = (params.get("q") or [""])[0]
            try:
                k = int((params.get("k") or ["3"])[0])
            except ValueError:
                k = 3
            hits = self.store.search(q, k=k)
            self._send_json(200, {"hits": hits})
            return
        self._send_404()

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlsplit(self.path)
        if parsed.path != "/insights":
            self._send_404()
            return
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length > 0 else b""
        try:
            card = json.loads(raw.decode("utf-8") or "{}")
        except json.JSONDecodeError as exc:
            self._send_json(400, {"error": "invalid_json", "detail": str(exc)})
            return
        try:
            saved = self.store.add(card)
        except ValueError as exc:
            self._send_json(400, {"error": "invalid_card", "detail": str(exc)})
            return
        self._send_json(200, {"id": saved.get("id")})


def _make_handler(store: InsightStore) -> type[InsightHandler]:
    return type("BoundInsightHandler", (InsightHandler,), {"store": store})


def run(
    host: str = "0.0.0.0",
    port: int = 7821,
    store_path: Path = Path("./wiki.json"),
) -> None:
    store = InsightStore(Path(store_path))
    handler_cls = _make_handler(store)
    httpd = ThreadingHTTPServer((host, port), handler_cls)
    lan_ip = _detect_lan_ip()
    sys.stderr.write(f"[insightsd] bound to {host}:{port}\n")
    sys.stderr.write(f"[insightsd] LAN IP detected: {lan_ip}\n")
    sys.stderr.write(
        f"[insightsd] teammates can publish/consume at http://{lan_ip}:{port}\n"
    )
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        sys.stderr.write("[insightsd] shutting down\n")
    finally:
        httpd.server_close()
