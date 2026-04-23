from __future__ import annotations

from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[2]
START_DEMO = ROOT / "start.demo.sh"
START_CLAUDE = ROOT / "start.claude.sh"
START_CODEX = ROOT / "start.codex.sh"
START_DRIVER = ROOT / "insights-share/validation/start_demo_driver.sh"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _run_dry(script: Path) -> str:
    completed = subprocess.run(
        ["bash", str(script), "--dry-run"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout


def test_start_scripts_exist_and_are_shell_scripts() -> None:
    assert START_DEMO.is_file()
    assert START_CLAUDE.is_file()
    assert START_CODEX.is_file()
    assert START_DRIVER.is_file()
    assert _read(START_DEMO).startswith("#!/usr/bin/env bash")
    assert _read(START_CLAUDE).startswith("#!/usr/bin/env bash")
    assert _read(START_CODEX).startswith("#!/usr/bin/env bash")
    assert _read(START_DRIVER).startswith("#!/usr/bin/env bash")


def test_start_demo_script_surfaces_plugin_m5_checks() -> None:
    script = _read(START_DEMO)

    assert 'plugins/insights-share/statusline/insights_share_statusline.sh' in script
    assert 'plugin M5 self-check' in script
    assert 'claude plugin install "${PLUGIN_NAME}@${PLUGIN_NAME}"' in script
    assert "sandbox 内已完成真实 plugin install" in script


def test_start_claude_script_wraps_shared_driver() -> None:
    script = _read(START_CLAUDE)

    assert 'START_PROVIDER="claude"' in script
    assert 'source "$(cd "$(dirname "$0")" && pwd)/insights-share/validation/start_demo_driver.sh"' in script
    assert 'main "$@"' in script
    assert "main_loop" in script


def test_start_codex_script_wraps_shared_driver() -> None:
    script = _read(START_CODEX)

    assert 'START_PROVIDER="codex"' in script
    assert 'source "$(cd "$(dirname "$0")" && pwd)/insights-share/validation/start_demo_driver.sh"' in script
    assert 'main "$@"' in script
    assert "main_loop" in script


def test_shared_start_driver_contains_real_demo_flow() -> None:
    script = _read(START_DRIVER)

    assert 'LOG_FILE="${LOG_DIR}/start_${START_PROVIDER}.latest.txt"' in script
    assert 'PORT="${PORT:-17821}"' in script
    assert 'WORKDIR="$(mktemp -d "/tmp/start-${START_PROVIDER}.XXXXXX")"' in script
    assert 'rsync -a \\' in script
    assert '"${SOURCE_DIR}/" "${RUN_DIR}/"' in script
    assert "--exclude '.venv'" in script
    assert 'insights_cli.py serve --host 127.0.0.1 --port ${PORT}' in script
    assert "./runtime-start/wiki_tree" in script
    assert "publish seeds/alice_pgpool.json" in script
    assert "publish seeds/bob_pgpool_bad.json" in script
    assert "Our checkout API is timing out, postgres is rejecting new connections during the lunch spike" in script
    assert "wiki-install --server" in script
    assert "cleanup() {" in script


def test_start_scripts_support_dry_run() -> None:
    claude_out = _run_dry(START_CLAUDE)
    codex_out = _run_dry(START_CODEX)

    assert "DRY RUN" in claude_out
    assert "DRY RUN" in codex_out
    assert "start_claude.latest.txt" in claude_out
    assert "start_codex.latest.txt" in codex_out
    assert "provider=claude" in claude_out
    assert "provider=codex" in codex_out
    assert "隔离目录=/tmp/start-claude.XXXXXX/demo_codes" in claude_out
    assert "隔离目录=/tmp/start-codex.XXXXXX/demo_codes" in codex_out
    assert "固定步骤数=10" in claude_out
    assert "固定步骤数=10" in codex_out
