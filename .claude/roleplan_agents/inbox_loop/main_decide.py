"""Main-session decision writer.

Called by the main session after it runs AskUserQuestion on a proposal.
Writes decisions/{pid}.json atomically. Enforces terminal semantics:
once approved/denied is written, subsequent calls are a no-op (no
regression).

Usage:
    python main_decide.py \
        --inbox-dir /abs/path \
        --proposal-id <pid> \
        --answer {Approve|Deny|Defer}
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from core import (
    DEFER_AFTER_K,
    TERMINAL_STATUSES,
    atomic_write_json,
    inbox_paths,
    load_decision,
    now_ts,
)


def apply_answer(
    prev: dict | None,
    answer: str,
) -> dict:
    answer = answer.strip().capitalize()
    if answer not in {"Approve", "Deny", "Defer"}:
        raise ValueError(f"answer must be Approve|Deny|Defer, got {answer!r}")
    history = list(prev.get("history", [])) if prev else []
    prev_status = (prev or {}).get("status")
    if prev_status in TERMINAL_STATUSES:
        # Terminal is terminal — no regression. Caller should have filtered
        # upstream, but we defend here too.
        return prev  # type: ignore[return-value]

    defer_count_prev = (prev or {}).get("defer_count", 0)
    if answer == "Defer":
        new_defer = defer_count_prev + 1
        status = "denied" if new_defer >= DEFER_AFTER_K else "deferred"
    elif answer == "Approve":
        new_defer = defer_count_prev
        status = "approved"
    else:  # Deny
        new_defer = defer_count_prev
        status = "denied"

    history.append({"answer": answer, "ts": now_ts()})
    return {
        "proposal_id": (prev or {}).get("proposal_id"),
        "status": status,
        "defer_count": new_defer,
        "ts_resolved": now_ts(),
        "history": history,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="write main-session decision")
    parser.add_argument("--inbox-dir", required=True)
    parser.add_argument("--proposal-id", required=True)
    parser.add_argument("--answer", required=True, choices=["Approve", "Deny", "Defer"])
    args = parser.parse_args()

    paths = inbox_paths(Path(args.inbox_dir))
    decisions_dir = paths["decisions_dir"]
    decisions_dir.mkdir(parents=True, exist_ok=True)

    prev = load_decision(decisions_dir, args.proposal_id)
    if prev and prev.get("status") in TERMINAL_STATUSES:
        sys.stderr.write(
            f"[decide] {args.proposal_id} already terminal "
            f"({prev['status']}); no-op\n"
        )
        return 0

    try:
        new = apply_answer(prev, args.answer)
    except ValueError as exc:
        sys.stderr.write(f"[decide] {exc}\n")
        return 2

    new["proposal_id"] = args.proposal_id  # ensure set when prev was None
    atomic_write_json(decisions_dir / f"{args.proposal_id}.json", new)
    sys.stderr.write(
        f"[decide] {args.proposal_id} → {new['status']} "
        f"(defer_count={new['defer_count']})\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
