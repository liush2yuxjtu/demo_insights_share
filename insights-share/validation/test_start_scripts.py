from __future__ import annotations

from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[2]
START_CLAUDE = ROOT / "start.claude.sh"
START_CODEX = ROOT / "start.codex.sh"


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
    assert START_CLAUDE.is_file()
    assert START_CODEX.is_file()
    assert _read(START_CLAUDE).startswith("#!/usr/bin/env bash")
    assert _read(START_CODEX).startswith("#!/usr/bin/env bash")


def test_start_claude_script_uses_real_claude_p_flow() -> None:
    script = _read(START_CLAUDE)

    assert 'LOG_FILE="${LOG_DIR}/start_claude.latest.txt"' in script
    assert 'PORT="${PORT:-17821}"' in script
    assert 'mktemp -d "/tmp/start-claude.XXXXXX"' in script
    assert 'rsync -a \\' in script
    assert '"${SOURCE_DIR}/" "${WORKDIR}/demo_codes/"' in script
    assert "--exclude '.venv'" in script
    assert 'source "${ENV_FILE}"' in script
    assert "printf '%s\\n' \"${PROMPT}\" | claude -p \\" in script
    assert '--permission-mode bypassPermissions \\' in script
    assert 'insights_cli.py serve --host 127.0.0.1 --port ${PORT} --store ./wiki_tree --store-mode tree' in script
    assert 'insights_cli.py publish seeds/alice_pgpool.json' in script
    assert 'insights_cli.py publish seeds/bob_pgpool_bad.json' in script
    assert 'insights_cli.py solve "Our checkout API is timing out, postgres is rejecting new connections during the lunch spike" --wiki "http://127.0.0.1:${PORT}" --no-ai' in script
    assert 'insights_cli.py wiki-install --server "http://127.0.0.1:${PORT}"' in script
    assert 'cleanup() {' in script


def test_start_codex_script_uses_real_codex_exec_flow() -> None:
    script = _read(START_CODEX)

    assert 'LOG_FILE="${LOG_DIR}/start_codex.latest.txt"' in script
    assert 'PORT="${PORT:-17821}"' in script
    assert 'mktemp -d "/tmp/start-codex.XXXXXX"' in script
    assert 'rsync -a \\' in script
    assert '"${SOURCE_DIR}/" "${WORKDIR}/demo_codes/"' in script
    assert "--exclude '.venv'" in script
    assert 'source "${ENV_FILE}"' in script
    assert "printf '%s\\n' \"${PROMPT}\" | codex --dangerously-bypass-approvals-and-sandbox exec \\" in script
    assert '-C "${RUN_DIR}" \\' in script
    assert 'insights_cli.py serve --host 127.0.0.1 --port ${PORT} --store ./wiki_tree --store-mode tree' in script
    assert 'insights_cli.py publish seeds/alice_pgpool.json' in script
    assert 'insights_cli.py publish seeds/bob_pgpool_bad.json' in script
    assert 'insights_cli.py solve "Our checkout API is timing out, postgres is rejecting new connections during the lunch spike" --wiki "http://127.0.0.1:${PORT}" --no-ai' in script
    assert 'insights_cli.py wiki-install --server "http://127.0.0.1:${PORT}"' in script
    assert 'cleanup() {' in script


def test_start_scripts_support_dry_run() -> None:
    claude_out = _run_dry(START_CLAUDE)
    codex_out = _run_dry(START_CODEX)

    assert "DRY RUN" in claude_out
    assert "DRY RUN" in codex_out
    assert "start_claude.latest.txt" in claude_out
    assert "start_codex.latest.txt" in codex_out
    assert "serve --host 127.0.0.1 --port 17821 --store ./wiki_tree --store-mode tree" in claude_out
    assert "serve --host 127.0.0.1 --port 17821 --store ./wiki_tree --store-mode tree" in codex_out
    assert "publish seeds/alice_pgpool.json" in claude_out
    assert "publish seeds/alice_pgpool.json" in codex_out
    assert "wiki-install --server http://127.0.0.1:17821" in claude_out
    assert "wiki-install --server http://127.0.0.1:17821" in codex_out
    assert "claude -p" in claude_out
    assert "codex --dangerously-bypass-approvals-and-sandbox exec" in codex_out
