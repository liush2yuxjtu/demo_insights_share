#!/usr/bin/env python3
"""
Claude 会话 jsonl → 易读 txt 导出工具

定位 ~/.claude/projects/-Users-m1-projects-demo-insights-share/*.jsonl，
默认按 mtime 取最新一个；可通过 --session-id <uuid> 指定具体文件。
仅提取 message.role in (user, assistant) 的事件，输出 [HH:MM:SS] role: text。
去 ANSI 转义、行宽 ≤ 120。
"""
import argparse
import json
import os
import re
import sys
import textwrap
from pathlib import Path

PROJECT_DIR = Path.home() / ".claude" / "projects" / "-Users-m1-projects-demo-insights-share"
ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
WRAP_WIDTH = 120


def strip_ansi(text: str) -> str:
    return ANSI_RE.sub("", text)


def find_latest_jsonl() -> Path | None:
    files = sorted(PROJECT_DIR.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None


def find_by_session_id(session_id: str) -> Path | None:
    candidate = PROJECT_DIR / f"{session_id}.jsonl"
    return candidate if candidate.exists() else None


def extract_text(content) -> str:
    """将 message.content 抽成纯文本。"""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if not isinstance(block, dict):
                continue
            btype = block.get("type")
            if btype == "text":
                parts.append(block.get("text", ""))
            elif btype == "thinking":
                continue
            elif btype == "tool_use":
                name = block.get("name", "?")
                parts.append(f"[tool_use: {name}]")
            elif btype == "tool_result":
                tr = block.get("content", "")
                if isinstance(tr, list):
                    tr = " ".join(
                        b.get("text", "") for b in tr if isinstance(b, dict) and b.get("type") == "text"
                    )
                parts.append(f"[tool_result] {tr}")
        return "\n".join(p for p in parts if p)
    return str(content)


def format_timestamp(ts: str) -> str:
    if not ts or len(ts) < 19:
        return "??:??:??"
    return ts[11:19]


def export(jsonl_path: Path) -> str:
    lines = []
    seen_assistant_ids = set()
    with jsonl_path.open() as f:
        for raw in f:
            try:
                d = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if d.get("type") not in ("user", "assistant"):
                continue
            msg = d.get("message", {})
            if not isinstance(msg, dict):
                continue
            role = msg.get("role")
            if role not in ("user", "assistant"):
                continue
            # 同一 assistant message id 可能被切成多块事件，只取一次
            if role == "assistant":
                mid = msg.get("id")
                if mid and mid in seen_assistant_ids:
                    continue
                if mid:
                    seen_assistant_ids.add(mid)
            text = extract_text(msg.get("content", ""))
            text = strip_ansi(text).strip()
            if not text:
                continue
            ts = format_timestamp(d.get("timestamp", ""))
            header = f"[{ts}] {role}: "
            indent = " " * len(header)
            wrapped = []
            for para in text.splitlines() or [""]:
                if not para:
                    wrapped.append("")
                    continue
                wrapped.extend(
                    textwrap.wrap(
                        para,
                        width=WRAP_WIDTH,
                        initial_indent=header if not wrapped else indent,
                        subsequent_indent=indent,
                        break_long_words=False,
                        break_on_hyphens=False,
                    )
                    or [header + para]
                )
                # 后续段落的 header 占位换成 indent
                header = indent
            lines.append("\n".join(wrapped))
    return "\n\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Claude 会话 jsonl → 易读 txt 导出")
    parser.add_argument("--session-id", help="指定 session uuid（不带 .jsonl）", default=None)
    parser.add_argument("--output", "-o", help="输出 txt 路径，缺省为 stdout", default=None)
    args = parser.parse_args()

    if args.session_id:
        jsonl = find_by_session_id(args.session_id)
        if not jsonl:
            print(f"[error] 未找到 session: {args.session_id}", file=sys.stderr)
            return 2
    else:
        jsonl = find_latest_jsonl()
        if not jsonl:
            print(f"[error] 目录无 jsonl: {PROJECT_DIR}", file=sys.stderr)
            return 2

    print(f"[info] 导出: {jsonl}", file=sys.stderr)
    text = export(jsonl)
    if args.output:
        Path(args.output).write_text(text)
        print(f"[info] 已写入: {args.output} ({len(text)} 字节)", file=sys.stderr)
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
