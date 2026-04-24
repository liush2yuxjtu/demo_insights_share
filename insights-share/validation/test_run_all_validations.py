from __future__ import annotations

import json
import os
import stat
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "insights-share/validation/run_all_validations.sh"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_run_all_validations_runner_is_executable_and_portable() -> None:
    script = _read(RUNNER)

    assert os.stat(RUNNER).st_mode & stat.S_IXUSR
    assert "/Users/m1" not in script
    assert 'SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"' in script
    assert 'REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"' in script
    assert "VALIDATION_REPORTS_DIR" in script


def test_run_all_validations_declares_current_gate_surface() -> None:
    script = _read(RUNNER)

    for gate in ("P0", "P1", "P2", "P3", "P6", "P7", "AP-1"):
        assert f'gate_id="{gate}"' in script or f'"id": "{gate}"' in script

    assert "run_contract_tests.sh" in script
    assert "run_adoption_proof.sh" in script
    assert "start.demo.sh" in script
    assert "handout:record" not in script
    assert "handout:verify" not in script
    assert "run_start_tmux_smoke.sh" in script
    assert "final_report.html" in script
    assert "final_summary.json" in script


def test_run_all_validations_generates_temp_report_without_rewriting_artifacts(tmp_path: Path) -> None:
    env = os.environ.copy()
    env.update(
        {
            "VALIDATION_REPORTS_DIR": str(tmp_path),
            "RUN_CONTRACT_TESTS": "0",
            "RUN_ADOPTION_PROOF": "0",
            "RUN_START_DEMO_DRY": "0",
            "RUN_START_DEMO_LIVE": "0",
            "RUN_TMUX_SMOKE": "0",
            "RUN_OPEN_REPORT": "0",
        }
    )

    proc = subprocess.run(
        ["bash", str(RUNNER)],
        cwd=ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=60,
    )

    assert proc.returncode == 0, proc.stdout

    summary_path = tmp_path / "final_summary.json"
    html_path = tmp_path / "final_report.html"
    assert summary_path.is_file()
    assert html_path.is_file()

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["schema_version"] == "validation-aggregate/v2"
    assert summary["repo_root"] == str(ROOT)
    assert summary["all_pass"] is True

    gates = {gate["id"]: gate for gate in summary["gates"]}
    assert gates["P0"]["status"] == "PASS"
    assert gates["P3"]["status"] == "SKIP"
    assert gates["AP-1"]["status"] == "SKIP"
    assert gates["P7"]["status"] == "PASS"

    html = html_path.read_text(encoding="utf-8")
    assert "/Users/m1" not in html
    assert "默认 E2E" in html
    assert "AP-1 adoption proof" in html
