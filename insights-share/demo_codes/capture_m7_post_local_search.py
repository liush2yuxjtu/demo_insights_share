"""M7 post-local-search 基线采样脚本。

对齐 proposal_generation_latency.md §验证：跑 5 个典型 query，每 query
分别模拟 cache-miss（清 cache）与 cache-hit（第二次跑同 query），把
end_to_end + search_total + adapter + inject 四条 stage metrics 写到
~/.cache/insights-share/metrics/<YYYY-MM-DD>.jsonl，对应 latency_gate.py
schema，直接喂给 gate 校验。

不要误用真实 insights_stop_hook.main（它依赖 transcript_path）；这里
直接 import 内部 _do_search_and_inject，用一个最小 transcript stub 模拟。

用法::

    ./.venv/bin/python capture_m7_post_local_search.py --out-metrics <path>
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import shutil
import tempfile
from pathlib import Path

DEMO_CODES = Path(__file__).resolve().parent
sys.path.insert(0, str(DEMO_CODES))
sys.path.insert(0, str(DEMO_CODES / "hooks"))


QUERIES = [
    "postgres connection pool timeout",
    "懒惰信号检测",
    "tmux nested 环境变量",
    "worktree 分离开发",
    "删除前审计流程",
]


def _clear_cache() -> None:
    """清 latency_cache 让下次 search 走 miss 路径。"""
    for d in (
        Path("~/.cache/insights-share/hits").expanduser(),
    ):
        if d.exists():
            shutil.rmtree(d, ignore_errors=True)


def _clear_daily_metrics() -> Path:
    """把今天的 metrics 文件挪到 tmp 备份，返回备份路径（可 diff 用）。"""
    from datetime import datetime, timezone

    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    p = Path(f"~/.cache/insights-share/metrics/{date_str}.jsonl").expanduser()
    if p.exists():
        bak = Path(tempfile.mkdtemp(prefix="metrics_bak_")) / p.name
        shutil.copy2(p, bak)
        p.unlink()
        sys.stderr.write(f"[capture] backed up {p} → {bak}\n")
        return bak
    return Path("")


def _make_transcript(tmpdir: Path, query: str) -> Path:
    """生成 minimal jsonl transcript，最后一条 user 消息 = query。"""
    f = tmpdir / "transcript.jsonl"
    f.write_text(
        json.dumps({"message": {"role": "user", "content": query}}, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return f


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-metrics", type=Path, help="拷贝一份 metrics 到指定路径")
    args = ap.parse_args()

    # 强制同步路径（INSIGHTS_STOP_HOOK_ASYNC=0）才能让子进程在 parent 内跑完
    os.environ["INSIGHTS_STOP_HOOK_ASYNC"] = "0"
    # 关静默 metrics 走默认路径
    os.environ.pop("INSIGHTS_EVENTS_SILENT", None)
    # 打开 local_search 短路
    os.environ.setdefault("INSIGHTS_LOCAL_SEARCH", "1")

    import insights_stop_hook as hook

    _clear_daily_metrics()
    _clear_cache()

    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        # cache-miss 5 次：只在最开始清一次；5 个不同 query 天然 miss，
        # cache 会在第 1 次 store 完成后累积，让 hit round 能真正命中
        _clear_cache()
        sys.stderr.write("\n---- cache-miss round ----\n")
        import io
        for q in QUERIES:
            transcript = _make_transcript(tdp, q)
            sys.stderr.write(f"[capture] miss query={q!r}\n")
            event_json = json.dumps({"transcript_path": str(transcript)})
            sys.stdin = io.StringIO(event_json)
            rc = hook.main()
            sys.stderr.write(f"[capture] hook rc={rc}\n")

        # cache-hit 5 次：所有 query 此时都已缓存
        sys.stderr.write("\n---- cache-hit round ----\n")
        for q in QUERIES:
            transcript = _make_transcript(tdp, q)
            event_json = json.dumps({"transcript_path": str(transcript)})
            sys.stdin = io.StringIO(event_json)
            rc = hook.main()
            sys.stderr.write(f"[capture] hit rc={rc}\n")

    # 拷贝 metrics
    from datetime import datetime, timezone

    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    metrics_path = Path(f"~/.cache/insights-share/metrics/{date_str}.jsonl").expanduser()
    if args.out_metrics and metrics_path.exists():
        args.out_metrics.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(metrics_path, args.out_metrics)
        sys.stderr.write(f"[capture] metrics → {args.out_metrics}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
