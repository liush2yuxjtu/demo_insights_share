"""Smoke test for insights_stop_hook 的 latency 指标 + cache flip。

对齐 proposal_generation_latency.md M6_LATENCY_MVP O5：
- 同步路径（INSIGHTS_STOP_HOOK_ASYNC=0）下跑两次 hook
- 第一次 cache=miss，第二次 cache=hit
- metrics jsonl 必须出现 search_total + end_to_end 两条，cache 字段翻转
"""
from __future__ import annotations

import json
import os
import sys
import types
from pathlib import Path

import pytest

HOOKS_DIR = Path(__file__).resolve().parent
DEMO_CODES = HOOKS_DIR.parent
sys.path.insert(0, str(DEMO_CODES))
sys.path.insert(0, str(HOOKS_DIR))

# search_agent 依赖 claude_agent_sdk（MiniMax SDK）在 CI / unit test 环境下可能没装。
# hook 里 import search_agent 是为了拿到 .run 当 runner；本测试用 monkeypatch 把
# latency_cache.cached_search 替换掉，runner 永远不会真被调用，所以这里塞一个
# 纯占位 stub 到 sys.modules，import 能过就够。
if "search_agent" not in sys.modules:
    _stub = types.ModuleType("search_agent")
    _stub.run = lambda query, wiki_tree_root: {"hits": []}  # 理论上不会被调用
    sys.modules["search_agent"] = _stub


@pytest.fixture
def canned_hits() -> dict:
    return {
        "hits": [
            {
                "wiki_type": "system-design",
                "item": "latency-cache",
                "score": 0.92,
                "rationale": "canned",
            }
        ]
    }


@pytest.fixture
def transcript_file(tmp_path: Path) -> Path:
    """造一个 minimal transcript jsonl，最后一条 user 消息是检索 query。"""
    transcript = tmp_path / "transcript.jsonl"
    lines = [
        {"message": {"role": "user", "content": "latency budget exceeded what do?"}},
    ]
    with transcript.open("w", encoding="utf-8") as fh:
        for obj in lines:
            fh.write(json.dumps(obj, ensure_ascii=False))
            fh.write("\n")
    return transcript


@pytest.fixture
def metrics_dir(tmp_path: Path, monkeypatch) -> Path:
    """把 METRICS_DIR 重定向到 tmp，避免污染用户真正的 ~/.cache。"""
    fake_home = tmp_path / "fakehome"
    fake_home.mkdir(parents=True, exist_ok=True)
    metrics_root = fake_home / ".cache" / "insights-share" / "metrics"

    import insights_stop_hook

    monkeypatch.setattr(insights_stop_hook, "METRICS_DIR", metrics_root)
    # REVIEW_PATH 也重定向到 tmp，避免 /tmp 污染
    monkeypatch.setattr(insights_stop_hook, "REVIEW_PATH", tmp_path / "insights_review.md")
    return metrics_root


def _read_all_metrics(metrics_dir: Path) -> list[dict]:
    records: list[dict] = []
    for p in sorted(metrics_dir.glob("*.jsonl")):
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    return records


def test_stop_hook_sync_cache_miss_then_hit(
    monkeypatch,
    capsys,
    transcript_file: Path,
    metrics_dir: Path,
    canned_hits: dict,
) -> None:
    """同步模式下跑两次，验证：
    1) metrics 文件存在且包含 search_total / end_to_end 两个 stage
    2) 第一次 cache=miss，第二次 cache=hit
    3) hook 返回 0
    """
    # 关掉 async fork，确保 metrics 在当前进程同步写完
    monkeypatch.setenv("INSIGHTS_STOP_HOOK_ASYNC", "0")
    # 强制 trigger_mode = SILENT_AND_JUST_RUN（默认即如此，显式兜底）
    monkeypatch.setenv("INSIGHTS_TRIGGER_MODE", "SILENT_AND_JUST_RUN")

    import insights_stop_hook
    import latency_cache

    # 第一次：miss；第二次：hit
    call_count = {"n": 0}

    def fake_cached_search(query, wiki_tree_root, runner, ttl_seconds=300):
        call_count["n"] += 1
        was_hit = call_count["n"] > 1
        return canned_hits, was_hit

    monkeypatch.setattr(latency_cache, "cached_search", fake_cached_search)

    # 干掉 insights_cache.persist + emit_from_env 的真实 IO，保持 hook 流程闭合
    import insights_cache
    monkeypatch.setattr(insights_cache, "persist", lambda top: Path("/tmp/fake"))

    from insightsd import emitter

    monkeypatch.setattr(emitter, "emit_from_env", lambda **kwargs: None)
    # stop hook 模块局部 import，这里 patch 已经生效（同一 module 对象）

    event_payload = json.dumps({"transcript_path": str(transcript_file)})

    def run_once() -> int:
        # 重置 stdin
        import io

        monkeypatch.setattr(sys, "stdin", io.StringIO(event_payload))
        return insights_stop_hook.main()

    rc1 = run_once()
    rc2 = run_once()

    assert rc1 == 0, "first run should exit 0"
    assert rc2 == 0, "second run should exit 0"

    records = _read_all_metrics(metrics_dir)
    stages = [r["stage"] for r in records]
    # 每次跑应写 3 条：search_total + inject + end_to_end（inject 存在 so bonus）
    # 至少必须满足题目契约：search_total + end_to_end 都在
    assert "search_total" in stages, f"search_total missing; stages={stages}"
    assert "end_to_end" in stages, f"end_to_end missing; stages={stages}"

    # 验证 cache 字段翻转
    search_records = [r for r in records if r["stage"] == "search_total"]
    assert len(search_records) == 2, f"expected 2 search_total rows, got {len(search_records)}"
    assert search_records[0]["cache"] == "miss", f"first run should be miss, got {search_records[0]}"
    assert search_records[1]["cache"] == "hit", f"second run should be hit, got {search_records[1]}"

    # query 截断检查
    for r in records:
        assert len(r.get("query", "")) <= 200

    # status 都应是 ok
    for r in records:
        assert r["status"] == "ok", f"unexpected status in {r}"

    # latency_ms 是非负 int
    for r in records:
        assert isinstance(r["latency_ms"], int)
        assert r["latency_ms"] >= 0
