"""Inner-loop subagent entry point.

Runs inside a detached opus subagent process. Does NOT call the
AskUserQuestion tool. Communicates with the main session purely via files
under inbox_dir.

Usage:
    python subagent.py \
        --task-file /abs/task.txt \
        --artifact-file /abs/artifact.md \
        --inbox-dir /abs/docs/user_complaints_inbox \
        --roles-dir /abs/.claude/roleplan_agents \
        --judge /abs/.claude/roleplan_agents/inbox_loop/judge.sh \
        --iters 5
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import traceback
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from core import (
    DEAD_LETTER_SEC,
    ROLES_DEFAULT,
    ROLE_CONCURRENCY,
    append_jsonl,
    atomic_write_json,
    derive_pending,
    ensure_inbox,
    inbox_paths,
    latest_checkpoint,
    now_ts,
    proposal_id,
    read_jsonl,
    read_text,
    schema_valid,
    write_text,
)

SHIP_MARKERS = ("ship-ready", "ship ready", "ready to ship", "no blockers", "可出货")
FIX_PREFIX = "FIXED:"


def judge_call(judge_script: Path, prompt: str) -> str:
    result = subprocess.run(
        [str(judge_script)],
        input=prompt,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"judge exit={result.returncode} stderr={result.stderr.strip()}"
        )
    return (result.stdout or "").strip()


def build_role_prompt(role_prompt_path: Path, iter_i: int, artifact: str) -> str:
    header = read_text(role_prompt_path)
    return (
        f"{header}\n\n---\n## review iter {iter_i}\n\n"
        f"```markdown\n{artifact}\n```\n\n"
        "Give your role-specific review in free text. "
        "Separate concrete bugs from upgrade proposals."
    )


def ask_roles_parallel(
    roles: list[str],
    roles_dir: Path,
    judge_script: Path,
    iter_i: int,
    artifact: str,
    concurrency: int,
    role_verdicts_dir: Path,
) -> dict[str, str]:
    def one(role: str) -> tuple[str, str]:
        role_file = roles_dir / f"prompt_{role}.md"
        prompt = build_role_prompt(role_file, iter_i, artifact)
        comment = judge_call(judge_script, prompt)
        append_jsonl(
            role_verdicts_dir / f"{role}.jsonl",
            {"iter": iter_i, "role": role, "comment": comment, "ts": now_ts()},
        )
        return role, comment

    with ThreadPoolExecutor(max_workers=max(1, concurrency)) as pool:
        return dict(pool.map(one, roles))


def autofix(
    judge_script: Path,
    task: str,
    artifact: str,
    role_comments: dict[str, str],
) -> tuple[str, bool]:
    combined = "\n".join(
        f"### {role}\n{comment}" for role, comment in role_comments.items()
    )
    prompt = (
        "You are a bug-fix bot. Find only concrete bugs in the artifact below.\n"
        f"TASK:\n{task}\n\n"
        f"ARTIFACT:\n```\n{artifact}\n```\n\n"
        f"ROLE COMMENTS (for context, only the bug parts):\n{combined}\n\n"
        "If concrete bugs (code / logic / schema / contract / typo / path) "
        "exist, output:\n"
        f"{FIX_PREFIX}\n<full rewritten artifact>\n\n"
        "If none, output exactly: NOBUG\n\n"
        "Ignore upgrade proposals; they belong to step 3."
    )
    verdict = judge_call(judge_script, prompt)
    if verdict.startswith(FIX_PREFIX):
        body = verdict[len(FIX_PREFIX):].lstrip("\n")
        return body, True
    return artifact, False


def extract_proposals(
    judge_script: Path,
    role_comments: dict[str, str],
) -> list[dict[str, Any]]:
    combined = "\n".join(
        f"### {role}\n{comment}" for role, comment in role_comments.items()
    )
    prompt = (
        "Extract-only task. No judging, no scoring.\n"
        "From the role comments below, extract each *upgrade proposal* "
        "(distinct from bug reports) into a JSON object with fields: "
        "title (>=5 chars), rationale (>=20 chars), impact "
        "(exactly one of: low, medium, high), affected_roles (array of role names).\n\n"
        "Output a JSON array. Nothing else — no prose, no markdown fences.\n\n"
        f"ROLE COMMENTS:\n{combined}\n"
    )
    raw = judge_call(judge_script, prompt)
    try:
        match = re.search(r"\[[\s\S]*\]", raw)
        if match is None:
            return []
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return []


def ship_verdict(
    judge_script: Path,
    task: str,
    artifact: str,
    role_comments: dict[str, str],
    autofix_applied: bool,
) -> str:
    combined = "\n".join(
        f"### {role}\n{comment}" for role, comment in role_comments.items()
    )
    prompt = (
        f"TASK:\n{task}\n\n"
        f"ARTIFACT (after autofix = {autofix_applied}):\n"
        f"```\n{artifact}\n```\n\n"
        f"ROLE COMMENTS:\n{combined}\n\n"
        "Decide if this artifact is ready to ship. IGNORE any upgrade "
        "proposals — those are user-side decisions filed to the inbox and "
        "do not block shipping. Base the decision on role bug-level feedback "
        "plus whether autofix was applied.\n\n"
        "Reply freely. Use 'ship-ready' or 'ready to ship' or 'no blockers' "
        "if and only if you approve. Otherwise list concrete revisions."
    )
    return judge_call(judge_script, prompt)


def verdict_says_ship(verdict: str) -> bool:
    lowered = verdict.lower()
    return any(marker in lowered for marker in SHIP_MARKERS)


def run_inner_loop(args: argparse.Namespace) -> int:
    task = read_text(Path(args.task_file)).strip()
    artifact = read_text(Path(args.artifact_file))
    roles: list[str] = args.roles.split(",") if args.roles else list(ROLES_DEFAULT)
    paths = ensure_inbox(Path(args.inbox_dir))
    judge_script = Path(args.judge)
    roles_dir = Path(args.roles_dir)

    prior_ship_verdict: str | None = None
    start_iter = 1
    ck = latest_checkpoint(paths["root"])
    if ck is not None and args.resume:
        artifact = ck.get("artifact_next", artifact)
        prior_ship_verdict = ck.get("ship_verdict_prev")
        start_iter = int(ck.get("iter", 0)) + 1

    verdict_tag = "maxed"
    previously_shipped = False
    current_iter = start_iter
    final_ship_verdict: str | None = prior_ship_verdict

    try:
        for current_iter in range(start_iter, args.iters + 1):
            role_comments = ask_roles_parallel(
                roles=roles,
                roles_dir=roles_dir,
                judge_script=judge_script,
                iter_i=current_iter,
                artifact=artifact,
                concurrency=args.concurrency,
                role_verdicts_dir=paths["role_verdicts_dir"],
            )
            artifact_next, fixed = autofix(
                judge_script=judge_script,
                task=task,
                artifact=artifact,
                role_comments=role_comments,
            )
            if fixed:
                append_jsonl(
                    paths["autofix_log"],
                    {
                        "iter": current_iter,
                        "before_sha": proposal_id(task, "before", artifact)[:8],
                        "after_sha": proposal_id(task, "after", artifact_next)[:8],
                        "ts": now_ts(),
                    },
                )

            raw_proposals = extract_proposals(judge_script, role_comments)
            kept = 0
            for design in raw_proposals:
                if not schema_valid(design):
                    continue
                pid = proposal_id(task, design["title"], design["rationale"])
                append_jsonl(
                    paths["proposals_appended"],
                    {
                        "proposal_id": pid,
                        "iter": current_iter,
                        "design": design,
                        "source_roles": design.get("affected_roles", []),
                        "ts_appended": now_ts(),
                    },
                )
                kept += 1

            verdict = ship_verdict(
                judge_script=judge_script,
                task=task,
                artifact=artifact_next,
                role_comments=role_comments,
                autofix_applied=fixed,
            )
            final_ship_verdict = verdict

            atomic_write_json(
                paths["checkpoints_dir"] / f"iter_{current_iter}.json",
                {
                    "iter": current_iter,
                    "artifact_next": artifact_next,
                    "ship_verdict_prev": verdict,
                    "autofix_applied": fixed,
                    "proposals_kept": kept,
                    "ts": now_ts(),
                },
            )

            shipped_now = verdict_says_ship(verdict)
            if shipped_now:
                verdict_tag = "shipped"
                artifact = artifact_next
                previously_shipped = True
                break
            if (
                prior_ship_verdict is not None
                and verdict.strip() == prior_ship_verdict.strip()
            ):
                verdict_tag = "converged" if previously_shipped else "stuck"
                artifact = artifact_next
                break
            prior_ship_verdict = verdict
            previously_shipped = shipped_now
            artifact = artifact_next
    except Exception:
        # Crash path: don't write summary.json; main session's crash_detected()
        # notices missing summary.json + stale checkpoint mtime.
        sys.stderr.write(traceback.format_exc())
        return 2

    pending = derive_pending(paths["root"])
    autofix_count = len(read_jsonl(paths["autofix_log"]))
    final_artifact_path = paths["root"] / "final_artifact.md"
    write_text(final_artifact_path, artifact)

    summary = {
        "verdict_tag": verdict_tag,
        "iters_used": current_iter,
        "artifact_final_path": str(final_artifact_path),
        "pending_hint": len(pending),
        "autofix_count": autofix_count,
        "roles": roles,
        "ship_verdict_final": final_ship_verdict,
        "exit_reason": "normal",
        "ts": now_ts(),
    }
    atomic_write_json(paths["summary_json"], summary)

    md_lines = [
        f"# inbox_loop run summary",
        "",
        f"- verdict_tag: **{summary['verdict_tag']}**",
        f"- iters_used: {summary['iters_used']}",
        f"- final_artifact: {summary['artifact_final_path']}",
        f"- pending proposals (from user_complaints_inbox): {summary['pending_hint']}",
        f"- autofix count: {summary['autofix_count']}",
        f"- exit_reason: {summary['exit_reason']}",
        f"- ts: {summary['ts']}",
        "",
        "## final ship verdict (free text from judge)",
        "",
        "```text",
        (final_ship_verdict or "(none)"),
        "```",
    ]
    write_text(paths["summary_md"], "\n".join(md_lines))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="role-review-inbox inner loop")
    parser.add_argument("--task-file", required=True)
    parser.add_argument("--artifact-file", required=True)
    parser.add_argument("--inbox-dir", required=True)
    parser.add_argument("--roles-dir", required=True)
    parser.add_argument("--judge", required=True)
    parser.add_argument("--iters", type=int, default=5)
    parser.add_argument("--concurrency", type=int, default=ROLE_CONCURRENCY)
    parser.add_argument(
        "--roles",
        default="",
        help="comma-separated; default = pm,oncall,tech_lead,newbie,curator,validator",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="resume from latest checkpoint if present",
    )
    args = parser.parse_args()
    return run_inner_loop(args)


if __name__ == "__main__":
    raise SystemExit(main())
