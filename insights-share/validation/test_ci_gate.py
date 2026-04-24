from __future__ import annotations

import os
import stat
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "insights-share/validation/run_ci_gate.sh"
WORKFLOW = ROOT / ".github/workflows/e2e-gates.yml"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_ci_gate_runner_is_executable() -> None:
    assert os.stat(RUNNER).st_mode & stat.S_IXUSR


def test_ci_gate_runner_includes_required_gates() -> None:
    script = _read(RUNNER)

    assert "run_contract_tests.sh" in script
    assert "run_adoption_proof.sh" in script
    assert "start.demo.sh --dry-run" in script
    assert "RUN_HANDOUT_VERIFY" in script
    assert "RUN_TMUX_SMOKE" in script


def test_github_workflow_watches_product_surfaces() -> None:
    workflow = _read(WORKFLOW)

    assert "pull_request:" in workflow
    assert "push:" in workflow
    assert '"start.demo.sh"' in workflow
    assert '"plugins/insights-share/**"' in workflow
    assert '"insights-share/validation/**"' in workflow
    assert "run_ci_gate.sh" in workflow
