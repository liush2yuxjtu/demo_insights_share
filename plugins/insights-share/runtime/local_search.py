"""本地 token-overlap 预检索（M7 cache-miss 优化）。

对齐 proposal_generation_latency.md §优化方案 O7 的轻量版：
不引入 embedding 依赖，先用 Jaccard token 重合度对 topics.json + 各
`<type>/INDEX.md` 的候选条目做排序，若 top 分数 ≥ 阈值即短路，不走
MiniMax SDK。命中时耗时 <200ms；未命中时退回 search_agent 原有 haiku 路径。

与既有 search_agent 契约完全一致：输入 (query, wiki_tree_root)，输出
`{"hits":[{"wiki_type","item","score","rationale","source"}], ...}`。

严禁 fallback：文件 IO / 解析异常一律 raise；caller 决定是否接受本地 miss。
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

# Jaccard ≥ 阈值即视为高置信命中，短路 MiniMax。
# 偏宽松：英文 query 与中文 topic 只会共享 slug token，overlap 天然偏低；
# 宽松阈值让多数真命中走本地路径，漏掉的交给 MiniMax。
DEFAULT_SCORE_THRESHOLD = 0.12

# Chinese bigram + ASCII word 混合分词：
#   - 连续英文/数字按 \w 词
#   - 中文字符切 bigram（2-gram）
_ASCII_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_-]{1,}")
_CJK_RE = re.compile(r"[\u4e00-\u9fff]+")

_STOPWORDS = {
    "的", "是", "在", "了", "和", "与", "及", "或",
    "the", "a", "an", "of", "to", "for", "in", "on", "and", "or",
    "is", "are", "be", "was", "were", "as", "by", "at",
}


def _tokenize(text: str) -> set[str]:
    """把一段文本切成 token set（小写、去停用词、含 CJK bigram）。"""
    if not text:
        return set()
    lower = text.lower()
    tokens: set[str] = set()

    # ASCII / 数字 / 破折号 合并
    for m in _ASCII_TOKEN_RE.findall(lower):
        if m not in _STOPWORDS and len(m) >= 2:
            tokens.add(m)

    # CJK：整段抽出后切 bigram
    for chunk in _CJK_RE.findall(text):
        if len(chunk) == 1:
            tokens.add(chunk)
        else:
            for i in range(len(chunk) - 1):
                bg = chunk[i : i + 2]
                if bg not in _STOPWORDS:
                    tokens.add(bg)
    return tokens


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


@dataclass(frozen=True)
class Candidate:
    wiki_type: str
    item: str
    tokens: frozenset[str]
    priority: int
    created_at: str
    source_tag: str


def _parse_index_rows(index_path: Path) -> list[tuple[str, str, str]]:
    """从 `<type>/INDEX.md` 抽出 `(name, description, trigger)` 行。

    期待表格形如 `| name | description | trigger | docs |`；前两列是表头/分隔符，
    其余列解析；不合法行跳过，不抛。
    """
    rows: list[tuple[str, str, str]] = []
    if not index_path.is_file():
        return rows
    for line in index_path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s.startswith("|") or "---" in s:
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        # 跳过表头
        if len(cells) < 2 or cells[0].lower() == "name":
            continue
        name = cells[0]
        desc = cells[1] if len(cells) > 1 else ""
        trig = cells[2] if len(cells) > 2 else ""
        if not name or name.startswith("-"):
            continue
        rows.append((name, desc, trig))
    return rows


def _iter_topic_candidates(wiki_tree_root: Path) -> list[Candidate]:
    topics_path = wiki_tree_root / "topics.json"
    if not topics_path.exists():
        return []
    raw = json.loads(topics_path.read_text(encoding="utf-8"))
    items = raw.get("topics", []) if isinstance(raw, dict) else []
    out: list[Candidate] = []
    for t in items:
        if not isinstance(t, dict):
            continue
        title = t.get("title") or ""
        tags = t.get("tags") or []
        wiki_type = t.get("wiki_type") or ""
        topic_id = t.get("id") or ""
        priority = int(t.get("priority") or 0)
        created_at = t.get("created_at") or ""
        if not wiki_type:
            continue
        blob = " ".join(
            [title, topic_id, " ".join(x for x in tags if isinstance(x, str))]
        )
        toks = _tokenize(blob)
        if not toks:
            continue
        out.append(
            Candidate(
                wiki_type=wiki_type,
                item=topic_id,
                tokens=frozenset(toks),
                priority=priority,
                created_at=created_at,
                source_tag="topics_json",
            )
        )
    return out


def _iter_index_candidates(wiki_tree_root: Path) -> list[Candidate]:
    out: list[Candidate] = []
    for index_md in sorted(wiki_tree_root.glob("*/INDEX.md")):
        wiki_type = index_md.parent.name
        for name, desc, trig in _parse_index_rows(index_md):
            blob = " ".join([name, desc, trig])
            toks = _tokenize(blob)
            if not toks:
                continue
            # INDEX.md 里的 name 即是 layer-3 slug
            out.append(
                Candidate(
                    wiki_type=wiki_type,
                    item=name,
                    tokens=frozenset(toks),
                    priority=0,
                    created_at="",
                    source_tag="index_md",
                )
            )
    return out


def _merge_candidates(
    topics: list[Candidate], indexes: list[Candidate]
) -> list[Candidate]:
    """合并 topics.json + INDEX.md：同 (wiki_type,item) 去重，topics.json 优先保留。"""
    seen: set[tuple[str, str]] = set()
    merged: list[Candidate] = []
    for c in topics:
        key = (c.wiki_type, c.item)
        if key in seen:
            continue
        seen.add(key)
        merged.append(c)
    for c in indexes:
        key = (c.wiki_type, c.item)
        if key in seen:
            continue
        seen.add(key)
        merged.append(c)
    return merged


def search(
    query: str,
    wiki_tree_root: Path,
    threshold: float = DEFAULT_SCORE_THRESHOLD,
    top_n: int = 3,
) -> dict:
    """本地检索。返回 hits dict，始终包含 `source` 字段。

    - `source=local` 当 top 分数 ≥ threshold（高置信短路）
    - `source=local_low` 当 top 分数 < threshold（caller 决定是否退回 MiniMax）
    """
    root = Path(wiki_tree_root).resolve()
    q_tokens = _tokenize(query)
    if not q_tokens:
        return {"hits": [], "source": "local_low", "reason": "empty_query_tokens"}

    cands = _merge_candidates(
        _iter_topic_candidates(root),
        _iter_index_candidates(root),
    )
    if not cands:
        return {"hits": [], "source": "local_low", "reason": "no_candidates"}

    scored: list[tuple[Candidate, float]] = []
    for c in cands:
        s = _jaccard(q_tokens, set(c.tokens))
        if s <= 0.0:
            continue
        scored.append((c, s))

    # 排序：score desc → priority desc → created_at asc（稳定）
    scored.sort(key=lambda x: (-x[1], -x[0].priority, x[0].created_at))
    top = scored[:top_n]

    hits = [
        {
            "wiki_type": c.wiki_type,
            "item": c.item,
            "score": round(s, 3),
            "rationale": f"local token overlap score={s:.3f} via {c.source_tag}",
            "source": "local",
        }
        for c, s in top
    ]
    best = top[0][1] if top else 0.0
    tier = "local" if best >= threshold else "local_low"
    return {
        "hits": hits,
        "source": tier,
        "top_score": round(best, 3),
        "threshold": threshold,
    }


__all__ = [
    "DEFAULT_SCORE_THRESHOLD",
    "search",
]
