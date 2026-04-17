"""Stdlib ThreadingHTTPServer daemon for insight-card sharing."""

from __future__ import annotations

import json
import mimetypes
import queue
import socket
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit

from .runtime import RuntimeStore
from .runners import RunnerManager
from .store import InsightStore, TreeInsightStore
from .terminal import TerminalBridge


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
    runtime: RuntimeStore
    app_root: Path
    runner: RunnerManager
    terminal: TerminalBridge

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

    def _send_file(self, path: Path) -> None:
        body = path.read_bytes()
        content_type, _ = mimetypes.guess_type(str(path))
        self.send_response(200)
        self.send_header("Content-Type", content_type or "application/octet-stream")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _serve_page(self, filename: str) -> None:
        path = Path(__file__).resolve().parent / filename
        if not path.is_file():
            self._send_404()
            return
        self._send_file(path)

    def _safe_artifact(self, rel_path: str) -> Path | None:
        candidate = (self.app_root / rel_path).resolve()
        root = self.app_root.resolve()
        try:
            candidate.relative_to(root)
        except ValueError:
            return None
        if any(part.startswith(".") for part in candidate.relative_to(root).parts):
            return None
        if not candidate.is_file():
            return None
        return candidate

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
        if path in ("/", "/dashboard"):
            self._serve_page("dashboard.html")
            return
        if path == "/handout":
            self._serve_page("handout.html")
            return
        if path == "/pm-script":
            self._serve_page("pm_script.html")
            return
        if path == "/preview":
            self._serve_page("preview.html")
            return
        if path == "/ops":
            self._serve_page("ops.html")
            return
        if path == "/cli":
            self._serve_page("cli.html")
            return
        if path.startswith("/static/"):
            static_path = (Path(__file__).resolve().parent / path.removeprefix("/static/")).resolve()
            static_root = Path(__file__).resolve().parent.resolve()
            try:
                static_path.relative_to(static_root)
            except ValueError:
                self._send_404()
                return
            if not static_path.is_file():
                self._send_404()
                return
            self._send_file(static_path)
            return
        if path.startswith("/artifacts/"):
            artifact = self._safe_artifact(path.removeprefix("/artifacts/"))
            if artifact is None:
                self._send_404()
                return
            self._send_file(artifact)
            return
        if path == "/healthz":
            self._send_json(200, {"ok": True})
            return
        if path == "/api/system/summary":
            self._send_json(200, self.runtime.system_summary())
            return
        if path == "/api/cli/tmux/summary":
            allow_input = self.client_address[0] in {"127.0.0.1", "::1"}
            self._send_json(200, self.terminal.tmux_summary(input_enabled=allow_input))
            return
        if path == "/api/cli/tmux":
            params = parse_qs(parsed.query)
            target = (params.get("target") or [""])[0].strip()
            if not target:
                self._send_json(400, {"error": "missing_target"})
                return
            try:
                lines = int((params.get("lines") or ["240"])[0])
            except ValueError:
                lines = 240
            try:
                payload = self.terminal.capture_tmux(target, lines=lines)
            except ValueError as exc:
                self._send_json(404, {"error": "tmux_capture_failed", "detail": str(exc)})
                return
            self._send_json(200, payload)
            return
        if path == "/api/sessions":
            params = parse_qs(parsed.query)
            payload = {
                "sessions": self.runtime.list_sessions(
                    kind=(params.get("kind") or [None])[0],
                    status=(params.get("status") or [None])[0],
                    q=(params.get("q") or [None])[0],
                    limit=int((params.get("limit") or ["20"])[0]),
                )
            }
            self._send_json(200, payload)
            return
        if path.startswith("/api/sessions/") and path.endswith("/events"):
            session_id = path[len("/api/sessions/") : -len("/events")].strip("/")
            session = self.runtime.get_session(session_id)
            if session is None:
                self._send_json(404, {"error": "not_found", "id": session_id})
                return
            params = parse_qs(parsed.query)
            limit_raw = (params.get("limit") or [None])[0]
            limit = int(limit_raw) if limit_raw else None
            self._send_json(
                200,
                {
                    "session": session,
                    "events": self.runtime.get_events(session_id, limit=limit),
                },
            )
            return
        if path.startswith("/api/sessions/"):
            session_id = path[len("/api/sessions/") :].strip("/")
            session = self.runtime.get_session(session_id)
            if session is None:
                self._send_json(404, {"error": "not_found", "id": session_id})
                return
            self._send_json(200, {"session": session})
            return
        if path == "/api/stream":
            snapshot = self.runtime.system_summary()
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Connection", "keep-alive")
            self.end_headers()
            self.wfile.write(
                (
                    "event: hello\n"
                    f"data: {json.dumps(snapshot, ensure_ascii=False)}\n\n"
                ).encode("utf-8")
            )
            self.wfile.flush()
            subscriber = self.runtime.subscribe()
            try:
                while True:
                    try:
                        item = subscriber.get(timeout=1.0)
                    except queue.Empty:
                        self.wfile.write(b": ping\n\n")
                        self.wfile.flush()
                        continue
                    self.wfile.write(
                        (
                            f"event: {item.get('type', 'message')}\n"
                            f"data: {json.dumps(item, ensure_ascii=False)}\n\n"
                        ).encode("utf-8")
                    )
                    self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError):
                return
            finally:
                self.runtime.unsubscribe(subscriber)
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

        if path == "/_events":
            if self.client_address[0] not in {"127.0.0.1", "::1"}:
                self._send_json(403, {"error": "forbidden", "detail": "loopback only"})
                return
            if self.headers.get("X-Insights-Token", "") != self.runtime.internal_token:
                self._send_json(403, {"error": "forbidden", "detail": "bad token"})
                return
            body, err = self._read_json_body()
            if err is not None or body is None:
                self._send_json(400, {"error": "invalid_json", "detail": err})
                return
            try:
                event = self.runtime.append_event(
                    str(body.get("session_id", "")),
                    stage=str(body.get("stage", "")),
                    status=str(body.get("status", "")),
                    source=str(body.get("source", "internal")),
                    message=str(body.get("message", "")),
                    payload=body.get("payload") or {},
                    metrics=body.get("metrics") or {},
                    artifact_refs=body.get("artifact_refs") or [],
                )
            except KeyError as exc:
                self._send_json(404, {"error": "not_found", "detail": str(exc)})
                return
            self._send_json(202, {"accepted": True, "event_id": event["id"]})
            return

        if path == "/api/runs/demo":
            if not self.runtime.runner_enabled:
                self._send_json(403, {"error": "runner_disabled"})
                return
            body, err = self._read_json_body()
            if err is not None or body is None:
                self._send_json(400, {"error": "invalid_json", "detail": err})
                return
            session_id = self.runner.start_demo(
                problem=str(body.get("problem", "")).strip() or None,
                local_context=str(body.get("local_context", "")).strip() or None,
                use_ai=bool(body.get("use_ai", False)),
            )
            self._send_json(202, {"session_id": session_id})
            return

        if path == "/api/runs/validation":
            if not self.runtime.runner_enabled:
                self._send_json(403, {"error": "runner_disabled"})
                return
            session_id = self.runner.start_validation()
            self._send_json(202, {"session_id": session_id})
            return
        if path == "/api/cli/tmux/input":
            if self.client_address[0] not in {"127.0.0.1", "::1"}:
                self._send_json(403, {"error": "forbidden", "detail": "loopback only"})
                return
            body, err = self._read_json_body()
            if err is not None or body is None:
                self._send_json(400, {"error": "invalid_json", "detail": err})
                return
            target = str(body.get("target", "")).strip()
            if not target:
                self._send_json(400, {"error": "missing_target"})
                return
            try:
                self.terminal.send_tmux_input(
                    target,
                    text=str(body.get("text", "")),
                    enter=bool(body.get("enter", True)),
                    control=str(body.get("control", "")).strip() or None,
                )
            except ValueError as exc:
                self._send_json(400, {"error": "tmux_input_failed", "detail": str(exc)})
                return
            self._send_json(202, {"accepted": True, "target": target})
            return

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


def _make_handler(
    store: InsightStore | TreeInsightStore,
    *,
    runtime: RuntimeStore | None = None,
    app_root: Path | None = None,
    terminal: TerminalBridge | None = None,
) -> type[InsightHandler]:
    resolved_root = app_root or Path(__file__).resolve().parents[2]
    resolved_runtime = runtime or RuntimeStore(resolved_root / "demo_codes" / "runtime")
    runner = RunnerManager(store=store, runtime=resolved_runtime, app_root=resolved_root)
    resolved_terminal = terminal or TerminalBridge(resolved_root)
    return type(
        "BoundInsightHandler",
        (InsightHandler,),
        {
            "store": store,
            "runtime": resolved_runtime,
            "app_root": resolved_root,
            "runner": runner,
            "terminal": resolved_terminal,
        },
    )


def run(
    host: str = "0.0.0.0",
    port: int = 7821,
    store_path: Path = Path("./wiki.json"),
    store_mode: str = "flat",
    runtime_dir: Path | None = None,
    enable_runners: bool = False,
) -> None:
    if store_mode == "tree":
        store: Any = TreeInsightStore(Path(store_path))
    else:
        store = InsightStore(Path(store_path))
    root = Path(__file__).resolve().parents[2]
    runtime = RuntimeStore(
        runtime_dir or (Path(store_path).resolve().parent / "runtime"),
        runner_enabled=enable_runners,
    )
    handler_cls = _make_handler(store, runtime=runtime, app_root=root)
    httpd = ThreadingHTTPServer((host, port), handler_cls)
    lan_ip = _detect_lan_ip()
    sys.stderr.write(
        f"[insightsd] bound to {host}:{port} mode={store_mode} store={store_path}\n"
    )
    sys.stderr.write(f"[insightsd] LAN IP detected: {lan_ip}\n")
    sys.stderr.write(
        f"[insightsd] teammates can publish/consume at http://{lan_ip}:{port}\n"
    )
    sys.stderr.write(
        f"[insightsd] web=http://{lan_ip}:{port}/ dashboard=http://{lan_ip}:{port}/dashboard preview=http://{lan_ip}:{port}/preview ops=http://{lan_ip}:{port}/ops cli=http://{lan_ip}:{port}/cli runners={runtime.runner_enabled}\n"
    )
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        sys.stderr.write("[insightsd] shutting down\n")
    finally:
        httpd.server_close()
