"""环境变量驱动的事件发射器。"""

from __future__ import annotations

import argparse
import json
import os
import urllib.request
from typing import Any


def emit_http_event(url: str, token: str, payload: dict[str, Any], timeout: float = 2.0) -> None:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "X-Insights-Token": token,
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout):
        return


def emit_from_env(
    *,
    stage: str,
    status: str,
    source: str,
    message: str,
    payload: dict[str, Any] | None = None,
    metrics: dict[str, Any] | None = None,
    artifact_refs: list[dict[str, Any]] | None = None,
) -> bool:
    url = os.environ.get("INSIGHTS_EVENTS_URL", "").strip()
    token = os.environ.get("INSIGHTS_INTERNAL_TOKEN", "").strip()
    session_id = os.environ.get("INSIGHTS_SESSION_ID", "").strip()
    if not url or not token or not session_id:
        return False
    try:
        emit_http_event(
            url,
            token,
            {
                "session_id": session_id,
                "stage": stage,
                "status": status,
                "source": source,
                "message": message,
                "payload": payload or {},
                "metrics": metrics or {},
                "artifact_refs": artifact_refs or [],
            },
        )
    except Exception:
        return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="向本地 insightsd 发送一条过程事件")
    parser.add_argument("--stage", required=True)
    parser.add_argument("--status", required=True)
    parser.add_argument("--source", default="shell")
    parser.add_argument("--message", required=True)
    args = parser.parse_args()
    ok = emit_from_env(
        stage=args.stage,
        status=args.status,
        source=args.source,
        message=args.message,
    )
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
