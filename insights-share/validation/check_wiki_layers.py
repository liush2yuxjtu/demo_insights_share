#!/usr/bin/env python3
"""静态校验 wiki_tree 4 层结构完整性。

验证每一层都存在，并且跨层的引用（INDEX.md 指向 item.md、item.md
frontmatter 的 raw_log 指向 raw/*.jsonl）都能 resolve。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("root", help="wiki_tree 根目录")
    ap.add_argument(
        "--report",
        default=None,
        help="JSON 报告输出路径（默认仅打印到 stdout）",
    )
    args = ap.parse_args()

    root = Path(args.root)
    report: dict = {"root": str(root), "checks": [], "pass": True}

    def check(name: str, cond: bool, detail: str = "") -> None:
        report["checks"].append({"name": name, "pass": bool(cond), "detail": detail})
        if not cond:
            report["pass"] = False

    types_file = root / "wiki_types.json"
    check("layer1_wiki_types_json", types_file.is_file(), str(types_file))
    if not types_file.is_file():
        return _finish(report, args)

    meta = json.loads(types_file.read_text(encoding="utf-8"))
    types = list(meta.get("types") or [])
    check("layer1_has_types", len(types) > 0, f"types={types}")

    item_pattern = re.compile(r"\[([^\]]+\.md)\]\(\./([^\)]+\.md)\)")

    for wtype in types:
        tdir = root / wtype
        check(f"layer2_{wtype}_dir", tdir.is_dir(), str(tdir))
        index_md = tdir / "INDEX.md"
        check(f"layer2_{wtype}_INDEX_md", index_md.is_file(), str(index_md))
        if not index_md.is_file():
            continue

        index_text = index_md.read_text(encoding="utf-8")
        item_links = item_pattern.findall(index_text)
        check(
            f"layer2_{wtype}_index_has_items",
            len(item_links) > 0,
            f"items={[lp for _, lp in item_links]}",
        )

        for _, link_path in item_links:
            item_md = tdir / link_path
            check(
                f"layer3_{wtype}_{link_path}",
                item_md.is_file(),
                f"resolves from INDEX → {item_md}",
            )
            if not item_md.is_file():
                continue

            text = item_md.read_text(encoding="utf-8")
            if text.startswith("---\n"):
                end = text.find("\n---\n", 4)
                if end > 0:
                    try:
                        fm = json.loads(text[4:end])
                    except json.JSONDecodeError as exc:
                        check(
                            f"layer3_{wtype}_{link_path}_frontmatter",
                            False,
                            f"json decode: {exc}",
                        )
                        continue
                    check(
                        f"layer3_{wtype}_{link_path}_frontmatter",
                        bool(fm.get("id")),
                        f"id={fm.get('id')}",
                    )
                    raw_log_rel = fm.get("raw_log")
                    if raw_log_rel:
                        raw_path = (tdir / raw_log_rel).resolve()
                        check(
                            f"layer4_{wtype}_{link_path}_raw_log",
                            raw_path.is_file(),
                            f"{raw_path}",
                        )
                else:
                    check(
                        f"layer3_{wtype}_{link_path}_frontmatter",
                        False,
                        "no closing --- fence",
                    )
            else:
                check(
                    f"layer3_{wtype}_{link_path}_frontmatter",
                    False,
                    "no leading --- fence",
                )

    return _finish(report, args)


def _finish(report: dict, args: argparse.Namespace) -> int:
    if args.report:
        out = Path(args.report)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    total = len(report["checks"])
    passed = sum(1 for c in report["checks"] if c["pass"])
    verdict = "PASS" if report["pass"] else "FAIL"
    print(f"[WIKI_LAYERS] {passed}/{total} checks {verdict}")
    for c in report["checks"]:
        mark = "OK" if c["pass"] else "XX"
        print(f"  [{mark}] {c['name']}  {c['detail']}")
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
