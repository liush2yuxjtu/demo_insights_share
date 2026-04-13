"""insights-share CLI 主入口。

子命令：serve / publish / list / solve / demo。
HTTP 仅用 urllib.request，不依赖 requests。
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

import adapter
import ui

DEFAULT_WIKI = "http://127.0.0.1:7821"
DEFAULT_LOCAL_CONTEXT = (
    "FastAPI + PostgreSQL 14 + PgBouncer transaction pooling, "
    "lunch-time traffic burst"
)
DEFAULT_PROBLEM = (
    "Our checkout API is timing out, postgres is rejecting new connections "
    "during the lunch spike"
)


def _http_get(url: str, timeout: float = 5.0) -> dict[str, Any]:
    with urllib.request.urlopen(url, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _http_post_json(url: str, payload: dict[str, Any], timeout: float = 5.0) -> dict[str, Any]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def cmd_serve(args: argparse.Namespace) -> int:
    from insightsd.server import run

    run(host=args.host, port=args.port, store_path=Path(args.store))
    return 0


def cmd_publish(args: argparse.Namespace) -> int:
    path = Path(args.file)
    if not path.exists():
        print(ui.color(f"file not found: {path}", "red"), file=sys.stderr)
        return 2
    card = json.loads(path.read_text(encoding="utf-8"))
    url = f"{args.wiki.rstrip('/')}/insights"
    try:
        resp = _http_post_json(url, card)
    except urllib.error.URLError as exc:
        print(ui.color(f"publish failed: {exc}", "red"), file=sys.stderr)
        return 1
    cid = resp.get("id") or card.get("id", "?")
    print(ui.color(f"published {cid}", "green"))
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    url = f"{args.wiki.rstrip('/')}/insights"
    try:
        resp = _http_get(url)
    except urllib.error.URLError as exc:
        print(ui.color(f"list failed: {exc}", "red"), file=sys.stderr)
        return 1
    cards = resp.get("cards") or []
    if not cards:
        print(ui.color("(no insights yet)", "dim"))
        return 0
    header = f"{'id':<28}  {'title':<40}  {'author':<12}  tags"
    print(ui.color(header, "bold"))
    print("-" * len(header))
    for c in cards:
        cid = str(c.get("id", ""))[:28]
        title = str(c.get("title", ""))[:40]
        author = str(c.get("author", ""))[:12]
        tags = ",".join(c.get("tags") or [])
        print(f"{cid:<28}  {title:<40}  {author:<12}  {tags}")
    return 0


def _print_hits_empty(problem: str) -> None:
    print(ui.color(f"no insight found for: {problem}", "red"))


def cmd_solve(args: argparse.Namespace) -> int:
    problem: str = args.problem
    wiki = args.wiki.rstrip("/")
    print(ui.banner("DEMO: Bob hits prod incident"))
    print()
    print(ui.color(f"restate: {problem}", "dim"))
    print()

    q = urllib.parse.urlencode({"q": problem, "k": 3})
    search_url = f"{wiki}/search?{q}"

    with ui.timer() as t:
        try:
            resp = _http_get(search_url)
        except urllib.error.URLError as exc:
            print(ui.color(f"search failed: {exc}", "red"), file=sys.stderr)
            return 1
        hits = resp.get("hits") or []

    if not hits:
        _print_hits_empty(problem)
        return 1

    card = hits[0]
    cid = card.get("id", "?")
    author = card.get("author", "?")
    score = card.get("score", 0.0)
    print(ui.color(f"hot-loaded {cid} from {author} (score={score})", "cyan"))
    print()

    if args.no_ai:
        confidence = card.get("confidence", 0)
        body = card.get("fix", "") or ""
        print(ui.panel(body, f"raw (no-ai) confidence={confidence}", "yellow"))
        print()
        print(
            f"fast path: {t.elapsed:.1f}s (no-ai)   "
            f"slow path baseline: ~62s"
        )
        return 0

    with ui.spinner("validating against your context..."):
        result = asyncio.run(adapter.adapt(card, problem, args.local_context))

    subtitle = (
        f"verdict={result.verdict} "
        f"confidence={result.confidence:.2f} "
        f"diff={result.diff_summary}"
    )
    print(ui.panel(result.adapted_insight, subtitle, "green"))
    print()
    print(
        f"fast path: {t.elapsed:.1f}s (adapter: {result.latency_s:.1f}s)   "
        f"slow path baseline: ~62s"
    )
    return 0


def cmd_demo(args: argparse.Namespace) -> int:  # noqa: ARG001
    script = Path(__file__).parent / "run_demo.sh"
    if script.exists():
        print(ui.color(f"please run: bash {script}", "cyan"))
    else:
        print(ui.color("run_demo.sh not found; start serve/publish/solve manually", "yellow"))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="insights_cli", description="insights-share demo CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p_serve = sub.add_parser("serve", help="run the insightsd HTTP daemon")
    p_serve.add_argument("--host", default="0.0.0.0")
    p_serve.add_argument("--port", type=int, default=7821)
    p_serve.add_argument("--store", default="./wiki.json")
    p_serve.set_defaults(func=cmd_serve)

    p_pub = sub.add_parser("publish", help="POST a JSON card file to /insights")
    p_pub.add_argument("file")
    p_pub.add_argument("--wiki", default=DEFAULT_WIKI)
    p_pub.set_defaults(func=cmd_publish)

    p_list = sub.add_parser("list", help="GET /insights and print a table")
    p_list.add_argument("--wiki", default=DEFAULT_WIKI)
    p_list.set_defaults(func=cmd_list)

    p_solve = sub.add_parser("solve", help="search + adapt for a problem")
    p_solve.add_argument("problem", nargs="?", default=DEFAULT_PROBLEM)
    p_solve.add_argument("--wiki", default=DEFAULT_WIKI)
    p_solve.add_argument("--no-ai", action="store_true", help="skip the AI adapter step")
    p_solve.add_argument("--local-context", default=DEFAULT_LOCAL_CONTEXT)
    p_solve.set_defaults(func=cmd_solve)

    p_demo = sub.add_parser("demo", help="print how to run the end-to-end demo")
    p_demo.set_defaults(func=cmd_demo)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
