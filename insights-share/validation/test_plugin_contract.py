from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN_DIR = ROOT / "plugin"
MANIFEST = PLUGIN_DIR / ".claude-plugin" / "plugin.json"
MARKETPLACE = PLUGIN_DIR / ".claude-plugin" / "marketplace.json"
README = PLUGIN_DIR / "README.md"
SELF_CHECK = PLUGIN_DIR / "scripts" / "self_check.sh"
MCP = PLUGIN_DIR / "mcp" / "wiki-server.json"
PUBLISH_SCRIPT = PLUGIN_DIR / "scripts" / "publish_marketplace.py"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_plugin_manifest_declares_m4_release() -> None:
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
    assert manifest["version"] == "0.4.0-m4"
    assert manifest["milestones"]["current"] == "M4_SIGN_MARKETPLACE"
    assert "M4_SIGN_MARKETPLACE" in manifest["milestones"]["completed"]
    assert manifest["milestones"]["pending"] == []


def test_wiki_diff_command_exists() -> None:
    command = PLUGIN_DIR / "commands" / "wiki-diff.md"

    assert command.is_file()
    text = _read(command)
    assert "不合并、不挑最优、不做冲突检测" in text
    assert "只写 diff" in text


def test_self_check_tracks_full_m4_contract() -> None:
    script = _read(SELF_CHECK)

    assert "wiki-diff" in script
    assert "mcp wiki-server" in script
    assert "marketplace publish script" in script
    assert "commands=5, mcp>=7" in script


def test_mcp_contract_exists_and_covers_team_queries() -> None:
    payload = json.loads(_read(MCP))

    assert payload["name"] == "wiki-server"
    assert payload["transport"]["base_url"] == "http://127.0.0.1:7821"
    tool_names = [tool["name"] for tool in payload["tools"]]
    assert "wiki_search" in tool_names
    assert "wiki_topics" in tool_names
    assert "wiki_examples" in tool_names
    assert "wiki_public_keys" in tool_names
    wiki_search = next(tool for tool in payload["tools"] if tool["name"] == "wiki_search")
    assert "team" in wiki_search["request"]["query"]
    assert payload["capabilities"]["signed_cards"] is True


def test_marketplace_and_readme_align_with_current_m4_release() -> None:
    manifest = json.loads(_read(MANIFEST))
    marketplace = json.loads(_read(MARKETPLACE))
    readme = _read(README)

    plugin = marketplace["plugins"][0]
    assert plugin["version"] == manifest["version"] == "0.4.0-m4"
    assert manifest["milestones"]["current"] == "M4_SIGN_MARKETPLACE"
    assert "M4_SIGN_MARKETPLACE" in readme
    assert "/wiki-diff" in readme
    assert "[wiki ⚠ stale]" in readme
    assert "[wiki 🔒 sig-fail]" in readme
    assert "team namespace" in readme
    assert "publish_marketplace.py" in readme


def test_publish_marketplace_script_exists() -> None:
    assert PUBLISH_SCRIPT.is_file()
    assert "--check" in _read(PUBLISH_SCRIPT)
