#!/usr/bin/env python3
"""从 ~/.claude/projects/**/*.jsonl 抽 user→assistant 教训配对，输出 wiki card。

按 upload_plan.md 规则。
"""
from __future__ import annotations
import json
import os
import re
import sys
import uuid
import hashlib
import argparse
from pathlib import Path
from datetime import datetime

BUG_PATTERN = re.compile(
    r"bug|error|fix|fail|crash|stuck|报错|不工作|为什么|崩|挂|hang|broken|怎么办",
    re.IGNORECASE,
)
LOCATION_PATTERN = re.compile(r"\.(py|sh|ts|js|md|json|yaml|toml|rs|go):\d+|\$\{?\w+|/\w+/[\w\-./]+")
MIN_ASSISTANT_CHARS = 50


def text_of(message: dict) -> str:
    """提取 message.content 的纯文本。"""
    content = message.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for blk in content:
            if not isinstance(blk, dict):
                continue
            if blk.get("type") == "text":
                parts.append(blk.get("text", ""))
        return "\n".join(parts)
    return ""


def slugify(s: str, n: int = 40) -> str:
    s = re.sub(r"[^\w\u4e00-\u9fff]+", "_", s.strip())[:n]
    return s.strip("_") or "lesson"


def derive_topic(user_text: str) -> str:
    """简易 topic 推断 (匹配 wiki_tree 现有目录)。"""
    t = user_text.lower()
    rules = [
        ("infra_cache", r"redis|cache|lru|memcached"),
        ("infra_queue", r"celery|queue|kafka|rabbitmq|retry storm"),
        ("database", r"postgres|pgpool|mysql|sql|connection pool|db|database"),
        ("docs_rules", r"claude\.md|agents\.md|rule|doc"),
        ("tooling", r"tmux|git|gh\b|hook|skill|cli"),
        ("agent_workflow", r"agent|subagent|judge|probe|self.?verify"),
        ("shell_env", r"shell|env|zshrc|path|alias|bash"),
    ]
    for topic, pat in rules:
        if re.search(pat, t):
            return topic
    return "general"


def fingerprint(scenario: str, rationale: str) -> str:
    return hashlib.sha256((scenario + "|" + rationale[:200]).encode("utf-8")).hexdigest()[:16]


def scan_jsonl(path: Path):
    """yield (user_msg_text, assistant_msg_text, sessionId, line_no, ts)."""
    last_user = None
    last_user_line = 0
    last_user_ts = ""
    with path.open() as f:
        for i, line in enumerate(f, 1):
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            t = d.get("type")
            if t == "user":
                last_user = text_of(d.get("message", {}))
                last_user_line = i
                last_user_ts = d.get("timestamp", "")
            elif t == "assistant" and last_user:
                txt = text_of(d.get("message", {}))
                if txt:
                    yield (
                        last_user,
                        txt,
                        d.get("sessionId", ""),
                        last_user_line,
                        last_user_ts,
                    )
                last_user = None


def is_lesson(user_txt: str, assistant_txt: str) -> bool:
    if len(assistant_txt) < MIN_ASSISTANT_CHARS:
        return False
    if not BUG_PATTERN.search(user_txt + assistant_txt):
        return False
    if not LOCATION_PATTERN.search(assistant_txt):
        return False
    return True


def build_card(
    user_txt: str,
    assistant_txt: str,
    session_id: str,
    src_path: Path,
    line_no: int,
    ts: str,
) -> dict:
    scenario = user_txt.strip().splitlines()[0][:160]
    rationale = assistant_txt.strip()[:600]
    topic = derive_topic(user_txt + " " + assistant_txt)
    date = (ts or datetime.utcnow().isoformat())[:10]
    fp = fingerprint(scenario, rationale)
    return {
        "id": str(uuid.uuid5(uuid.NAMESPACE_URL, f"{src_path}:{line_no}:{fp}")),
        "topic": topic,
        "author": f"claude_session_{session_id[:8]}",
        "scenario": scenario,
        "decision": "good",
        "rationale": rationale,
        "evidence_jsonl": f"{src_path}:{line_no}",
        "date": date,
        "labels": ["auto-extracted", f"src:{src_path.stem[:8]}"],
        "fingerprint": fp,
    }


def existing_fingerprints(staging: Path) -> set[str]:
    fps = set()
    for p in staging.rglob("*.json"):
        try:
            d = json.loads(p.read_text())
            if "fingerprint" in d:
                fps.add(d["fingerprint"])
        except Exception:
            continue
    return fps


def write_card(staging: Path, card: dict) -> Path:
    topic_dir = staging / card["topic"]
    topic_dir.mkdir(parents=True, exist_ok=True)
    slug = slugify(card["scenario"])
    fname = f"{card['author']}_{slug}_{card['date']}.json"
    out = topic_dir / fname
    out.write_text(json.dumps(card, ensure_ascii=False, indent=2))
    md = topic_dir / fname.replace(".json", ".md")
    md.write_text(
        f"# {card['scenario']}\n\n"
        f"- topic: {card['topic']}\n"
        f"- author: {card['author']}\n"
        f"- date: {card['date']}\n"
        f"- decision: {card['decision']}\n"
        f"- evidence: `{card['evidence_jsonl']}`\n\n"
        f"## rationale\n\n{card['rationale']}\n"
    )
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, help="单个 jsonl 文件 或 目录")
    ap.add_argument("--out", default="/tmp/insights_upload_staging")
    ap.add_argument("--limit", type=int, default=0, help=">0 则只输出 N 张")
    args = ap.parse_args()

    src = Path(args.src)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    files = [src] if src.is_file() else list(src.rglob("*.jsonl"))
    seen = existing_fingerprints(out)
    written = 0
    scanned = 0
    for fp in files:
        for u, a, sid, ln, ts in scan_jsonl(fp):
            scanned += 1
            if not is_lesson(u, a):
                continue
            card = build_card(u, a, sid, fp, ln, ts)
            if card["fingerprint"] in seen:
                continue
            seen.add(card["fingerprint"])
            path = write_card(out, card)
            written += 1
            print(f"WROTE {path}")
            if args.limit and written >= args.limit:
                print(f"DONE scanned={scanned} written={written}")
                return 0
    print(f"DONE scanned={scanned} written={written}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
