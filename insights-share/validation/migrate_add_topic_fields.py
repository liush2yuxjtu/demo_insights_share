#!/usr/bin/env python3
"""
迁移脚本：为 wiki_tree/<type>/*.md 添加缺失的 topic_id/label/raw_log_type 字段。

遍历 insights-share/demo_codes/wiki_tree/<type>/*.md，给缺失字段补默认值：
- topic_id = slug.replace("_","-")
- label = "good"
- raw_log_type = "jsonl"
- raw_log = f"./raw/{card_id}.jsonl"

读取每个 .md 文件的 frontmatter，如果缺失新字段则补充，写回 .md 文件。
不动 raw/ 目录下已有文件。
"""

import re
import sys
from pathlib import Path

WIKI_TREE = Path(__file__).parent.parent / "demo_codes" / "wiki_tree"


def slug_from_filename(fname: str) -> str:
    """从文件名生成 slug：去掉 .md 后缀，下划线转横线"""
    return fname.replace(".md", "").replace("_", "-")


def patch_frontmatter(content: str) -> tuple[str, bool]:
    """
    解析 markdown frontmatter，补充缺失字段。
    返回 (new_content, modified) 元组。
    """
    # 匹配 YAML frontmatter
    fm_match = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
    if not fm_match:
        return content, False

    fm_text = fm_match.group(1)
    lines = fm_text.splitlines()
    original_lines = lines[:]

    # 解析已有字段
    existing = {}
    for line in lines:
        m = re.match(r"^(\w+):\s*(.*)$", line)
        if m:
            existing[m.group(1)] = m.group(2).strip()

    modified = False

    # 从文件名推导默认值（使用 content 中的 id 或从文件名猜）
    # 这里 frontmatter 里已有 id 字段，直接用即可
    card_id = existing.get("id", "")
    slug = slug_from_filename(card_id) if card_id else ""

    defaults = {
        "topic_id": slug.replace("_", "-") if slug else "",
        "label": "good",
        "raw_log_type": "jsonl",
        "raw_log": f"./raw/{card_id}.jsonl" if card_id else "",
    }

    for field, default_val in defaults.items():
        if field not in existing:
            lines.append(f"{field}: {default_val}")
            modified = True

    if not modified:
        return content, False

    new_fm_text = "\n".join(lines)
    new_content = content.replace(fm_match.group(0), f"---\n{new_fm_text}\n---\n", 1)
    return new_content, True


def main():
    types = ["database", "queue", "cache", "messaging", "search", "monitoring"]
    total_modified = 0

    for wtype in types:
        type_dir = WIKI_TREE / wtype
        if not type_dir.is_dir():
            continue

        for md_file in sorted(type_dir.glob("*.md")):
            content = md_file.read_text(encoding="utf-8")
            new_content, modified = patch_frontmatter(content)
            if modified:
                md_file.write_text(new_content, encoding="utf-8")
                print(f"PATCHED: {md_file.relative_to(WIKI_TREE.parent.parent)}")
                total_modified += 1

    print(f"\n总计修改 {total_modified} 个文件")
    return 0


if __name__ == "__main__":
    sys.exit(main())
