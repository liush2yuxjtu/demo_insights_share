from __future__ import annotations

import os
import stat
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "insights-share/validation/run_adoption_proof.sh"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_adoption_proof_runner_is_executable() -> None:
    mode = os.stat(RUNNER).st_mode

    assert mode & stat.S_IXUSR


def test_adoption_proof_runner_declares_four_signals() -> None:
    script = _read(RUNNER)

    assert "clean_machine_install" in script
    assert "first_relevant_hit" in script
    assert "first_publish" in script
    assert "day_2_return" in script
    assert "adoption_proof_latest.json" in script


def test_adoption_proof_uses_isolated_home_and_current_cache_name() -> None:
    script = _read(RUNNER)

    assert 'HOME_DIR="${WORKDIR}/home"' in script
    assert 'HOME="${HOME_DIR}"' in script
    assert ".cache/insights-share" in script
    assert "insights-wiki" not in script


def test_adoption_proof_covers_publish_hit_install_and_return() -> None:
    script = _read(RUNNER)

    assert "publish seeds/alice_pgpool.json" in script
    assert "publish seeds/bob_pgpool_bad.json" in script
    assert "solve \"${PROBLEM}\" --wiki \"${WIKI_URL}\" --no-ai" in script
    assert "wiki-install --server \"${WIKI_URL}\"" in script
    assert '"${SOURCE_DIR}/insights_cli.py" solve "${PROBLEM}" --no-ai' in script
