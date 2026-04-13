"""轻量 JSON 卡片存储 + bag-of-words Jaccard 检索。

包含两种 store：
- InsightStore：扁平 wiki.json 文件（run_demo.sh 的 baseline 路径）
- TreeInsightStore：4 层 wiki_tree 目录（validation.md task #4 要求）
"""

from __future__ import annotations

import json
import re
import threading
from pathlib import Path
from typing import Any

_TOKEN_RE = re.compile(r"[^\w]+", re.UNICODE)

_STOPWORDS = frozenset(
    {
        "the",
        "a",
        "an",
        "of",
        "in",
        "on",
        "at",
        "for",
        "to",
        "from",
        "and",
        "or",
        "but",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "with",
        "our",
        "your",
        "their",
        "my",
        "its",
        "this",
        "that",
        "these",
        "those",
        "it",
        "api",
        "app",
    }
)


def _stem(tok: str) -> str:
    """极简复数剥离：`connections` → `connection`、`spikes` → `spike`。"""
    if len(tok) > 4 and tok.endswith("ies"):
        return tok[:-3] + "y"
    if len(tok) > 3 and tok.endswith("s") and not tok.endswith("ss"):
        return tok[:-1]
    return tok


def _tokenize(text: str) -> set[str]:
    return {
        _stem(tok)
        for tok in _TOKEN_RE.split((text or "").lower())
        if tok and tok not in _STOPWORDS and not tok.isdigit()
    }


def _card_tokens(card: dict[str, Any]) -> set[str]:
    parts: list[str] = [str(card.get("title", ""))]
    tags = card.get("tags") or []
    if isinstance(tags, list):
        parts.extend(str(t) for t in tags)
    for field in ("context", "symptom", "root_cause", "fix", "body"):
        value = card.get(field)
        if value:
            parts.append(str(value))
    for field in ("applies_when", "do_not_apply_when"):
        value = card.get(field) or []
        if isinstance(value, list):
            parts.extend(str(x) for x in value)
    return _tokenize(" ".join(parts))


class InsightStore:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self._lock = threading.Lock()

    def load(self) -> list[dict[str, Any]]:
        with self._lock:
            return self._load_unlocked()

    def _load_unlocked(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        with self.path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and isinstance(data.get("cards"), list):
            return list(data["cards"])
        return []

    def save(self, cards: list[dict[str, Any]]) -> None:
        with self._lock:
            self._save_unlocked(cards)

    def _save_unlocked(self, cards: list[dict[str, Any]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        with tmp.open("w", encoding="utf-8") as fh:
            json.dump(cards, fh, ensure_ascii=False, indent=2)
        tmp.replace(self.path)

    def add(self, card: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(card, dict) or not card.get("id"):
            raise ValueError("card must be a dict with non-empty 'id'")
        with self._lock:
            cards = self._load_unlocked()
            cid = card["id"]
            replaced = False
            for idx, existing in enumerate(cards):
                if existing.get("id") == cid:
                    cards[idx] = card
                    replaced = True
                    break
            if not replaced:
                cards.append(card)
            self._save_unlocked(cards)
            return card

    def list_all(self) -> list[dict[str, Any]]:
        cards = self.load()
        return [
            {
                "id": c.get("id"),
                "title": c.get("title"),
                "tags": c.get("tags") or [],
                "author": c.get("author"),
            }
            for c in cards
        ]

    def search(self, q: str, k: int = 3) -> list[dict[str, Any]]:
        query_tokens = _tokenize(q or "")
        if not query_tokens:
            return []
        cards = self.load()
        scored: list[tuple[float, dict[str, Any]]] = []
        for card in cards:
            card_tokens = _card_tokens(card)
            if not card_tokens:
                continue
            union = query_tokens | card_tokens
            if not union:
                continue
            inter = query_tokens & card_tokens
            score = len(inter) / len(union)
            if score <= 0:
                continue
            scored.append((score, card))
        scored.sort(key=lambda item: item[0], reverse=True)
        results: list[dict[str, Any]] = []
        for score, card in scored[: max(1, int(k))]:
            enriched = dict(card)
            enriched["score"] = round(score, 4)
            results.append(enriched)
        return results


_FRONTMATTER_OPEN = "---\n"
_FRONTMATTER_CLOSE = "\n---\n"


def _parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith(_FRONTMATTER_OPEN):
        return {}, text
    end = text.find(_FRONTMATTER_CLOSE, len(_FRONTMATTER_OPEN))
    if end == -1:
        return {}, text
    raw = text[len(_FRONTMATTER_OPEN) : end]
    body = text[end + len(_FRONTMATTER_CLOSE) :]
    try:
        fm = json.loads(raw)
    except json.JSONDecodeError:
        return {}, text
    if not isinstance(fm, dict):
        return {}, text
    return fm, body


def _split_sections(body: str) -> dict[str, str]:
    out: dict[str, str] = {}
    current: str | None = None
    lines: list[str] = []
    for line in body.splitlines():
        if line.startswith("## "):
            if current is not None:
                out[current] = "\n".join(lines).strip()
            current = line[3:].strip()
            lines = []
        else:
            lines.append(line)
    if current is not None:
        out[current] = "\n".join(lines).strip()
    return out


def _render_item_md(card: dict[str, Any]) -> str:
    def bullet(items: list[Any]) -> str:
        if not items:
            return "(none)"
        return "\n".join(f"- {x}" for x in items)

    fm = {
        "id": card["id"],
        "title": card.get("title", ""),
        "author": card.get("author", ""),
        "confidence": float(card.get("confidence", 0.5)),
        "tags": list(card.get("tags") or []),
        "status": card.get("status", "active"),
        "applies_when": list(card.get("applies_when") or []),
        "do_not_apply_when": list(card.get("do_not_apply_when") or []),
        "raw_log": card.get("raw_log", f"./raw/{card['id']}.jsonl"),
    }
    return "\n".join(
        [
            "---",
            json.dumps(fm, ensure_ascii=False, indent=2),
            "---",
            "",
            f"# {card.get('title','')}",
            "",
            f"> author: {card.get('author','?')} · confidence: {card.get('confidence','?')}",
            "",
            "## Description",
            "",
            card.get("context", "") or "",
            "",
            card.get("root_cause", "") or "",
            "",
            "## Bad example",
            "",
            card.get("symptom", "") or "",
            "",
            "## Good example",
            "",
            card.get("fix", "") or "",
            "",
            "## Applies when",
            "",
            bullet(card.get("applies_when") or []),
            "",
            "## Do NOT apply when",
            "",
            bullet(card.get("do_not_apply_when") or []),
            "",
            "## Raw log",
            "",
            f"[{fm['raw_log']}]({fm['raw_log']})",
            "",
        ]
    )


class TreeInsightStore:
    """读取（以及 Phase 3 的 CRUD）4 层 wiki_tree 目录结构。

    目录 layout::

        {root}/wiki_types.json
        {root}/{wiki_type}/INDEX.md
        {root}/{wiki_type}/{item_slug}.md
        {root}/{wiki_type}/raw/{card_id}.jsonl
    """

    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        self._lock = threading.Lock()

    def _load_types(self) -> list[str]:
        f = self.root / "wiki_types.json"
        if not f.is_file():
            return []
        data = json.loads(f.read_text(encoding="utf-8"))
        return list(data.get("types") or [])

    def _save_types(self, types: list[str]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        (self.root / "wiki_types.json").write_text(
            json.dumps({"types": sorted(set(types))}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _iter_item_files(self):
        for wtype in self._load_types():
            tdir = self.root / wtype
            if not tdir.is_dir():
                continue
            for md in sorted(tdir.glob("*.md")):
                if md.name == "INDEX.md":
                    continue
                yield wtype, md

    def _item_to_card(self, wtype: str, md_path: Path) -> dict[str, Any] | None:
        fm, body = _parse_frontmatter(md_path.read_text(encoding="utf-8"))
        if not fm.get("id"):
            return None
        sections = _split_sections(body)
        card: dict[str, Any] = dict(fm)
        card["wiki_type"] = wtype
        card["item_slug"] = md_path.stem
        card["context"] = sections.get("Description", "").split("\n\n", 1)[0].strip()
        card["root_cause"] = sections.get("Description", "").strip()
        card["symptom"] = sections.get("Bad example", "").strip()
        card["fix"] = sections.get("Good example", "").strip()
        return card

    def _find_item_path(self, card_id: str) -> tuple[str, Path] | None:
        with self._lock:
            for wtype, md in self._iter_item_files():
                fm, _ = _parse_frontmatter(md.read_text(encoding="utf-8"))
                if fm.get("id") == card_id:
                    return wtype, md
        return None

    # --- read API (shared interface with InsightStore) ---

    def load(self) -> list[dict[str, Any]]:
        cards: list[dict[str, Any]] = []
        for wtype, md in self._iter_item_files():
            card = self._item_to_card(wtype, md)
            if card:
                cards.append(card)
        return cards

    def list_all(self) -> list[dict[str, Any]]:
        return [
            {
                "id": c.get("id"),
                "title": c.get("title"),
                "tags": c.get("tags") or [],
                "author": c.get("author"),
                "wiki_type": c.get("wiki_type"),
                "status": c.get("status", "active"),
            }
            for c in self.load()
        ]

    def search(self, q: str, k: int = 3) -> list[dict[str, Any]]:
        query_tokens = _tokenize(q or "")
        if not query_tokens:
            return []
        scored: list[tuple[float, dict[str, Any]]] = []
        for card in self.load():
            if card.get("status") == "not_triggered":
                continue
            card_tokens = _card_tokens(card)
            if not card_tokens:
                continue
            union = query_tokens | card_tokens
            inter = query_tokens & card_tokens
            if not union or not inter:
                continue
            score = len(inter) / len(union)
            if score <= 0:
                continue
            scored.append((score, card))
        scored.sort(key=lambda item: item[0], reverse=True)
        results: list[dict[str, Any]] = []
        for score, card in scored[: max(1, int(k))]:
            enriched = dict(card)
            enriched["score"] = round(score, 4)
            results.append(enriched)
        return results

    # --- Phase 3 CRUD (write API) ---

    def _rebuild_index(self, wtype: str) -> None:
        tdir = self.root / wtype
        lines = [
            f"# {wtype} · INDEX",
            "",
            "| name | description | trigger when | docs |",
            "|------|-------------|--------------|------|",
        ]
        for md in sorted(tdir.glob("*.md")):
            if md.name == "INDEX.md":
                continue
            fm, _ = _parse_frontmatter(md.read_text(encoding="utf-8"))
            if not fm.get("id"):
                continue
            slug = md.stem
            description = (fm.get("title") or "").replace("|", "\\|")
            trigger_when = ", ".join((fm.get("tags") or [])[:4])
            lines.append(
                f"| {slug} | {description} | {trigger_when} | [{slug}.md](./{slug}.md) |"
            )
        lines.append("")
        (tdir / "INDEX.md").write_text("\n".join(lines), encoding="utf-8")

    def _write_card(self, wtype: str, slug: str, card: dict[str, Any]) -> Path:
        tdir = self.root / wtype
        tdir.mkdir(parents=True, exist_ok=True)
        (tdir / "raw").mkdir(exist_ok=True)
        raw_rel = card.get("raw_log") or f"./raw/{card['id']}.jsonl"
        card["raw_log"] = raw_rel
        (tdir / "raw" / f"{card['id']}.jsonl").write_text(
            json.dumps(
                {k: v for k, v in card.items() if k not in {"wiki_type", "item_slug", "score"}},
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )
        path = tdir / f"{slug}.md"
        path.write_text(_render_item_md(card), encoding="utf-8")
        return path

    def add(self, card: dict[str, Any], wiki_type: str = "general") -> dict[str, Any]:
        if not isinstance(card, dict) or not card.get("id"):
            raise ValueError("card must be a dict with non-empty 'id'")
        with self._lock:
            existing = None
            for wtype, md in self._iter_item_files():
                fm, _ = _parse_frontmatter(md.read_text(encoding="utf-8"))
                if fm.get("id") == card["id"]:
                    existing = (wtype, md)
                    break
            if existing is not None:
                wtype, md = existing
                slug = md.stem
            else:
                wtype = wiki_type
                slug = card.get("item_slug") or card["id"].replace("-", "_")
            self._write_card(wtype, slug, card)
            types = set(self._load_types())
            types.add(wtype)
            self._save_types(sorted(types))
            self._rebuild_index(wtype)
            return card

    def delete(self, card_id: str) -> bool:
        found = self._find_item_path(card_id)
        if not found:
            return False
        wtype, md = found
        with self._lock:
            try:
                md.unlink()
            except FileNotFoundError:
                pass
            raw = self.root / wtype / "raw" / f"{card_id}.jsonl"
            if raw.exists():
                raw.unlink()
            self._rebuild_index(wtype)
            return True

    def edit(self, card_id: str, patch: dict[str, Any]) -> dict[str, Any] | None:
        found = self._find_item_path(card_id)
        if not found:
            return None
        wtype, md = found
        with self._lock:
            card = self._item_to_card(wtype, md)
            if not card:
                return None
            for key, value in (patch or {}).items():
                if key in {"id", "wiki_type", "item_slug", "score"}:
                    continue
                card[key] = value
            self._write_card(wtype, md.stem, card)
            self._rebuild_index(wtype)
            return card

    def tag(self, card_id: str, tags: list[str], *, sticky: bool = True) -> dict[str, Any] | None:
        found = self._find_item_path(card_id)
        if not found:
            return None
        wtype, md = found
        with self._lock:
            card = self._item_to_card(wtype, md)
            if not card:
                return None
            current = list(card.get("tags") or [])
            merged = list(dict.fromkeys(current + list(tags or [])))
            card["tags"] = merged
            if "not_triggered" in (tags or []):
                card["status"] = "not_triggered"
                card["sticky_not_triggered"] = bool(sticky)
            self._write_card(wtype, md.stem, card)
            self._rebuild_index(wtype)
            return card

    def merge(self, source_id: str, target_id: str) -> dict[str, Any] | None:
        src = self._find_item_path(source_id)
        tgt = self._find_item_path(target_id)
        if not src or not tgt:
            return None
        src_wtype, src_md = src
        tgt_wtype, tgt_md = tgt
        with self._lock:
            src_card = self._item_to_card(src_wtype, src_md)
            tgt_card = self._item_to_card(tgt_wtype, tgt_md)
            if not src_card or not tgt_card:
                return None
            # 合并 tags，保留 not_triggered
            merged_tags = list(
                dict.fromkeys((tgt_card.get("tags") or []) + (src_card.get("tags") or []))
            )
            tgt_card["tags"] = merged_tags
            # 合并文字段：target 优先，非空 source 追加到 body
            for field in ("context", "root_cause", "symptom", "fix"):
                src_val = src_card.get(field) or ""
                tgt_val = tgt_card.get(field) or ""
                if src_val and src_val.strip() and src_val.strip() not in tgt_val:
                    tgt_card[field] = (tgt_val + "\n\n" + src_val).strip()
            # 合并 applies_when / do_not_apply_when
            for field in ("applies_when", "do_not_apply_when"):
                merged = list(
                    dict.fromkeys((tgt_card.get(field) or []) + (src_card.get(field) or []))
                )
                tgt_card[field] = merged
            # not_triggered sticky 标签在合并时保留
            if (
                src_card.get("status") == "not_triggered"
                or tgt_card.get("status") == "not_triggered"
            ):
                tgt_card["status"] = "not_triggered"
                if "not_triggered" not in tgt_card["tags"]:
                    tgt_card["tags"].append("not_triggered")
            self._write_card(tgt_wtype, tgt_md.stem, tgt_card)
            # 删除 source
            try:
                src_md.unlink()
            except FileNotFoundError:
                pass
            src_raw = self.root / src_wtype / "raw" / f"{source_id}.jsonl"
            if src_raw.exists():
                src_raw.unlink()
            self._rebuild_index(src_wtype)
            if src_wtype != tgt_wtype:
                self._rebuild_index(tgt_wtype)
            return tgt_card

    def research(self, query: str) -> dict[str, Any]:
        """调用 Phase 5 的 search_agent 做一次真 AI 语义搜索并回写一张新卡。

        严禁 fallback：search_agent 的任何异常直接向上传播。
        """
        import importlib.util
        from datetime import datetime, timezone

        demo_codes = Path(__file__).resolve().parent.parent
        spec_path = demo_codes / "search_agent.py"
        if not spec_path.is_file():
            raise FileNotFoundError(f"search_agent.py not found at {spec_path}")
        spec = importlib.util.spec_from_file_location("search_agent", spec_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"cannot load search_agent from {spec_path}")
        search_agent = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(search_agent)

        hits = search_agent.run(query=query, wiki_tree_root=str(self.root))
        top = (hits or {}).get("hits") or []
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        card = {
            "id": f"research-{timestamp}",
            "title": f"Research result for: {query[:80]}",
            "author": "research-agent",
            "confidence": 0.5,
            "tags": ["research", "agentic"],
            "status": "active",
            "applies_when": [],
            "do_not_apply_when": [],
            "context": query,
            "symptom": "",
            "root_cause": json.dumps(hits, ensure_ascii=False),
            "fix": (top[0].get("rationale") if top else "") or "see hits",
        }
        return self.add(card, wiki_type="research")
