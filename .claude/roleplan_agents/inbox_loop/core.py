"""Core helpers for the role-review-inbox self-verify loop.

Pure functions: path layout, schema validation, proposal_id, atomic
write, crash detection, derive_pending. No LLM calls here.
"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
import time
from pathlib import Path
from typing import Any, Iterable

ROLES_DEFAULT = ["pm", "oncall", "tech_lead", "newbie", "curator", "validator"]

MAX_PENDING = 20
DEFER_AFTER_K = 3
ROLE_CONCURRENCY = 2
DEAD_LETTER_SEC = 1800

REQUIRED_FIELDS = ("title", "rationale", "impact", "affected_roles")
INVALID_IMPACT = {"", "minimal", "none", "n/a", "tbd"}
VALID_IMPACT = {"low", "medium", "high"}

TERMINAL_STATUSES = {"approved", "denied"}


def inbox_paths(inbox_dir: Path) -> dict[str, Path]:
    """Layout: single source of truth for every file/dir inside inbox."""
    inbox_dir = Path(inbox_dir)
    return {
        "root": inbox_dir,
        "role_verdicts_dir": inbox_dir / "role_verdicts",
        "autofix_log": inbox_dir / "autofix_log.jsonl",
        "proposals_appended": inbox_dir / "proposals_appended.jsonl",
        "decisions_dir": inbox_dir / "decisions",
        "checkpoints_dir": inbox_dir / "checkpoints",
        "summary_json": inbox_dir / "summary.json",
        "summary_md": inbox_dir / "summary.md",
    }


def ensure_inbox(inbox_dir: Path) -> dict[str, Path]:
    paths = inbox_paths(inbox_dir)
    for key in ("root", "role_verdicts_dir", "decisions_dir", "checkpoints_dir"):
        paths[key].mkdir(parents=True, exist_ok=True)
    return paths


def proposal_id(task: str, title: str, rationale: str) -> str:
    raw = f"{task}|{title}|{rationale}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


def schema_valid(design: dict[str, Any]) -> bool:
    """Structural-only filter for step 3 (no LLM, no semantic judge)."""
    if not isinstance(design, dict):
        return False
    for field in REQUIRED_FIELDS:
        value = design.get(field)
        if not value:
            return False
        if isinstance(value, str) and not value.strip():
            return False
    impact = str(design["impact"]).strip().lower()
    if impact in INVALID_IMPACT or impact not in VALID_IMPACT:
        return False
    if len(str(design["title"]).strip()) < 5:
        return False
    if len(str(design["rationale"]).strip()) < 20:
        return False
    affected = design["affected_roles"]
    if not isinstance(affected, (list, tuple)) or len(affected) == 0:
        return False
    return True


def atomic_write_json(path: Path, obj: Any) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(
        prefix=path.name + ".", suffix=".tmp", dir=str(path.parent)
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fp:
            json.dump(obj, fp, ensure_ascii=False, indent=2)
            fp.flush()
            os.fsync(fp.fileno())
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(record, ensure_ascii=False)
    with open(path, "a", encoding="utf-8") as fp:
        fp.write(line + "\n")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    path = Path(path)
    if not path.exists():
        return []
    out: list[dict[str, Any]] = []
    with open(path, encoding="utf-8") as fp:
        for line in fp:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def load_decision(decisions_dir: Path, pid: str) -> dict[str, Any] | None:
    path = Path(decisions_dir) / f"{pid}.json"
    if not path.exists():
        return None
    try:
        with open(path, encoding="utf-8") as fp:
            return json.load(fp)
    except json.JSONDecodeError:
        return None


def effective_status(decisions_dir: Path, pid: str) -> str:
    decision = load_decision(decisions_dir, pid)
    if decision is None:
        return "pending"
    return decision.get("status", "pending")


def derive_pending(inbox_dir: Path) -> list[dict[str, Any]]:
    """Aggregate appended proposals minus terminal decisions.

    Duplicates by proposal_id are collapsed to the first appearance (earliest
    iter); proposals that reached a terminal status via decisions/{pid}.json
    are excluded; deferred proposals past DEFER_AFTER_K are auto-denied
    and excluded.
    """
    paths = inbox_paths(inbox_dir)
    appended = read_jsonl(paths["proposals_appended"])
    seen: dict[str, dict[str, Any]] = {}
    for rec in appended:
        pid = rec.get("proposal_id")
        if not pid or pid in seen:
            continue
        seen[pid] = rec
    pending: list[dict[str, Any]] = []
    for pid, rec in seen.items():
        decision = load_decision(paths["decisions_dir"], pid)
        if decision is None:
            pending.append(rec)
            continue
        status = decision.get("status")
        if status in TERMINAL_STATUSES:
            continue
        if status == "deferred" and decision.get("defer_count", 0) >= DEFER_AFTER_K:
            continue
        pending.append(rec)
    return pending


def latest_checkpoint(inbox_dir: Path) -> dict[str, Any] | None:
    paths = inbox_paths(inbox_dir)
    ckpt_dir = paths["checkpoints_dir"]
    if not ckpt_dir.exists():
        return None
    candidates = [
        p for p in ckpt_dir.glob("iter_*.json") if not p.name.endswith(".tmp")
    ]
    if not candidates:
        return None

    def parse_iter(p: Path) -> int:
        stem = p.stem
        try:
            return int(stem.split("_")[-1])
        except (ValueError, IndexError):
            return -1

    latest = max(candidates, key=parse_iter)
    try:
        with open(latest, encoding="utf-8") as fp:
            return json.load(fp)
    except (json.JSONDecodeError, OSError):
        return None


def crash_detected(inbox_dir: Path, dead_letter_sec: int = DEAD_LETTER_SEC) -> bool:
    paths = inbox_paths(inbox_dir)
    if paths["summary_json"].exists():
        return False
    ckpt_dir = paths["checkpoints_dir"]
    if not ckpt_dir.exists():
        return False
    candidates = [
        p for p in ckpt_dir.glob("iter_*.json") if not p.name.endswith(".tmp")
    ]
    if not candidates:
        return False
    latest_mtime = max(p.stat().st_mtime for p in candidates)
    return (time.time() - latest_mtime) > dead_letter_sec


def now_ts() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())


def read_text(path: Path) -> str:
    with open(path, encoding="utf-8") as fp:
        return fp.read()


def write_text(path: Path, text: str) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
