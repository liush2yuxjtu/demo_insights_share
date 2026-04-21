from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[0]
PLUGIN_DIR = REPO_ROOT / "plugins" / "insights-share"
MANIFEST = PLUGIN_DIR / ".claude-plugin" / "plugin.json"
MARKETPLACE = PLUGIN_DIR / ".claude-plugin" / "marketplace.json"
README = PLUGIN_DIR / "README.md"
SELF_CHECK = PLUGIN_DIR / "scripts" / "self_check.sh"
MCP = PLUGIN_DIR / "mcp" / "wiki-server.json"
PUBLISH_SCRIPT = PLUGIN_DIR / "scripts" / "publish_marketplace.py"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_plugin_manifest_declares_m5_release() -> None:
    manifest = json.loads(_read(MANIFEST))
    commands = manifest["entry"]["commands"]

    assert manifest["name"] == "insights-share"
    assert commands == [
        "commands/share-install.md",
        "commands/share-search.md",
        "commands/share-publish.md",
        "commands/share-review.md",
        "commands/share-diff.md",
    ]
    assert manifest["entry"]["agents"] == [
        "agents/share-curator.md",
        "agents/share-validator.md",
    ]
    assert manifest["entry"]["statusline"] == "statusline/insights_share_statusline.sh"
    assert manifest["entry"]["skills"] == [
        "skills/insights-share/SKILL.md",
        "skills/insights-share-server/SKILL.md",
    ]
    assert manifest["version"] == "0.5.0-m5"
    assert manifest["milestones"]["current"] == "M5_RENAME"
    assert "M5_RENAME" in manifest["milestones"]["completed"]
    assert manifest["milestones"]["pending"] == []


def test_share_diff_command_exists() -> None:
    command = PLUGIN_DIR / "commands" / "share-diff.md"

    assert command.is_file()
    text = _read(command)
    assert "不合并、不挑最优、不做冲突检测" in text
    assert "只写 diff" in text


def test_self_check_tracks_full_m5_contract() -> None:
    script = _read(SELF_CHECK)

    assert "share-diff" in script
    assert "mcp wiki-server" in script
    assert "marketplace publish script" in script
    assert "insights_share_statusline.sh" in script
    assert 'm["name"] == "insights-share"' in script
    assert 'm["version"] == "0.5.0-m5"' in script
    assert 'm["milestones"]["current"] == "M5_RENAME"' in script


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


def test_marketplace_and_readme_align_with_current_m5_release() -> None:
    manifest = json.loads(_read(MANIFEST))
    marketplace = json.loads(_read(MARKETPLACE))
    readme = _read(README)

    plugin = marketplace["plugins"][0]
    assert marketplace["name"] == "insights-share"
    assert plugin["name"] == "insights-share"
    assert plugin["version"] == manifest["version"] == "0.5.0-m5"
    assert "subdir=plugins/insights-share" in plugin["source"]
    assert manifest["milestones"]["current"] == "M5_RENAME"
    assert "M5_RENAME" in readme
    assert "/share-diff" in readme
    assert "[share ⚠ stale]" in readme
    assert "[share 🔒 sig-fail]" in readme
    assert "team namespace" in readme
    assert "publish_marketplace.py" in readme


def test_publish_marketplace_script_exists() -> None:
    assert PUBLISH_SCRIPT.is_file()
    assert "--check" in _read(PUBLISH_SCRIPT)
