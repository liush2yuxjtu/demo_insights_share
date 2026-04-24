from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[0]
PLUGIN_DIR = REPO_ROOT / "plugins" / "insights-share"
DEMO_CODES = REPO_ROOT / "insights-share" / "demo_codes"
MANIFEST = PLUGIN_DIR / ".claude-plugin" / "plugin.json"
MARKETPLACE = PLUGIN_DIR / ".claude-plugin" / "marketplace.json"
README = PLUGIN_DIR / "README.md"
SELF_CHECK = PLUGIN_DIR / "scripts" / "self_check.sh"
MCP = PLUGIN_DIR / "mcp" / "wiki-server.json"
PUBLISH_SCRIPT = PLUGIN_DIR / "scripts" / "publish_marketplace.py"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_plugin_manifest_declares_current_release() -> None:
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
    assert manifest["version"] == "0.6.0-m7"
    assert manifest["milestones"]["current"] == "M7_LATENCY_DEEP"
    assert "M5_RENAME" in manifest["milestones"]["completed"]
    assert manifest["milestones"]["pending"] == ["M8_LATENCY_INDEX"]


def test_share_diff_command_exists() -> None:
    command = PLUGIN_DIR / "commands" / "share-diff.md"

    assert command.is_file()
    text = _read(command)
    assert "不合并、不挑最优、不做冲突检测" in text
    assert "只写 diff" in text


def test_self_check_tracks_bundle_local_contract() -> None:
    script = _read(SELF_CHECK)

    assert "share-diff" in script
    assert "mcp wiki-server" in script
    assert "marketplace publish script" in script
    assert "insights_share_statusline.sh" in script
    assert "insights_prefetch.py" in script
    assert "session_start_full_fetch.py" in script
    assert 'm["name"] == "insights-share"' in script
    assert 'm["version"].startswith("0.")' in script
    assert 'current in known' in script


def test_mcp_contract_exists_and_covers_team_queries() -> None:
    payload = json.loads(_read(MCP))

    assert payload["name"] == "wiki-server"
    assert payload["transport"]["base_url"] == "http://192.168.22.42:7821"
    tool_names = [tool["name"] for tool in payload["tools"]]
    assert "wiki_search" in tool_names
    assert "wiki_topics" in tool_names
    assert "wiki_examples" in tool_names
    assert "wiki_public_keys" in tool_names
    wiki_search = next(tool for tool in payload["tools"] if tool["name"] == "wiki_search")
    assert "team" in wiki_search["request"]["query"]
    assert payload["capabilities"]["signed_cards"] is True


def test_marketplace_and_readme_align_with_current_release() -> None:
    manifest = json.loads(_read(MANIFEST))
    marketplace = json.loads(_read(MARKETPLACE))
    readme = _read(README)

    plugin = marketplace["plugins"][0]
    assert marketplace["name"] == "insights-share"
    assert plugin["name"] == "insights-share"
    assert plugin["version"] == manifest["version"] == "0.6.0-m7"
    assert plugin["source"] == "./"
    assert manifest["milestones"]["current"] == "M7_LATENCY_DEEP"
    assert "M7_LATENCY_DEEP" in readme
    assert "v0.6.0-m7" in readme
    assert "/share-diff" in readme
    assert "[share ⚠ stale]" in readme
    assert "[share 🔒 sig-fail]" in readme
    assert "team namespace" in readme
    assert "publish_marketplace.py" in readme


def test_publish_marketplace_script_exists() -> None:
    assert PUBLISH_SCRIPT.is_file()
    assert "--check" in _read(PUBLISH_SCRIPT)


def test_bundle_cache_persist_sanitizes_sensitive_fields(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    module = _load_module(PLUGIN_DIR / "scripts" / "insights_cache.py", "plugin_insights_cache_test")

    saved_path = module.persist(
        {
            "id": "cache-card-1",
            "title": "Postgres Pool Exhaustion",
            "author": "alice",
            "wiki_type": "database",
            "tags": ["postgres"],
            "raw_log": "./raw/cache-card-1.jsonl",
            "label_note": "internal only",
            "description": "should not leak into cache",
            "signature_status": "verified",
        }
    )

    saved = json.loads(Path(saved_path).read_text(encoding="utf-8"))
    assert saved["id"] == "cache-card-1"
    assert saved["title"] == "Postgres Pool Exhaustion"
    assert saved["signature_status"] == "verified"
    assert "raw_log" not in saved
    assert "label_note" not in saved
    assert "description" not in saved


def test_prefetch_additional_context_uses_public_card_allowlist() -> None:
    module = _load_module(DEMO_CODES / "hooks" / "insights_prefetch.py", "prefetch_contract_test")

    additional = module._build_context(
        "postgres token",
        [
            {
                "id": "safe-card-1",
                "title": "Postgres Pool",
                "author": "alice",
                "tags": ["postgres"],
                "raw_log": "./raw/safe-card-1.jsonl",
                "raw_log_export_content": "sk-liveSECRET1234567890",
                "description": "Bearer abcdefghijklmnopqrstuvwxyz",
                "fix": "do not leak this field",
            }
        ],
    )

    assert "safe-card-1" in additional
    assert "Postgres Pool" in additional
    assert "alice" in additional
    assert "raw_log" not in additional
    assert "sk-liveSECRET1234567890" not in additional
    assert "Bearer abcdefghijklmnopqrstuvwxyz" not in additional
    assert "do not leak this field" not in additional
