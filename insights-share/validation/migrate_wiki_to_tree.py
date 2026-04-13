#!/usr/bin/env python3
"""一次性 ETL：把 demo_codes/seeds/*.json 迁移为 wiki_tree/ 的 4 层结构。

4 层结构（对齐 validation.md task #4）：

    {root}/wiki_types.json                 layer-1: 所有 wiki_type 的元清单
    {root}/{type}/INDEX.md                 layer-2: 该 type 下所有 item 的元表
    {root}/{type}/{item}.md                layer-3: 单个 item 的完整描述
    {root}/{type}/raw/{id}.jsonl           layer-4: 原始 seed JSON（raw log）

每个 item.md 的开头是一段 JSON frontmatter（以 --- 作为围栏），
正文按 `## Description / ## Bad example / ## Good example /
## Applies when / ## Do NOT apply when / ## Raw log` 6 节组织。
TreeInsightStore 读取时复用这 6 节。
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

# tag → wiki_type 路由规则：第一条命中即为 type
ROUTING: list[tuple[tuple[str, ...], str]] = [
    (("postgres", "pgbouncer", "connection-pool"), "database"),
    (("celery", "retry", "redis-broker"), "infra_queue"),
    (("redis", "eviction", "maxmemory", "session-store"), "infra_cache"),
]

# 人工 slug 映射（保持稳定、可读的文件名，对齐 validation.md 示例）
SLUG_MAP = {
    "alice-pgpool-2026-04-10": "postgres_pool",
    "alice-celery-retry-2026-04-08": "celery_retry_storm",
    "carol-redis-eviction-2026-03-27": "redis_lru_session_eviction",
}


def route_card(card: dict) -> str:
    tags = {str(t).lower() for t in (card.get("tags") or [])}
    for keywords, wtype in ROUTING:
        if tags & set(keywords):
            return wtype
    return "general"


def slug_of(card: dict) -> str:
    cid = card.get("id", "")
    if cid in SLUG_MAP:
        return SLUG_MAP[cid]
    return cid.replace("-", "_")


def _write_item_md(type_dir: Path, slug: str, card: dict) -> None:
    raw_rel = f"./raw/{card['id']}.jsonl"
    raw_path = type_dir / "raw" / f"{card['id']}.jsonl"
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_text(json.dumps(card, ensure_ascii=False) + "\n", encoding="utf-8")

    frontmatter = {
        "id": card["id"],
        "title": card.get("title", ""),
        "author": card.get("author", ""),
        "confidence": card.get("confidence", 0.5),
        "tags": card.get("tags") or [],
        "status": "active",
        "applies_when": card.get("applies_when") or [],
        "do_not_apply_when": card.get("do_not_apply_when") or [],
        "raw_log": raw_rel,
    }

    def bullet_list(items: list[str]) -> str:
        return "\n".join(f"- {x}" for x in items) if items else "(none)"

    parts = [
        "---",
        json.dumps(frontmatter, ensure_ascii=False, indent=2),
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
        bullet_list(card.get("applies_when") or []),
        "",
        "## Do NOT apply when",
        "",
        bullet_list(card.get("do_not_apply_when") or []),
        "",
        "## Raw log",
        "",
        f"[{raw_rel}]({raw_rel})",
        "",
    ]
    (type_dir / f"{slug}.md").write_text("\n".join(parts), encoding="utf-8")


def _write_index_md(type_dir: Path, cards_for_type: list[dict]) -> None:
    lines = [
        f"# {type_dir.name} · INDEX",
        "",
        "| name | description | trigger when | docs |",
        "|------|-------------|--------------|------|",
    ]
    for card in cards_for_type:
        slug = slug_of(card)
        description = (card.get("title") or "").replace("|", "\\|")
        trigger_when = ", ".join((card.get("tags") or [])[:4])
        docs = f"[{slug}.md](./{slug}.md)"
        lines.append(f"| {slug} | {description} | {trigger_when} | {docs} |")
    lines.append("")
    (type_dir / "INDEX.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--seeds",
        default=str(Path(__file__).resolve().parent.parent / "demo_codes" / "seeds"),
    )
    ap.add_argument(
        "--out",
        default=str(Path(__file__).resolve().parent.parent / "demo_codes" / "wiki_tree"),
    )
    args = ap.parse_args()

    seeds_dir = Path(args.seeds)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    by_type: dict[str, list[dict]] = {}
    for jf in sorted(seeds_dir.glob("*.json")):
        card = json.loads(jf.read_text(encoding="utf-8"))
        wtype = route_card(card)
        by_type.setdefault(wtype, []).append(card)

    for wtype, cards in by_type.items():
        type_dir = out_dir / wtype
        type_dir.mkdir(parents=True, exist_ok=True)
        (type_dir / "raw").mkdir(exist_ok=True)
        for card in cards:
            _write_item_md(type_dir, slug_of(card), card)
        _write_index_md(type_dir, cards)

    (out_dir / "wiki_types.json").write_text(
        json.dumps({"types": sorted(by_type.keys())}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    total = sum(len(v) for v in by_type.values())
    print(
        f"[MIGRATE OK] out={out_dir} types={sorted(by_type.keys())} cards={total}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
