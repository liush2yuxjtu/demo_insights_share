"""Stdlib ThreadingHTTPServer daemon for insight-card sharing."""

from __future__ import annotations

import json
import socket
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit

from .store import InsightStore, TreeInsightStore


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
    store: Any  # InsightStore | TreeInsightStore, injected by run()

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

    def _read_json_body(self) -> tuple[dict[str, Any] | None, str | None]:
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length > 0 else b""
        try:
            data = json.loads(raw.decode("utf-8") or "{}")
        except json.JSONDecodeError as exc:
            return None, str(exc)
        if not isinstance(data, dict):
            return None, "body must be a JSON object"
        return data, None

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlsplit(self.path)
        path = parsed.path
        # 根路径 / /dashboard 直接返回同目录下的 dashboard.html
        if path in ("/", "/dashboard"):
            html = Path(__file__).resolve().parent / "dashboard.html"
            if not html.is_file():
                self._send_404()
                return
            body = html.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)
            return
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
        # GET /topics
        if path == "/topics":
            if not isinstance(self.store, TreeInsightStore):
                self._send_json(400, {"error": "topics_not_supported", "detail": "tree mode only"})
                return
            self._send_json(200, {"topics": self.store.list_topics()})
            return
        # GET /topics/{topic_id}/examples?label=...
        if path.startswith("/topics/") and path.endswith("/examples"):
            if not isinstance(self.store, TreeInsightStore):
                self._send_json(400, {"error": "topics_not_supported", "detail": "tree mode only"})
                return
            topic_id = path[len("/topics/"):-len("/examples")]
            params = parse_qs(parsed.query)
            label = (params.get("label") or [None])[0]
            examples = self.store.list_examples(topic_id, label=label)
            self._send_json(200, {"examples": examples})
            return
        self._send_404()

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlsplit(self.path)
        path = parsed.path

        # POST /insights → add
        if path == "/insights":
            card, err = self._read_json_body()
            if err is not None or card is None:
                self._send_json(400, {"error": "invalid_json", "detail": err})
                return
            try:
                if isinstance(self.store, TreeInsightStore):
                    saved = self.store.add(card, wiki_type=card.get("wiki_type") or "general")
                else:
                    saved = self.store.add(card)
            except ValueError as exc:
                self._send_json(400, {"error": "invalid_card", "detail": str(exc)})
                return
            self._send_json(200, {"id": saved.get("id")})
            return

        # POST /insights/merge → merge source into target
        if path == "/insights/merge":
            if not isinstance(self.store, TreeInsightStore):
                self._send_json(400, {"error": "merge_not_supported", "detail": "tree mode only"})
                return
            body, err = self._read_json_body()
            if err is not None or body is None:
                self._send_json(400, {"error": "invalid_json", "detail": err})
                return
            result = self.store.merge(body.get("source_id", ""), body.get("target_id", ""))
            if result is None:
                self._send_json(404, {"error": "not_found", "detail": "source or target missing"})
                return
            self._send_json(200, {"id": result.get("id")})
            return

        # POST /insights/research → agentic search + write new card
        if path == "/insights/research":
            if not isinstance(self.store, TreeInsightStore):
                self._send_json(400, {"error": "research_not_supported", "detail": "tree mode only"})
                return
            body, err = self._read_json_body()
            if err is not None or body is None:
                self._send_json(400, {"error": "invalid_json", "detail": err})
                return
            try:
                result = self.store.research(body.get("query", ""))
            except Exception as exc:
                # 严禁 fallback：异常原样返回 500
                self._send_json(500, {"error": "research_failed", "detail": f"{type(exc).__name__}: {exc}"})
                return
            self._send_json(200, {"id": result.get("id")})
            return

        # POST /insights/{id}/edit → patch fields
        if path.endswith("/edit") and path.startswith("/insights/"):
            if not isinstance(self.store, TreeInsightStore):
                self._send_json(400, {"error": "edit_not_supported", "detail": "tree mode only"})
                return
            card_id = path[len("/insights/") : -len("/edit")]
            patch, err = self._read_json_body()
            if err is not None or patch is None:
                self._send_json(400, {"error": "invalid_json", "detail": err})
                return
            result = self.store.edit(card_id, patch)
            if result is None:
                self._send_json(404, {"error": "not_found", "id": card_id})
                return
            self._send_json(200, {"id": result.get("id")})
            return

        # POST /insights/{id}/tag → add tags (sticky for not_triggered)
        if path.endswith("/tag") and path.startswith("/insights/"):
            if not isinstance(self.store, TreeInsightStore):
                self._send_json(400, {"error": "tag_not_supported", "detail": "tree mode only"})
                return
            card_id = path[len("/insights/") : -len("/tag")]
            body, err = self._read_json_body()
            if err is not None or body is None:
                self._send_json(400, {"error": "invalid_json", "detail": err})
                return
            tags = body.get("tags") or []
            sticky = bool(body.get("sticky", True))
            result = self.store.tag(card_id, tags, sticky=sticky)
            if result is None:
                self._send_json(404, {"error": "not_found", "id": card_id})
                return
            self._send_json(200, {"id": result.get("id"), "tags": result.get("tags")})
            return

        # POST /topics
        if path == "/topics":
            if not isinstance(self.store, TreeInsightStore):
                self._send_json(400, {"error": "topics_not_supported", "detail": "tree mode only"})
                return
            body, err = self._read_json_body()
            if err is not None or body is None:
                self._send_json(400, {"error": "invalid_json", "detail": err})
                return
            topic = self.store.create_topic(body)
            self._send_json(200, {"id": topic.get("id")})
            return
        # POST /insights/{id}/relabel
        if path.startswith("/insights/") and path.endswith("/relabel"):
            if not isinstance(self.store, TreeInsightStore):
                self._send_json(400, {"error": "relabel_not_supported", "detail": "tree mode only"})
                return
            card_id = path[len("/insights/"):-len("/relabel")]
            body, err = self._read_json_body()
            if err is not None or body is None:
                self._send_json(400, {"error": "invalid_json", "detail": err})
                return
            new_label = body.get("label", "")
            override_by = body.get("override_by", "admin")
            result = self.store.relabel(card_id, new_label, override_by)
            if result is None:
                self._send_json(404, {"error": "not_found", "detail": f"card {card_id!r} not found"})
                return
            effective_label = result.get("label_override") or result.get("label", "good")
            self._send_json(200, {"id": card_id, "effective_label": effective_label})
            return

        self._send_404()

    def do_DELETE(self) -> None:  # noqa: N802
        parsed = urlsplit(self.path)
        path = parsed.path
        if path.startswith("/insights/"):
            if not isinstance(self.store, TreeInsightStore):
                self._send_json(400, {"error": "delete_not_supported", "detail": "tree mode only"})
                return
            card_id = path[len("/insights/") :]
            ok = self.store.delete(card_id)
            if not ok:
                self._send_json(404, {"error": "not_found", "id": card_id})
                return
            self._send_json(200, {"id": card_id, "deleted": True})
            return
        self._send_404()


def _make_handler(store: InsightStore) -> type[InsightHandler]:
    return type("BoundInsightHandler", (InsightHandler,), {"store": store})


def run(
    host: str = "0.0.0.0",
    port: int = 7821,
    store_path: Path = Path("./wiki.json"),
    store_mode: str = "flat",
) -> None:
    if store_mode == "tree":
        store: Any = TreeInsightStore(Path(store_path))
    else:
        store = InsightStore(Path(store_path))
    handler_cls = _make_handler(store)
    httpd = ThreadingHTTPServer((host, port), handler_cls)
    lan_ip = _detect_lan_ip()
    sys.stderr.write(
        f"[insightsd] bound to {host}:{port} mode={store_mode} store={store_path}\n"
    )
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
