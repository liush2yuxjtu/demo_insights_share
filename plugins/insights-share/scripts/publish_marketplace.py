#!/usr/bin/env python3
"""生成 insights-share 的 marketplace 发布摘要。"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
PLUGIN_DIR = Path(__file__).resolve().parents[1]
MANIFEST = PLUGIN_DIR / ".claude-plugin" / "plugin.json"
MARKETPLACE = PLUGIN_DIR / ".claude-plugin" / "marketplace.json"
README = PLUGIN_DIR / "README.md"
MCP = PLUGIN_DIR / "mcp" / "wiki-server.json"


EXCLUDE_NAMES = {
    ".DS_Store",
    ".claude",
    ".pytest_cache",
    "__pycache__",
    "runtime-web",
}
EXCLUDE_SUFFIXES = {".pyc", ".pyo"}


def _default_output() -> Path:
    version = _read_json(MANIFEST)["version"]
    return PLUGIN_DIR / "release" / f"plugin-marketplace-{version}.json"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _should_skip(path: Path) -> bool:
    rel = path.relative_to(PLUGIN_DIR)
    if any(part in EXCLUDE_NAMES for part in rel.parts):
        return True
    if path.suffix in EXCLUDE_SUFFIXES:
        return True
    return False


def _validate_contract() -> tuple[dict, dict]:
    manifest = _read_json(MANIFEST)
    marketplace = _read_json(MARKETPLACE)
    plugin = marketplace["plugins"][0]

    assert manifest["name"] == "insights-share", "manifest name"
    assert manifest["version"].startswith("0."), "manifest version prefix"
    assert plugin["name"] == "insights-share", "marketplace plugin name"
    plugin_version = plugin.get("version")
    if plugin_version is not None:
        assert plugin_version == manifest["version"], "marketplace version"
    plugin_source = str(plugin.get("source") or "")
    assert plugin_source in {"./", "."} or "subdir=plugins/insights-share" in plugin_source, "marketplace source"
    _known_milestones = {"M1_MVP", "M2_AGENTS", "M3_MCP_NAMESPACE_TTL", "M4_SIGN_MARKETPLACE",
                         "M5_RENAME", "M6_LATENCY_MVP", "M7_LATENCY_DEEP", "M8_LATENCY_INDEX"}
    assert manifest["milestones"]["current"] in _known_milestones, "milestone current"
    assert "M5_RENAME" in manifest["milestones"]["completed"], "m5 completed"
    assert "签名" in README.read_text(encoding="utf-8"), "readme signing"
    mcp = _read_json(MCP)
    tool_names = [tool["name"] for tool in mcp.get("tools", [])]
    assert "wiki_public_keys" in tool_names, "mcp public keys tool"
    return manifest, marketplace


def _build_bundle(manifest: dict, marketplace: dict) -> dict:
    files = []
    for path in sorted(PLUGIN_DIR.rglob("*")):
        if not path.is_file():
            continue
        if _should_skip(path):
            continue
        rel = path.relative_to(PLUGIN_DIR).as_posix()
        files.append({"path": rel, "sha256": _sha256(path)})
    return {
        "name": manifest["name"],
        "version": manifest["version"],
        "published_at": datetime.now(timezone.utc).isoformat(),
        "source": marketplace["plugins"][0]["source"],
        "checksums": files,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="只校验，不落盘")
    parser.add_argument("--output", default=str(_default_output()), help="发布摘要输出路径")
    args = parser.parse_args()

    manifest, marketplace = _validate_contract()
    if args.check:
        print("marketplace publish contract: OK")
        return 0

    output = Path(args.output).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(_build_bundle(manifest, marketplace), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
