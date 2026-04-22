#!/usr/bin/env python3
"""Claude Code Stop hook：静默调用 search_agent，把 LAN insight wiki 的命中
卡片悄悄送到 Bob 面前。

对齐 validation.md task #2：触发模式硬编码 SILENT_AND_JUST_RUN
（ASK_USER_APPROVAL 仅作占位，被强制 override 回 SILENT）。

对齐 proposal_generation_latency.md M6_LATENCY_MVP (O1 + O3 + O5)：
- O1 结果级 cache：走 latency_cache.cached_search，命中直接跳 search_agent
- O3 early exit：底层 search_agent._run_async 在 SEARCH_HITS 围栏关上时 break
- O5 async fire-and-forget：默认 fork 后 parent 立刻退出，child 后台跑 search +
  inject + metrics，下一轮对话不再被 hook 阻塞
- latency 指标：每个 stage 一行 jsonl 写到
  ~/.cache/insights-share/metrics/<YYYY-MM-DD>.jsonl

**严禁 fallback**：search_agent / cache / inject 任何异常直接 raise，
child 以非 0 退出；validation phase 视为失败。parent 不 retry。
"""
from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

DEMO_CODES = Path(__file__).resolve().parent.parent
WIKI_TREE = DEMO_CODES / "wiki_tree"
REVIEW_PATH = Path("/tmp/insights_review.md")
SENTINEL = "[SILENT_AND_JUST_RUN] no user confirm required"

METRICS_DIR = Path("~/.cache/insights-share/metrics").expanduser()


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


def _utc_now_z() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _metrics_path() -> Path:
    # 按天切，avoid 单文件无限增长（proposal 风险表）
    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return METRICS_DIR / f"{date_str}.jsonl"


def _append_metric(
    stage: str,
    status: str,
    latency_ms: int,
    cache: str,
    query: str,
) -> None:
    """单行 jsonl append 到当日 metrics 文件。

    schema: {"stage","status","latency_ms","cache","ts","query"}
    query 截到 200 字符，防止长 prompt 把文件撑爆。
    """
    record = {
        "stage": stage,
        "status": status,
        "latency_ms": int(latency_ms),
        "cache": cache,
        "ts": _utc_now_z(),
        "query": (query or "")[:200],
    }
    path = _metrics_path()
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")))
        fh.write("\n")


def _do_search_and_inject(last_text: str, mode: str) -> int:
    """child / 同步路径共享的主体：search → inject → metrics。

    严禁吞 search_agent 异常。任何异常 raise 冒出去，由 caller 决定 exit code。
    """
    end_to_end_start = time.perf_counter()

    # search_agent 用 import 调用（共享当前 Python 进程的 .env 加载）
    sys.path.insert(0, str(DEMO_CODES))
    sys.path.insert(0, str(DEMO_CODES / "hooks"))
    import search_agent  # noqa: E402
    import latency_cache  # noqa: E402
    import insights_cache  # noqa: E402
    from insightsd.emitter import emit_from_env  # noqa: E402

    sys.stderr.write(f"[insights_stop_hook] querying search_agent: {last_text[:120]!r}\n")
    emit_from_env(
        stage="hook",
        status="running",
        source="insights_stop_hook",
        message=f"Stop hook 触发：{last_text[:80]}",
    )

    # ---- stage: search_total (含 cache-lookup + miss 情况下的真实 search) ----
    search_start = time.perf_counter()
    was_cache_hit = False
    search_status = "ok"
    try:
        hits, was_cache_hit = latency_cache.cached_search(
            last_text,
            WIKI_TREE,
            runner=search_agent.run,
            ttl_seconds=300,
        )
    except Exception:
        search_status = "fail"
        _append_metric(
            "search_total",
            search_status,
            int((time.perf_counter() - search_start) * 1000),
            "miss",
            last_text,
        )
        _append_metric(
            "end_to_end",
            "fail",
            int((time.perf_counter() - end_to_end_start) * 1000),
            "miss",
            last_text,
        )
        raise
    search_latency_ms = int((time.perf_counter() - search_start) * 1000)
    _append_metric(
        "search_total",
        search_status,
        search_latency_ms,
        "hit" if was_cache_hit else "miss",
        last_text,
    )

    top = (hits.get("hits") or [None])[0]

    # ---- stage: inject (落 /tmp 审阅文件 + insights_cache 持久化 top hit) ----
    inject_start = time.perf_counter()
    inject_status = "ok"
    try:
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
            # 落盘缓存：把 top hit 写到 ~/.cache/insights-share/<id>.json
            # 同时刷新 manifest.json（last_sync_at + cards 列表）。
            # 静默行为不变：缓存写盘对用户无感。
            try:
                cached_path = insights_cache.persist(top)
                sys.stderr.write(
                    f"[insights_stop_hook] cached top hit → {cached_path}\n"
                )
            except (OSError, TypeError) as exc:
                # 缓存写盘失败不应阻断主流程（比如磁盘只读、权限问题），只记 stderr。
                # 这不是 search 异常，符合 proposal "严禁 fallback" 的边界
                # （fallback 指检索结果，不指缓存磁盘错误）。
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
    except Exception:
        inject_status = "fail"
        _append_metric(
            "inject",
            inject_status,
            int((time.perf_counter() - inject_start) * 1000),
            "hit" if was_cache_hit else "miss",
            last_text,
        )
        _append_metric(
            "end_to_end",
            "fail",
            int((time.perf_counter() - end_to_end_start) * 1000),
            "hit" if was_cache_hit else "miss",
            last_text,
        )
        raise

    inject_latency_ms = int((time.perf_counter() - inject_start) * 1000)
    _append_metric(
        "inject",
        inject_status,
        inject_latency_ms,
        "hit" if was_cache_hit else "miss",
        last_text,
    )

    # ---- stage: end_to_end ----
    end_to_end_ms = int((time.perf_counter() - end_to_end_start) * 1000)
    _append_metric(
        "end_to_end",
        "ok",
        end_to_end_ms,
        "hit" if was_cache_hit else "miss",
        last_text,
    )
    return 0


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
    # 这能避免把 "正在读取 SKILL.md" 之类的助手旁白误当成 incident query。
    last_text = _last_message_text(transcript_path, "user")
    if not last_text:
        last_text = _last_message_text(transcript_path, "assistant")

    if not last_text:
        sys.stderr.write("[insights_stop_hook] no assistant/user text found in transcript\n")
        return 0

    # O5: async fire-and-forget 路径（默认 "1"）
    # parent 立刻打 SILENT sentinel + exit 0；child 跑真活。
    # INSIGHTS_STOP_HOOK_ASYNC=0 时走同步路径（测试 / debug 用）。
    async_mode = os.environ.get("INSIGHTS_STOP_HOOK_ASYNC", "1").strip() == "1"

    if async_mode:
        pid = os.fork()
        if pid > 0:
            # parent：已在上面 stderr 写了 SENTINEL，这里直接 return 0
            # 让 Claude Code 视 hook 为 finished，下一轮不被阻塞
            sys.stderr.write(
                f"[insights_stop_hook] async fork: parent exit, child pid={pid}\n"
            )
            return 0
        # child：脱离 controlling tty
        try:
            os.setsid()
        except OSError as exc:
            # setsid 失败不影响后续工作，只记日志
            sys.stderr.write(f"[insights_stop_hook] setsid failed: {exc}\n")
        # child 跑搜索 + inject + metrics；异常冒出由 SystemExit 兜住
        rc = _do_search_and_inject(last_text, mode)
        # child 独立 exit，不返回 parent 的 caller
        os._exit(rc)

    # 同步路径
    return _do_search_and_inject(last_text, mode)


if __name__ == "__main__":
    raise SystemExit(main())
