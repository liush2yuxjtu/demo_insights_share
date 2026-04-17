"""运行时 session / event 存储。"""

from __future__ import annotations

import json
import queue
import secrets
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


_DEMO_STAGES = ["bootstrap", "publish", "search", "adapt", "result", "summary"]
_VALIDATION_STAGES = [
    "phase0",
    "phase1",
    "phase2",
    "phase3",
    "phase4",
    "phase5",
    "summary",
]
_FINAL_STATUSES = {"completed", "failed", "error"}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _as_dict(value: dict[str, Any] | None) -> dict[str, Any]:
    return dict(value or {})


def _as_artifacts(value: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for item in value or []:
        if not isinstance(item, dict):
            continue
        href = str(item.get("href", "")).strip()
        label = str(item.get("label", href or "artifact")).strip()
        if not href:
            continue
        out.append({"label": label, "href": href})
    return out


def _merge_artifacts(current: list[dict[str, Any]], new: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged = list(current)
    seen = {item.get("href") for item in merged}
    for item in new:
        href = item.get("href")
        if href in seen:
            continue
        merged.append(item)
        seen.add(href)
    return merged


def _progress(kind: str, stage: str) -> float:
    if kind == "validation":
        order = _VALIDATION_STAGES
    else:
        order = _DEMO_STAGES
    if stage not in order:
        return 0.0
    return round((order.index(stage) + 1) / len(order), 4)


class RuntimeStore:
    def __init__(
        self,
        root: Path,
        *,
        runner_enabled: bool = False,
        internal_token: str | None = None,
    ) -> None:
        self.root = Path(root)
        self.sessions_dir = self.root / "sessions"
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self.runner_enabled = runner_enabled
        self.internal_token = internal_token or secrets.token_hex(16)
        self._lock = threading.Lock()
        self._sessions: dict[str, dict[str, Any]] = {}
        self._events: dict[str, list[dict[str, Any]]] = {}
        self._subscribers: list[queue.Queue[dict[str, Any]]] = []
        self._load()

    def _session_path(self, session_id: str) -> Path:
        return self.sessions_dir / f"{session_id}.json"

    def _events_path(self, session_id: str) -> Path:
        return self.sessions_dir / f"{session_id}.events.jsonl"

    def _load(self) -> None:
        for session_file in sorted(self.sessions_dir.glob("*.json")):
            if session_file.name.endswith(".events.json"):
                continue
            session = json.loads(session_file.read_text(encoding="utf-8"))
            session_id = str(session.get("id", "")).strip()
            if not session_id:
                continue
            self._sessions[session_id] = session
            event_file = self._events_path(session_id)
            events: list[dict[str, Any]] = []
            if event_file.is_file():
                for line in event_file.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    events.append(json.loads(line))
            self._events[session_id] = events

    def _write_session(self, session: dict[str, Any]) -> None:
        self._session_path(session["id"]).write_text(
            json.dumps(session, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _append_event_file(self, session_id: str, event: dict[str, Any]) -> None:
        with self._events_path(session_id).open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(event, ensure_ascii=False) + "\n")

    def subscribe(self) -> queue.Queue[dict[str, Any]]:
        q: queue.Queue[dict[str, Any]] = queue.Queue()
        with self._lock:
            self._subscribers.append(q)
        return q

    def unsubscribe(self, q: queue.Queue[dict[str, Any]]) -> None:
        with self._lock:
            self._subscribers = [item for item in self._subscribers if item is not q]

    def _publish(self, payload: dict[str, Any]) -> None:
        stale: list[queue.Queue[dict[str, Any]]] = []
        for q in list(self._subscribers):
            try:
                q.put_nowait(payload)
            except Exception:
                stale.append(q)
        if stale:
            self._subscribers = [item for item in self._subscribers if item not in stale]

    def start_session(
        self,
        *,
        kind: str,
        title: str,
        artifact_refs: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        session_id = uuid.uuid4().hex
        session = {
            "id": session_id,
            "kind": kind,
            "title": title,
            "status": "running",
            "started_at": _utc_now(),
            "ended_at": None,
            "current_stage": "pending",
            "progress": 0.0,
            "headline_metrics": {},
            "latest_message": "等待事件",
            "artifact_refs": _as_artifacts(artifact_refs),
        }
        with self._lock:
            self._sessions[session_id] = session
            self._events[session_id] = []
            self._write_session(session)
        self._publish({"type": "session.update", "session": dict(session), "event": None})
        return dict(session)

    def append_event(
        self,
        session_id: str,
        *,
        stage: str,
        status: str,
        source: str,
        message: str,
        payload: dict[str, Any] | None = None,
        metrics: dict[str, Any] | None = None,
        artifact_refs: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                raise KeyError(f"unknown session: {session_id}")
            event = {
                "id": uuid.uuid4().hex,
                "session_id": session_id,
                "kind": session["kind"],
                "stage": stage,
                "status": status,
                "ts": _utc_now(),
                "source": source,
                "message": message,
                "payload": _as_dict(payload),
                "metrics": _as_dict(metrics),
                "artifact_refs": _as_artifacts(artifact_refs),
            }
            events = self._events.setdefault(session_id, [])
            events.append(event)
            self._append_event_file(session_id, event)

            session["current_stage"] = stage
            session["progress"] = _progress(session["kind"], stage)
            session["latest_message"] = message
            session["headline_metrics"] = {
                **session.get("headline_metrics", {}),
                **event["metrics"],
            }
            session["artifact_refs"] = _merge_artifacts(
                list(session.get("artifact_refs") or []),
                event["artifact_refs"],
            )

            if status in {"running", "pending"}:
                session["status"] = "running"
                session["ended_at"] = None
            elif status in {"ok", "completed"}:
                if stage == "summary":
                    session["status"] = "completed"
                    session["ended_at"] = event["ts"]
            elif status in {"failed", "error"}:
                session["status"] = "failed"
                session["ended_at"] = event["ts"]

            self._write_session(session)
            payload_data = {
                "type": "session.update",
                "session": dict(session),
                "event": dict(event),
            }
        self._publish(payload_data)
        return dict(event)

    def list_sessions(
        self,
        *,
        kind: str | None = None,
        status: str | None = None,
        q: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        with self._lock:
            sessions = [dict(item) for item in self._sessions.values()]
        if kind:
            sessions = [item for item in sessions if item.get("kind") == kind]
        if status:
            sessions = [item for item in sessions if item.get("status") == status]
        if q:
            needle = q.lower()
            sessions = [
                item
                for item in sessions
                if needle in str(item.get("title", "")).lower()
                or needle in str(item.get("latest_message", "")).lower()
            ]
        sessions.sort(key=lambda item: str(item.get("started_at", "")), reverse=True)
        return sessions[: max(1, int(limit))]

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        with self._lock:
            session = self._sessions.get(session_id)
            return dict(session) if session else None

    def get_events(self, session_id: str, *, limit: int | None = None) -> list[dict[str, Any]]:
        with self._lock:
            events = [dict(item) for item in self._events.get(session_id, [])]
        if limit is None:
            return events
        return events[-max(1, int(limit)) :]

    def system_summary(self) -> dict[str, Any]:
        sessions = self.list_sessions(limit=200)
        by_kind: dict[str, int] = {}
        by_status: dict[str, int] = {}
        live_session = next((item for item in sessions if item.get("status") == "running"), None)
        for session in sessions:
            kind = str(session.get("kind", "unknown"))
            by_kind[kind] = by_kind.get(kind, 0) + 1
            status = str(session.get("status", "unknown"))
            by_status[status] = by_status.get(status, 0) + 1
        return {
            "generated_at": _utc_now(),
            "runner_enabled": self.runner_enabled,
            "counts": {
                "total": len(sessions),
                "by_kind": by_kind,
                "by_status": by_status,
            },
            "live_session": live_session,
            "recent_sessions": sessions[:8],
        }
