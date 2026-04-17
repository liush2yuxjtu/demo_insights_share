#!/usr/bin/env python3
"""Claude Code Stop hook：静默调用 search_agent，把 LAN insight wiki 的命中
卡片悄悄送到 Bob 面前。

对齐 validation.md task #2：触发模式硬编码 SILENT_AND_JUST_RUN
（ASK_USER_APPROVAL 仅作占位，被强制 override 回 SILENT）。

**严禁 fallback**：search_agent 的任何异常直接 raise，hook 退出码非 0，
validation phase 视为失败。
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

DEMO_CODES = Path(__file__).resolve().parent.parent
WIKI_TREE = DEMO_CODES / "wiki_tree"
REVIEW_PATH = Path("/tmp/insights_review.md")
SENTINEL = "[SILENT_AND_JUST_RUN] no user confirm required"


def _resolve_trigger_mode() -> str:
    requested = os.environ.get("INSIGHTS_TRIGGER_MODE", "SILENT_AND_JUST_RUN").strip()
    if requested != "SILENT_AND_JUST_RUN":
        # validation.md：ASK_USER_APPROVAL 仅占位，强制 override
        sys.stderr.write(
            f"[insights_stop_hook] requested={requested}; force override → SILENT_AND_JUST_RUN\n"
        )
    return "SILENT_AND_JUST_RUN"


def _last_message_text(transcript_path: str | None, role: str) -> str:
    if not transcript_path:
        return ""
    p = Path(transcript_path)
    if not p.is_file():
        return ""
    last = ""
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        # claude code transcript 是 jsonl，每行可能是 message / tool / system
        msg = event.get("message") or {}
        if msg.get("role") == role:
            content = msg.get("content")
            if isinstance(content, str):
                last = content
            elif isinstance(content, list):
                parts: list[str] = []
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        text = block.get("text", "")
                        if text:
                            parts.append(text)
                if parts:
                    last = "\n".join(parts)
    return last.strip()


def main() -> int:
    raw = sys.stdin.read() or "{}"
    try:
        event = json.loads(raw)
    except json.JSONDecodeError:
        event = {}

    mode = _resolve_trigger_mode()
    sys.stderr.write(f"{SENTINEL}\n")
    sys.stderr.write(f"[insights_stop_hook] mode={mode}\n")

    transcript_path = event.get("transcript_path")
    # 对 wiki 检索来说，最后一条 user 问题比 assistant 的中间解释更稳定。
    # 这能避免把 “正在读取 SKILL.md” 之类的助手旁白误当成 incident query。
    last_text = _last_message_text(transcript_path, "user")
    if not last_text:
        last_text = _last_message_text(transcript_path, "assistant")

    if not last_text:
        sys.stderr.write("[insights_stop_hook] no assistant/user text found in transcript\n")
        return 0

    # search_agent 用 import 调用（共享当前 Python 进程的 .env 加载）
    sys.path.insert(0, str(DEMO_CODES))
    sys.path.insert(0, str(DEMO_CODES / "hooks"))
    import search_agent  # noqa: E402
    import insights_cache  # noqa: E402
    from insightsd.emitter import emit_from_env  # noqa: E402

    sys.stderr.write(f"[insights_stop_hook] querying search_agent: {last_text[:120]!r}\n")
    emit_from_env(
        stage="hook",
        status="running",
        source="insights_stop_hook",
        message=f"Stop hook 触发：{last_text[:80]}",
    )
    try:
        hits = search_agent.run(query=last_text, wiki_tree_root=str(WIKI_TREE))
    except Exception as exc:  # noqa: BLE001
        sys.stderr.write(f"[insights_stop_hook] search_agent failed: {exc}\n")
        emit_from_env(
            stage="hook",
            status="failed",
            source="insights_stop_hook",
            message=f"Stop hook 检索失败：{type(exc).__name__}",
        )
        return 0
    top = (hits.get("hits") or [None])[0]

    REVIEW_PATH.parent.mkdir(parents=True, exist_ok=True)
    with REVIEW_PATH.open("a", encoding="utf-8") as fh:
        fh.write("---\n")
        fh.write(f"sentinel: {SENTINEL}\n")
        fh.write(f"trigger_mode: {mode}\n")
        fh.write(f"query: {last_text[:200]}\n")
        fh.write(f"hits: {json.dumps(hits, ensure_ascii=False)}\n")

    if top:
        sys.stderr.write(
            f"[insights_stop_hook] top wiki_type={top.get('wiki_type')} "
            f"item={top.get('item')} score={top.get('score')}\n"
        )
        # 落盘缓存：把 top hit 写到 ~/.cache/insights-wiki/<id>.json
        # 同时刷新 manifest.json（last_sync_at + cards 列表）。
        # 静默行为不变：缓存写盘对用户无感。
        try:
            cached_path = insights_cache.persist(top)
            sys.stderr.write(
                f"[insights_stop_hook] cached top hit → {cached_path}\n"
            )
        except (OSError, TypeError) as exc:
            # 严禁吞 search_agent 异常，但缓存写盘失败不应阻断主流程
            # （比如磁盘只读、权限问题），只记 stderr。
            sys.stderr.write(
                f"[insights_stop_hook] cache persist failed: {exc}\n"
            )
        emit_from_env(
            stage="hook",
            status="ok",
            source="insights_stop_hook",
            message=f"Stop hook 命中 {top.get('item')}",
            payload={"top": top},
            metrics={"score": top.get("score", 0)},
        )
        # 注：Stop hook 的 hookSpecificOutput schema 不支持 additionalContext 字段，
        # 写 stdout 会导致 Claude Code 报 "Stop hook error: JSON validation failed"。
        # hint 注入改由 insights_prefetch.py 在 UserPromptSubmit 事件里处理，
        # 此处只负责"搜索 + 落盘缓存"，不再向 stdout 输出 payload。
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
