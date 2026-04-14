#!/usr/bin/env python3
"""从 Claude Code 会话 jsonl 中按关键词提取线性时间线事件。

输入：jsonl glob（默认 ~/.claude/projects/-Users-m1-projects-demo-insights-share/*.jsonl）
关键词：用于过滤 message 内容中包含的字符串（如 "proposal.md"、"validation"）。
输出：按 timestamp 升序的 list[{ts, actor, summary, file}]，每条 summary 截断到 200 字。

设计要点：
- 跳过没有 timestamp 的行（permission-mode / file-history-snapshot 等元数据行）。
- JSONDecodeError 仅 warning 跳过，不 crash。
- summary 为去除 XML 标签后的纯文本前缀，避免泄漏完整 prompt 原文。
- 不依赖任何第三方库。
"""
from __future__ import annotations

import argparse
import glob as globmod
import json
import re
import sys
from pathlib import Path

DEFAULT_GLOB = str(
    Path.home() / ".claude/projects/-Users-m1-projects-demo-insights-share/*.jsonl"
)
SUMMARY_LIMIT = 200
TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")


def _stringify_tool_input(value) -> str:
    """把 tool_use.input 压成可搜索的扁平字符串（保留 file_path 等字段名）。"""
    if value is None:
        return ""
    if isinstance(value, (str, int, float, bool)):
        return str(value)
    if isinstance(value, list):
        return " ".join(_stringify_tool_input(v) for v in value)
    if isinstance(value, dict):
        return " ".join(f"{k}={_stringify_tool_input(v)}" for k, v in value.items())
    return str(value)


def flatten_content(content) -> str:
    """把 message.content 统一压成纯字符串（含 tool_use input / tool_result text）。"""
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict):
                itype = item.get("type")
                if "text" in item and isinstance(item["text"], str):
                    parts.append(item["text"])
                elif itype == "tool_use":
                    name = item.get("name", "tool")
                    inp = _stringify_tool_input(item.get("input"))
                    parts.append(f"[tool_use:{name}] {inp}")
                elif itype == "tool_result":
                    inner = item.get("content")
                    if isinstance(inner, str):
                        parts.append(f"[tool_result] {inner}")
                    elif isinstance(inner, list):
                        sub: list[str] = []
                        for sub_item in inner:
                            if isinstance(sub_item, dict) and isinstance(
                                sub_item.get("text"), str
                            ):
                                sub.append(sub_item["text"])
                        parts.append("[tool_result] " + " ".join(sub))
                    else:
                        parts.append("[tool_result]")
            elif isinstance(item, str):
                parts.append(item)
        return " ".join(parts)
    return str(content)


def sanitize(text: str) -> str:
    """脱敏：去掉 XML/HTML 标签 + 折叠空白 + 截断到 SUMMARY_LIMIT。"""
    no_tag = TAG_RE.sub(" ", text)
    flat = WS_RE.sub(" ", no_tag).strip()
    if len(flat) > SUMMARY_LIMIT:
        return flat[:SUMMARY_LIMIT] + "…"
    return flat


def extract_events(jsonl_files: list[Path], keywords: list[str]) -> list[dict]:
    events: list[dict] = []
    kws = [k.lower() for k in keywords]
    for fp in jsonl_files:
        try:
            fh = fp.open("r", encoding="utf-8")
        except OSError as e:
            print(f"[warn] 打开失败 {fp}: {e}", file=sys.stderr)
            continue
        with fh:
            for line_no, raw in enumerate(fh, start=1):
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    obj = json.loads(raw)
                except json.JSONDecodeError as e:
                    print(
                        f"[warn] {fp.name}:{line_no} JSONDecodeError 跳过: {e}",
                        file=sys.stderr,
                    )
                    continue
                ts = obj.get("timestamp")
                if not ts:
                    continue
                msg = obj.get("message")
                if isinstance(msg, dict):
                    role = msg.get("role") or obj.get("type", "?")
                    body = flatten_content(msg.get("content"))
                else:
                    role = obj.get("type", "?")
                    body = obj.get("content", "")
                    if not isinstance(body, str):
                        body = str(body)
                hay = body.lower()
                if not any(k in hay for k in kws):
                    continue
                events.append(
                    {
                        "ts": ts,
                        "actor": role,
                        "summary": sanitize(body),
                        "file": fp.name,
                    }
                )
    events.sort(key=lambda e: e["ts"])
    return events


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--glob", default=DEFAULT_GLOB, help="jsonl 文件 glob 模式")
    p.add_argument(
        "--keyword",
        action="append",
        default=None,
        help="过滤关键词，可多次指定；不指定时默认 proposal.md + validation",
    )
    p.add_argument("--out", default="-", help="输出 JSON 路径，- 表示 stdout")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    keywords = args.keyword or ["proposal.md", "validation"]
    files = sorted(Path(p) for p in globmod.glob(args.glob))
    if not files:
        print(f"[warn] 未匹配到任何 jsonl: {args.glob}", file=sys.stderr)
    events = extract_events(files, keywords)
    payload = {
        "glob": args.glob,
        "keywords": keywords,
        "files": [f.name for f in files],
        "count": len(events),
        "events": events,
    }
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.out == "-":
        print(text)
    else:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"[ok] 已写入 {args.out}（{len(events)} 条事件）", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
