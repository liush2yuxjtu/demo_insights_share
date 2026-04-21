from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN_DIR = ROOT / "plugin"
MANIFEST = PLUGIN_DIR / ".claude-plugin" / "plugin.json"
MARKETPLACE = PLUGIN_DIR / ".claude-plugin" / "marketplace.json"
README = PLUGIN_DIR / "README.md"
SELF_CHECK = PLUGIN_DIR / "scripts" / "self_check.sh"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_plugin_manifest_declares_m2_command_set() -> None:
    manifest = json.loads(_read(MANIFEST))
    commands = manifest["entry"]["commands"]

    assert commands == [
        "commands/wiki-install.md",
        "commands/wiki-search.md",
        "commands/wiki-publish.md",
        "commands/wiki-review.md",
        "commands/wiki-diff.md",
    ]
    assert len(manifest["entry"]["agents"]) == 2


def test_wiki_diff_command_exists() -> None:
    command = PLUGIN_DIR / "commands" / "wiki-diff.md"

    assert command.is_file()
    text = _read(command)
    assert "不合并、不挑最优、不做冲突检测" in text
    assert "只写 diff" in text


def test_self_check_tracks_full_m2_contract() -> None:
    script = _read(SELF_CHECK)

    assert "wiki-diff" in script
    assert "commands=5" in script


def test_marketplace_and_readme_align_with_current_m2_release() -> None:
    manifest = json.loads(_read(MANIFEST))
    marketplace = json.loads(_read(MARKETPLACE))
    readme = _read(README)

    plugin = marketplace["plugins"][0]
    assert plugin["version"] == manifest["version"] == "0.2.0-m2"
    assert manifest["milestones"]["current"] == "M3_MCP_NAMESPACE_TTL"
    assert "M2_AGENTS" in readme
    assert "/wiki-diff" in readme
