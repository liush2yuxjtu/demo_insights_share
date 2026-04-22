"""search_agent.topics payload 优先级排序测试。

对齐 proposal_ceo_next_steps.md 「决策一致性」：多主题输入固定优先级。

用 stub 避免导入 claude_agent_sdk（CI / 无网络环境也能跑）。
"""
from __future__ import annotations

import json
import sys
import types
from pathlib import Path

import pytest


# 在 import search_agent 前 stub SDK：该模块顶级 import claude_agent_sdk
if "claude_agent_sdk" not in sys.modules:
    _sdk = types.ModuleType("claude_agent_sdk")

    class _Stub:
        pass

    _sdk.AssistantMessage = _Stub
    _sdk.ClaudeAgentOptions = _Stub
    _sdk.ResultMessage = _Stub

    async def _stub_query(*_a, **_kw):  # pragma: no cover
        return
        yield  # make it an async gen

    _sdk.query = _stub_query
    sys.modules["claude_agent_sdk"] = _sdk


def _load_real_search_agent():
    """确保拿到的是真实 search_agent 模块，而不是 hooks 测试在 sys.modules
    里塞的 stub（pytest 集合阶段的污染）。"""
    import importlib

    existing = sys.modules.get("search_agent")
    if existing is not None and not hasattr(existing, "_load_topics_payload"):
        # stub 没有这个函数，说明不是真模块 → 清掉后重新 import
        del sys.modules["search_agent"]
    import search_agent as sa

    if not hasattr(sa, "_load_topics_payload"):
        sa = importlib.reload(sa)
    return sa


@pytest.fixture
def wiki_with_priorities(tmp_path: Path) -> Path:
    root = tmp_path / "wt"
    (root / "a").mkdir(parents=True)
    (root / "a" / "INDEX.md").write_text("# a\n", encoding="utf-8")
    (root / "topics.json").write_text(
        json.dumps(
            {
                "topics": [
                    {
                        "id": "low-prio-old",
                        "title": "x",
                        "tags": ["t"],
                        "wiki_type": "a",
                        "priority": 0,
                        "created_at": "2025-01-01T00:00:00Z",
                    },
                    {
                        "id": "high-prio",
                        "title": "y",
                        "tags": ["t"],
                        "wiki_type": "a",
                        "priority": 10,
                        "created_at": "2026-04-20T00:00:00Z",
                    },
                    {
                        "id": "mid-prio-new",
                        "title": "z",
                        "tags": ["t"],
                        "wiki_type": "a",
                        "priority": 5,
                        "created_at": "2026-01-01T00:00:00Z",
                    },
                    {
                        "id": "mid-prio-old",
                        "title": "zz",
                        "tags": ["t"],
                        "wiki_type": "a",
                        "priority": 5,
                        "created_at": "2025-06-01T00:00:00Z",
                    },
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return root


def test_topics_payload_sorted_by_priority_desc(wiki_with_priorities):
    search_agent = _load_real_search_agent()

    payload = search_agent._load_topics_payload(wiki_with_priorities)
    data = json.loads(payload)
    ids = [t["id"] for t in data["topics"]]
    assert ids == [
        "high-prio",       # priority 10
        "mid-prio-old",    # priority 5, older created_at
        "mid-prio-new",    # priority 5, newer created_at
        "low-prio-old",    # priority 0
    ], f"unexpected order: {ids}"


def test_topics_payload_missing_priority_defaults_zero(tmp_path: Path):
    import search_agent

    root = tmp_path / "wt"
    (root / "a").mkdir(parents=True)
    (root / "a" / "INDEX.md").write_text("# a\n", encoding="utf-8")
    (root / "topics.json").write_text(
        json.dumps(
            {"topics": [{"id": "t", "title": "x", "tags": ["y"], "wiki_type": "a"}]},
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    payload = search_agent._load_topics_payload(root)
    data = json.loads(payload)
    assert data["topics"][0]["priority"] == 0


def test_topics_payload_stable_across_calls(wiki_with_priorities):
    """同一 wiki 多次读 → 顺序必须一致（多主题决策一致性）。"""
    import search_agent

    seen = set()
    for _ in range(5):
        payload = search_agent._load_topics_payload(wiki_with_priorities)
        seen.add(payload)
    assert len(seen) == 1, f"ordering drift across calls: {len(seen)} variants"
