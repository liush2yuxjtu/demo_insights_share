"""Main-session inbox drain.

Read-only from the main session's perspective. Emits a JSON object with up
to MAX_PENDING pending proposals so the main session can feed them into
AskUserQuestion. Does NOT itself call AskUserQuestion (that tool is
Claude-Code-specific; this script runs via Bash from the main session).

Usage:
    python main_drain.py --inbox-dir /abs/path [--max 20] [--batch 4]

Exit codes:
    0 — printed JSON (could be empty pending list)
    1 — inbox_dir missing
    2 — crash detected (prints diagnostic JSON with pending + "crash": true)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from core import (
    MAX_PENDING,
    crash_detected,
    derive_pending,
    inbox_paths,
    latest_checkpoint,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="inbox drain (read-only)")
    parser.add_argument("--inbox-dir", required=True)
    parser.add_argument("--max", type=int, default=MAX_PENDING)
    parser.add_argument(
        "--batch", type=int, default=4, help="top-K returned for AskUserQuestion"
    )
    args = parser.parse_args()

    inbox_dir = Path(args.inbox_dir)
    if not inbox_dir.exists():
        sys.stderr.write(f"[drain] inbox_dir not found: {inbox_dir}\n")
        return 1

    paths = inbox_paths(inbox_dir)
    pending = derive_pending(inbox_dir)
    capped = pending[-args.max :] if len(pending) > args.max else pending
    batch = capped[: args.batch]
    crash = crash_detected(inbox_dir)
    ck = latest_checkpoint(inbox_dir)

    output = {
        "inbox_dir": str(inbox_dir),
        "total_pending": len(pending),
        "cap": args.max,
        "batch_size": args.batch,
        "batch": batch,
        "crash_detected": crash,
        "summary_json_exists": paths["summary_json"].exists(),
        "latest_checkpoint_iter": ck.get("iter") if ck else None,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
