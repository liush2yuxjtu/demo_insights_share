"""MiniMax agentic search over the 4-layer wiki_tree.

让 haiku-agent 自己用 Glob/Grep/Read 为主、必要时用只读 Bash 探索 wiki_tree，
最终返回排序好的 hits。
对齐 validation.md task #5 的 "MUST have agentic search wiki minimax"。

**严禁 fallback**：任何 SDK / 网络 / 解析异常直接 raise；validation 阶段
任何回退都视为 failure（由 user 显式约束）。

CLI 用法::

    python search_agent.py --query "..." --wiki-tree /abs/path/to/wiki_tree

输出格式（最后一行包含一个 JSON 对象，被 `<<<SEARCH_HITS>>>` 与
`<<<END>>>` 围栏标记，便于 Stop hook 解析）::

    <<<SEARCH_HITS>>>
    {"hits": [{"wiki_type": "...", "item": "...", "score": 0.87, "rationale": "..."}]}
    <<<END>>>
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
import time
from pathlib import Path

from _sdk_common import env_summary, get_haiku_model
from insightsd.emitter import emit_from_env

import local_search

from claude_agent_sdk import (  # noqa: E402
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    query,
)


# 12 KB 上限：超过则逐条裁剪，保证 prompt 可控
_TOPICS_PAYLOAD_MAX_BYTES = 12 * 1024


def _sort_topics_by_priority(items: list) -> list:
    """按 priority desc → created_at asc 稳定排序。

    对齐 proposal_ceo_next_steps.md 「决策一致性」：同一 multi-topic 命中集合
    多次检索必须给出同一顺序。priority 字段可选，缺省为 0。
    """
    def _key(t):
        if not isinstance(t, dict):
            return (0, "")
        prio = int(t.get("priority") or 0)
        ts = t.get("created_at") or ""
        # priority 越大越靠前 → 用负号
        return (-prio, ts)
    return sorted(items, key=_key)


def _load_topics_payload(wiki_tree: Path) -> str:
    """读取 topics.json 并打成紧凑 JSON，供 PROMPT 注入。

    仅保留 id/title/tags/wiki_type/team/priority 字段；丢弃 created_by/created_at 以压缩体积。
    输出紧凑 JSON（无 indent），超过 12 KB 时截取前 N 条保证不超限。
    文件缺失时返回 "{}"（tree 模式下 topics.json 可选，不得 raise）。
    排序对齐多主题优先级规则：priority desc → created_at asc。"""
    topics_path = wiki_tree / "topics.json"
    if not topics_path.exists():
        return "{}"

    raw = json.loads(topics_path.read_text(encoding="utf-8"))
    items = raw.get("topics", []) if isinstance(raw, dict) else []
    items = _sort_topics_by_priority(items)

    keep_fields = ("id", "title", "tags", "wiki_type", "team")
    slim: list[dict] = []
    for t in items:
        if not isinstance(t, dict):
            continue
        row = {k: t.get(k) for k in keep_fields}
        # priority 缺省 0；None / 非法值也归 0，保证 downstream 一致
        try:
            row["priority"] = int(t.get("priority") or 0)
        except (TypeError, ValueError):
            row["priority"] = 0
        slim.append(row)

    # 先整体 dump，超限则逐条弹出直到符合
    payload = json.dumps({"topics": slim}, ensure_ascii=False, separators=(",", ":"))
    while len(payload.encode("utf-8")) > _TOPICS_PAYLOAD_MAX_BYTES and slim:
        slim.pop()
        payload = json.dumps({"topics": slim}, ensure_ascii=False, separators=(",", ":"))
    return payload


PROMPT_TEMPLATE = """You are an offline wiki search agent.

Goal: Find the single most relevant insight entry inside a local 4-layer wiki and return a small JSON object describing the top hits.

Wiki root (absolute path): {wiki_tree}

Wiki layout (4 layers):
  layer-1: {wiki_tree}/wiki_types.json            (lists all wiki_type names)
  layer-2: {wiki_tree}/<type>/INDEX.md            (markdown table of items in that type)
  layer-3: {wiki_tree}/<type>/<item_slug>.md      (full entry, JSON frontmatter then ## sections)
  layer-4: {wiki_tree}/<type>/raw/<id>.jsonl      (raw card)

Topic index hint (pre-loaded; may be empty):
{topics_payload}

Hint usage: if the user query fuzzy-matches a topic (by title or tags), start exploration in `{wiki_tree}/<topic.wiki_type>/` — Glob that one directory first and Read its INDEX.md to pick the matching item_slug. DO NOT assume `topic.id` equals the on-disk slug — slugs may differ (e.g. id="postgres-pool-exhaustion" vs file "postgres_pool.md"). Fall back to full wiki glob only when no topic looks related.

User query:
{query}

Procedure (be efficient, do NOT narrate):
1. Glob "{wiki_tree}/*/INDEX.md" to discover the available wiki_types.
2. Read 1-2 most promising INDEX.md files to see candidate item slugs.
3. Read the single best <item_slug>.md file (full entry).
4. Score it 0.0-1.0 by how well it matches the user query (semantic, not lexical).
5. Output the result on its OWN final line, surrounded by sentinel fences. NO other text after the closing fence.

Required output format (verbatim):

<<<SEARCH_HITS>>>
{{"hits": [{{"wiki_type": "<type>", "item": "<slug-without-.md>", "score": <0.0-1.0>, "rationale": "<one-line>"}}]}}
<<<END>>>

Hard rules:
- Prefer Glob / Grep / Read. Bash is allowed only for read-only local inspection
  such as ls / find / cat; never modify files.
- Max 5 turns.
- "item" must be the slug WITHOUT the .md suffix.
- "hits" is an array; sort by score descending; you may include up to 3 entries but the first one is what matters.
- Do NOT wrap the JSON in markdown code fences.
"""


def _collect_text(message: AssistantMessage) -> str:
    parts: list[str] = []
    for block in message.content:
        text = getattr(block, "text", None)
        if text:
            parts.append(text)
    return "\n".join(parts)


_SENTINEL_RE = re.compile(
    r"<<<SEARCH_HITS>>>\s*(\{.*?\})\s*<<<END>>>",
    re.DOTALL,
)


def _extract_hits(raw: str) -> dict:
    match = _SENTINEL_RE.search(raw)
    if not match:
        # 退路 1：某些模型可能漏了 sentinel；尝试找最后一个完整 JSON 对象
        candidates = re.findall(r"\{[^{}]*\"hits\"[^{}]*\[.*?\][^{}]*\}", raw, re.DOTALL)
        if not candidates:
            raise ValueError(
                f"no SEARCH_HITS sentinel and no fallback JSON found in agent output "
                f"(len={len(raw)})"
            )
        return json.loads(candidates[-1])
    return json.loads(match.group(1))


async def _run_async(query_text: str, wiki_tree: str) -> dict:
    wiki_tree_abs = str(Path(wiki_tree).resolve())
    topics_payload = _load_topics_payload(Path(wiki_tree_abs))
    # topics_count 用于事后观测 layer-skip 是否被触发
    try:
        topics_count = len(json.loads(topics_payload).get("topics", []))
    except (ValueError, AttributeError):
        topics_count = 0
    prompt = PROMPT_TEMPLATE.format(
        wiki_tree=wiki_tree_abs,
        query=query_text,
        topics_payload=topics_payload,
    )
    emit_from_env(
        stage="search",
        status="running",
        source="search_agent",
        message=f"agentic search 开始：{query_text[:80]}",
        payload={"wiki_tree": wiki_tree_abs},
    )

    options = ClaudeAgentOptions(
        permission_mode="dontAsk",
        allowed_tools=["Glob", "Grep", "Read", "Bash"],
        max_turns=5,
        model=get_haiku_model(),
        cwd=wiki_tree_abs,
        extra_args={"bare": None},
    )

    sys.stderr.write(
        f"[search_agent] env: {env_summary()}\n"
        f"[search_agent] cwd: {wiki_tree_abs}\n"
        f"[search_agent] tools: {options.allowed_tools}\n"
    )

    collected: list[str] = []
    early_exit = False
    async for message in query(prompt=prompt, options=options):
        if isinstance(message, AssistantMessage):
            text = _collect_text(message)
            if text:
                collected.append(text)
                sys.stderr.write(f"[search_agent] assistant: {text[:200]!r}\n")
                joined = "\n".join(collected)
                if "<<<SEARCH_HITS>>>" in joined and "<<<END>>>" in joined:
                    early_exit = True
                    sys.stderr.write(
                        f"[search_agent] early_exit: sentinel closed after {len(collected)} assistant chunks\n"
                    )
                    break
        elif isinstance(message, ResultMessage):
            final = getattr(message, "result", None)
            if final:
                collected.append(str(final))
                sys.stderr.write(f"[search_agent] result: {str(final)[:200]!r}\n")

    raw = "\n".join(collected).strip()
    if not raw:
        raise RuntimeError("search_agent: empty response from MiniMax")
    hits = _extract_hits(raw)
    top = (hits.get("hits") or [None])[0]
    emit_from_env(
        stage="search",
        status="ok",
        source="search_agent",
        message=f"agentic search 命中 {top.get('item') if top else 'none'}",
        payload=hits,
        metrics={
            "score": top.get("score", 0) if top else 0,
            "early_exit": early_exit,
            "topics_count": topics_count,
        },
    )
    return hits


def _local_first(query_text: str, wiki_tree_root: str) -> dict | None:
    """本地预检索短路（M7 cache-miss 优化）。

    top score ≥ threshold 且 env `INSIGHTS_LOCAL_SEARCH=1`（默认开启）时返回 hits，
    同时发 stage=search_agent / cache=miss / source=local 的 metrics；
    否则返回 None，caller 落回 MiniMax haiku 路径。
    """
    if os.environ.get("INSIGHTS_LOCAL_SEARCH", "1") == "0":
        return None
    t0 = time.perf_counter()
    result = local_search.search(query_text, Path(wiki_tree_root).resolve())
    dt_ms = int((time.perf_counter() - t0) * 1000)
    if result.get("source") != "local":
        return None
    top = result["hits"][0] if result["hits"] else None
    emit_from_env(
        stage="search",
        status="ok",
        source="search_agent",
        message=f"local search 命中 {top.get('item') if top else 'none'}",
        payload=result,
        metrics={
            "score": top.get("score", 0) if top else 0,
            "early_exit": True,
            "topics_count": 0,
            "source": "local",
            "latency_ms_local": dt_ms,
        },
    )
    sys.stderr.write(
        f"[search_agent] local short-circuit hit={top} dt={dt_ms}ms\n"
    )
    return {"hits": result["hits"]}


def run(query: str, wiki_tree_root: str) -> dict:
    """同步 facade：被 hooks/insights_stop_hook.py 和 store.research() 复用。

    优先跑 local_search；若 top 分数过阈值直接返回，绕开 MiniMax SDK。
    否则退回 haiku-agent 原路径（不是 error fallback，是分层检索）。
    """
    local = _local_first(query, wiki_tree_root)
    if local is not None:
        return local
    return asyncio.run(_run_async(query, wiki_tree_root))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--query", required=True)
    ap.add_argument(
        "--wiki-tree",
        required=True,
        help="Absolute path to the wiki_tree root directory",
    )
    args = ap.parse_args()

    hits = run(args.query, args.wiki_tree)
    print("<<<SEARCH_HITS>>>")
    print(json.dumps(hits, ensure_ascii=False))
    print("<<<END>>>")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
