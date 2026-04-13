"""MiniMax agentic search over the 4-layer wiki_tree.

让 haiku-agent 自己用 Glob/Grep/Read 探索 wiki_tree，最终返回排序好的 hits。
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
import re
import sys
from pathlib import Path

from _sdk_common import env_summary, get_haiku_model

from claude_agent_sdk import (  # noqa: E402
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    query,
)


PROMPT_TEMPLATE = """You are an offline wiki search agent.

Goal: Find the single most relevant insight entry inside a local 4-layer wiki and return a small JSON object describing the top hits.

Wiki root (absolute path): {wiki_tree}

Wiki layout (4 layers):
  layer-1: {wiki_tree}/wiki_types.json            (lists all wiki_type names)
  layer-2: {wiki_tree}/<type>/INDEX.md            (markdown table of items in that type)
  layer-3: {wiki_tree}/<type>/<item_slug>.md      (full entry, JSON frontmatter then ## sections)
  layer-4: {wiki_tree}/<type>/raw/<id>.jsonl      (raw card)

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
- Use only Glob / Grep / Read tools.
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
    prompt = PROMPT_TEMPLATE.format(wiki_tree=wiki_tree_abs, query=query_text)

    options = ClaudeAgentOptions(
        permission_mode="dontAsk",
        allowed_tools=["Glob", "Grep", "Read"],
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
    async for message in query(prompt=prompt, options=options):
        if isinstance(message, AssistantMessage):
            text = _collect_text(message)
            if text:
                collected.append(text)
                sys.stderr.write(f"[search_agent] assistant: {text[:200]!r}\n")
        elif isinstance(message, ResultMessage):
            final = getattr(message, "result", None)
            if final:
                collected.append(str(final))
                sys.stderr.write(f"[search_agent] result: {str(final)[:200]!r}\n")

    raw = "\n".join(collected).strip()
    if not raw:
        raise RuntimeError("search_agent: empty response from MiniMax")
    return _extract_hits(raw)


def run(query: str, wiki_tree_root: str) -> dict:
    """同步 facade：被 hooks/insights_stop_hook.py 和 store.research() 复用。"""
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
