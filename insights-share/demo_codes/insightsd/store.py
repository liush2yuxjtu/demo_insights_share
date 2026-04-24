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

from .signing import CardSignatureService, sha256_hex

_TOKEN_RE = re.compile(r"[^\w]+", re.UNICODE)

_SECRET_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9_-]{10,}"),
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    re.compile(r"Bearer[ \t]+[A-Za-z0-9._~+/-]{10,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
)
_SENSITIVE_KEYS = {
    "api_key",
    "apikey",
    "authorization",
    "bearer",
    "password",
    "secret",
    "token",
}

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


def redact_sensitive_text(text: str) -> str:
    redacted = text
    for pattern in _SECRET_PATTERNS:
        redacted = pattern.sub("<redacted:secret>", redacted)
    return redacted


def _redact_for_raw_log(value: Any, *, key: str = "") -> Any:
    lowered = key.lower().replace("-", "_")
    if any(part in lowered for part in _SENSITIVE_KEYS):
        return "<redacted:field>"
    if isinstance(value, str):
        return redact_sensitive_text(value)
    if isinstance(value, list):
        return [_redact_for_raw_log(item) for item in value]
    if isinstance(value, dict):
        return {
            item_key: _redact_for_raw_log(item_value, key=str(item_key))
            for item_key, item_value in value.items()
        }
    return value


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


def _normalize_team(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    team = value.strip()
    return team or None


def _team_matches(record: dict[str, Any], team: str | None) -> bool:
    if team is None:
        return True
    return _normalize_team(record.get("team")) == team


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


def search_cards(
    cards: list[dict[str, Any]],
    q: str,
    *,
    k: int = 3,
    skip_not_triggered: bool = False,
) -> list[dict[str, Any]]:
    """Jaccard + tag_bonus 打分（保留原 Jaccard 兼容 + tag 高信号加权）。

    P1 fix (2026-04-23)：纯 Jaccard `|inter|/|union|` 让 canonical 卡（alice-pgpool
    等）被精简短卡 (m1-project-001) 以高 Jaccard 胜出。而长 noise 卡
    (carol do_not_apply_when 含 "postgres" 干扰词) 又会借 coverage 反超。

    最终策略：
    - 保留 Jaccard（对短精准卡友好）
    - 加 `0.15 * tag_hit_count`（tags 是高信号，noise-free，线性加权）
    - 不用 coverage（避免长 noise 卡伪命中）

    trigger_rate.py 实测（tree mode）：
    - before (flat mode): train f1=0.0 test f1=0.0
    - tree mode only:     train f1=0.53 test f1=0.75
    - tree + tag_bonus:   train f1=? test f1=?（见 finish_log）
    """
    query_tokens = _tokenize(q or "")
    if not query_tokens:
        return []
    scored: list[tuple[float, dict[str, Any]]] = []
    for original in cards:
        card = dict(original)
        if skip_not_triggered and card.get("status") == "not_triggered":
            continue
        card_tokens = _card_tokens(card)
        if not card_tokens:
            continue
        inter = query_tokens & card_tokens
        if not inter:
            continue
        union = query_tokens | card_tokens
        jaccard = len(inter) / len(union) if union else 0.0
        # tag bonus：query 与 card tags 的 token 重叠计数（线性 0.15/命中）
        card_tags = card.get("tags") or []
        tag_text = " ".join(str(t) for t in card_tags if isinstance(t, str))
        tag_tokens = _tokenize(tag_text)
        tag_hit_count = len(query_tokens & tag_tokens)
        score = jaccard + 0.15 * tag_hit_count
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


class InsightStore:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self._lock = threading.Lock()

    def load(self, team: str | None = None) -> list[dict[str, Any]]:
        # flat 模式不区分 team，参数仅为 TreeInsightStore 接口兼容
        _ = team
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

    def list_all(self, team: str | None = None) -> list[dict[str, Any]]:
        cards = self.load()
        if team is not None:
            cards = [card for card in cards if _team_matches(card, team)]
        return [
            {
                "id": c.get("id"),
                "title": c.get("title"),
                "tags": c.get("tags") or [],
                "author": c.get("author"),
                "team": _normalize_team(c.get("team")),
            }
            for c in cards
        ]

    def search(self, q: str, k: int = 3, team: str | None = None) -> list[dict[str, Any]]:
        cards = self.load()
        if team is not None:
            cards = [card for card in cards if _team_matches(card, team)]
        return search_cards(cards, q, k=k)


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

    description = (
        card.get("description")
        or "\n\n".join(
            part.strip()
            for part in [
                str(card.get("context") or "").strip(),
                str(card.get("root_cause") or "").strip(),
            ]
            if part and part.strip()
        )
    ).strip()
    bad_example = (card.get("bad_example") or card.get("symptom") or "").strip()
    good_example = (card.get("good_example") or card.get("fix") or "").strip()

    fm = {
        "id": card["id"],
        "title": card.get("title", ""),
        "author": card.get("author", ""),
        "team": _normalize_team(card.get("team")),
        "confidence": float(card.get("confidence", 0.5)),
        "tags": list(card.get("tags") or []),
        "status": card.get("status", "active"),
        "applies_when": list(card.get("applies_when") or []),
        "do_not_apply_when": list(card.get("do_not_apply_when") or []),
        "raw_log": card.get("raw_log", f"./raw/{card['id']}.jsonl"),
    }
    fm["topic_id"] = card.get("topic_id", "")
    fm["label"] = card.get("label", "good")
    fm["label_note"] = card.get("label_note", "")
    fm["label_override"] = card.get("label_override", None)
    fm["label_override_by"] = card.get("label_override_by", None)
    fm["label_override_at"] = card.get("label_override_at", None)
    fm["raw_log_type"] = card.get("raw_log_type", "jsonl")
    fm["raw_log_sha256"] = card.get("raw_log_sha256", "")
    fm["signature_algorithm"] = card.get("signature_algorithm")
    fm["signature_schema"] = card.get("signature_schema")
    fm["signature_key_id"] = card.get("signature_key_id")
    fm["signature"] = card.get("signature")
    fm["signature_signed_at"] = card.get("signature_signed_at")
    return "\n".join(
        [
            "---",
            json.dumps(fm, ensure_ascii=False, indent=2),
            "---",
            "",
            f"# {card.get('title','')}",
            "",
            (
                f"> author: {card.get('author','?')} · "
                f"team: {_normalize_team(card.get('team')) or 'shared'} · "
                f"confidence: {card.get('confidence','?')}"
            ),
            "",
            "## Description",
            "",
            description,
            "",
            "## Bad example",
            "",
            bad_example,
            "",
            "## Good example",
            "",
            good_example,
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


def migrate_card(card: dict[str, Any], slug: str) -> dict[str, Any]:
    """为老 card 补齐缺失字段：topic_id / label / raw_log_type。

    不会覆盖已有值。slug 用于生成 topic_id（把下划线替换为连字符）。
    """
    if "topic_id" not in card or not card["topic_id"]:
        card["topic_id"] = slug.replace("_", "-")
    if "label" not in card or not card["label"]:
        card["label"] = "good"
    if "raw_log_type" not in card or not card["raw_log_type"]:
        card["raw_log_type"] = "jsonl"
    return card


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
        if self.root.exists() and not self.root.is_dir():
            raise ValueError(
                f"TreeInsightStore root must be a directory, got file: {self.root}. "
                "Tree mode 需要 --store 指向 wiki_tree 目录，不是 wiki.json 文件。"
            )
        self._lock = threading.Lock()
        self.signatures = CardSignatureService()

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
        description = sections.get("Description", "").strip()
        bad_example = sections.get("Bad example", "").strip()
        good_example = sections.get("Good example", "").strip()
        card["description"] = description
        card["bad_example"] = bad_example
        card["good_example"] = good_example
        card["context"] = description.split("\n\n", 1)[0].strip()
        card["root_cause"] = description
        card["symptom"] = bad_example
        card["fix"] = good_example
        card["topic_id"] = fm.get("topic_id", "")
        card["label"] = fm.get("label", "good")
        card["label_note"] = fm.get("label_note", "")
        card["label_override"] = fm.get("label_override", None)
        card["label_override_by"] = fm.get("label_override_by", None)
        card["label_override_at"] = fm.get("label_override_at", None)
        card["raw_log_type"] = fm.get("raw_log_type", "jsonl")
        card["raw_log_sha256"] = fm.get("raw_log_sha256", "")
        card["signature_algorithm"] = fm.get("signature_algorithm")
        card["signature_schema"] = fm.get("signature_schema")
        card["signature_key_id"] = fm.get("signature_key_id")
        card["signature"] = fm.get("signature")
        card["signature_signed_at"] = fm.get("signature_signed_at")
        card["team"] = _normalize_team(fm.get("team"))
        raw_rel = str(card.get("raw_log") or "").strip()
        raw_bytes = None
        if raw_rel.startswith("./"):
            raw_path = (md_path.parent / raw_rel[2:]).resolve()
            try:
                raw_bytes = raw_path.read_bytes()
            except OSError:
                raw_bytes = None
        verify = self.signatures.verify_card(card, raw_log_bytes=raw_bytes)
        card["signature_status"] = verify.status
        card["signature_error"] = verify.error
        return card

    def _find_item_path(self, card_id: str) -> tuple[str, Path] | None:
        with self._lock:
            for wtype, md in self._iter_item_files():
                fm, _ = _parse_frontmatter(md.read_text(encoding="utf-8"))
                if fm.get("id") == card_id:
                    return wtype, md
        return None

    # --- read API (shared interface with InsightStore) ---

    def load(self, team: str | None = None) -> list[dict[str, Any]]:
        cards: list[dict[str, Any]] = []
        for wtype, md in self._iter_item_files():
            card = self._item_to_card(wtype, md)
            if card and _team_matches(card, team):
                cards.append(card)
        return cards

    def list_all(self, team: str | None = None) -> list[dict[str, Any]]:
        return [
            {
                "id": c.get("id"),
                "title": c.get("title"),
                "tags": c.get("tags") or [],
                "author": c.get("author"),
                "wiki_type": c.get("wiki_type"),
                "status": c.get("status", "active"),
                "team": _normalize_team(c.get("team")),
                "signature_status": c.get("signature_status", "legacy-unsigned"),
                "signature_error": c.get("signature_error"),
                "signature_key_id": c.get("signature_key_id"),
                "signature_signed_at": c.get("signature_signed_at"),
            }
            for c in self.load(team=team)
        ]

    def search(self, q: str, k: int = 3, team: str | None = None) -> list[dict[str, Any]]:
        cards = [
            card
            for card in self.load(team=team)
            if card.get("signature_status") != "invalid"
        ]
        results = search_cards(cards, q, k=k, skip_not_triggered=True)
        enriched: list[dict[str, Any]] = []
        for card in results:
            item = dict(card)
            item["effective_label"] = item.get("label_override") or item.get("label", "good")
            enriched.append(item)
        return enriched

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
        raw_log_type = card.get("raw_log_type", "jsonl")
        if raw_log_type == "export":
            ext = "txt"
            raw_content = (
                redact_sensitive_text(str(card.get("raw_log_export_content") or ""))
                + "\n"
            ).encode("utf-8")
        else:
            ext = "jsonl"
            raw_card = _redact_for_raw_log(
                {k: v for k, v in card.items() if k not in {"wiki_type", "item_slug", "score"}}
            )
            raw_content = (
                json.dumps(raw_card, ensure_ascii=False)
                + "\n"
            ).encode("utf-8")
        raw_rel = f"./raw/{card['id']}.{ext}"
        signed_card = dict(card)
        signed_card["title"] = signed_card.get("title", "")
        signed_card["author"] = signed_card.get("author", "")
        signed_card["team"] = _normalize_team(signed_card.get("team"))
        signed_card["confidence"] = float(signed_card.get("confidence", 0.5))
        signed_card["tags"] = list(signed_card.get("tags") or [])
        signed_card["status"] = signed_card.get("status", "active")
        signed_card["applies_when"] = list(signed_card.get("applies_when") or [])
        signed_card["do_not_apply_when"] = list(signed_card.get("do_not_apply_when") or [])
        signed_card["topic_id"] = signed_card.get("topic_id", "")
        signed_card["label"] = signed_card.get("label", "good")
        signed_card["label_note"] = signed_card.get("label_note", "")
        signed_card["label_override"] = signed_card.get("label_override", None)
        signed_card["label_override_by"] = signed_card.get("label_override_by", None)
        signed_card["label_override_at"] = signed_card.get("label_override_at", None)
        signed_card["raw_log_type"] = signed_card.get("raw_log_type", "jsonl")
        signed_card["raw_log"] = raw_rel
        signed_card["raw_log_sha256"] = sha256_hex(raw_content)
        signed_card["description"] = (
            signed_card.get("description")
            or "\n\n".join(
                part.strip()
                for part in [
                    str(signed_card.get("context") or "").strip(),
                    str(signed_card.get("root_cause") or "").strip(),
                ]
                if part and part.strip()
            )
        ).strip()
        signed_card["bad_example"] = (signed_card.get("bad_example") or signed_card.get("symptom") or "").strip()
        signed_card["good_example"] = (signed_card.get("good_example") or signed_card.get("fix") or "").strip()
        signed_card = self.signatures.sign_card(signed_card)
        (tdir / "raw" / f"{card['id']}.{ext}").write_bytes(raw_content)
        path = tdir / f"{slug}.md"
        path.write_text(_render_item_md(signed_card), encoding="utf-8")
        return path

    def add(self, card: dict[str, Any], wiki_type: str = "general") -> dict[str, Any]:
        if not isinstance(card, dict) or not card.get("id"):
            raise ValueError("card must be a dict with non-empty 'id'")
        team = _normalize_team(card.get("team") or card.get("team_namespace"))
        if team is None:
            card.pop("team", None)
        else:
            card["team"] = team
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
            return self._item_to_card(wtype, self.root / wtype / f"{slug}.md") or card

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

    # Admin /edit 不得修改的字段：id/结构性元数据 + 原 label + raw_log 原始证据。
    # 对 label 的覆盖请走 /insights/{id}/relabel（只写 label_override 三元组）。
    # 详见 proposal/proposal_conflict_design.md §"管理员权限范围"。
    _EDIT_PROTECTED = frozenset({
        "id", "wiki_type", "item_slug", "score",
        "label",
        "raw_log", "raw_log_type", "raw_log_sha256", "raw_log_path",
        "raw_log_export_content",
        "signature", "signature_algorithm", "signature_schema",
        "signature_key_id", "signature_signed_at", "signature_status",
    })

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
                if key in self._EDIT_PROTECTED:
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

    # ---- Topic API ----

    def _topics_path(self) -> Path:
        return self.root / "topics.json"

    def _load_topics(self) -> list[dict[str, Any]]:
        p = self._topics_path()
        if not p.is_file():
            return []
        topics = list(json.loads(p.read_text(encoding="utf-8")).get("topics", []))
        for topic in topics:
            topic["team"] = _normalize_team(topic.get("team"))
        return topics

    def _save_topics(self, topics: list[dict[str, Any]]) -> None:
        self._topics_path().write_text(
            json.dumps({"topics": topics}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def create_topic(self, topic: dict[str, Any]) -> dict[str, Any]:
        topic = dict(topic)
        topic["team"] = _normalize_team(topic.get("team"))
        with self._lock:
            topics = self._load_topics()
            if any(
                t["id"] == topic["id"] and _normalize_team(t.get("team")) == topic.get("team")
                for t in topics
            ):
                return topic  # 幂等：id 重复不报错
            topics.append(topic)
            self._save_topics(topics)
        return topic

    def list_topics(self, team: str | None = None) -> list[dict[str, Any]]:
        topics = self._load_topics()
        if team is None:
            return topics
        return [topic for topic in topics if _team_matches(topic, team)]

    def list_examples(
        self,
        topic_id: str,
        label: str | None = None,
        team: str | None = None,
    ) -> list[dict[str, Any]]:
        results = []
        for card in self.load(team=team):
            if card.get("topic_id") != topic_id:
                continue
            effective_label = card.get("label_override") or card.get("label", "good")
            card["effective_label"] = effective_label
            if label is not None and effective_label != label:
                continue
            results.append(card)
        return results

    def relabel(self, card_id: str, new_label: str, override_by: str) -> dict[str, Any] | None:
        from datetime import datetime, timezone
        found = self._find_item_path(card_id)
        if not found:
            return None
        wtype, md = found
        with self._lock:
            card = self._item_to_card(wtype, md)
            if not card:
                return None
            card["label_override"] = new_label
            card["label_override_by"] = override_by
            card["label_override_at"] = datetime.now(timezone.utc).isoformat()
            self._write_card(wtype, md.stem, card)
            self._rebuild_index(wtype)
            return self._item_to_card(wtype, md)

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
