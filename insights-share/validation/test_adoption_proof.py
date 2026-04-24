from __future__ import annotations

import json
import os
import stat
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "insights-share/validation/run_adoption_proof.sh"
REPORT_JSON = ROOT / "insights-share/validation/reports/deliverables/adoption_proof_latest.json"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_adoption_proof_runner_is_executable() -> None:
    mode = os.stat(RUNNER).st_mode

    assert mode & stat.S_IXUSR


def test_adoption_proof_runner_declares_four_signals() -> None:
    script = _read(RUNNER)

    assert "adoption-proof/v2" in script
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


def test_adoption_proof_report_has_structured_signal_evidence() -> None:
    report = json.loads(REPORT_JSON.read_text(encoding="utf-8"))

    assert report["schema_version"] == "adoption-proof/v2"
    assert report["pass"] is True
    assert report["legacy_signals"] == {
        "clean_machine_install": "ok",
        "first_relevant_hit": "alice-pgpool-2026-04-10",
        "first_publish": "alice-pgpool-2026-04-10,bob-pgpool-bad-2026-04-12",
        "day_2_return": "ok",
    }

    signals = report["signals"]
    assert set(signals) == {
        "clean_machine_install",
        "first_relevant_hit",
        "first_publish",
        "day_2_return",
    }
    for signal in signals.values():
        assert signal["status"] == "ok"
        assert signal["started_at"].endswith("Z")
        assert signal["finished_at"].endswith("Z")
        assert isinstance(signal["duration_ms"], int)
        assert signal["duration_ms"] >= 0
        assert isinstance(signal["evidence"], dict)

    clean = signals["clean_machine_install"]["evidence"]
    assert clean["cached_card_count"] == 2
    assert clean["config_server_url"] == report["wiki_url"]
    assert clean["ephemeral_cache_dir"].endswith("/.cache/insights-share")
    assert clean["config_path"].endswith("/cache/insights-share/config.json")
    assert "adoption_proof_artifacts/latest" in clean["config_path"]

    hit = signals["first_relevant_hit"]["evidence"]
    assert hit["top_hit_id"] == "alice-pgpool-2026-04-10"
    assert hit["hit_count"] >= 1
    assert "idle_in_transaction_session_timeout" in hit["output_excerpt"]

    publish = signals["first_publish"]["evidence"]
    assert publish["published_card_ids"] == [
        "alice-pgpool-2026-04-10",
        "bob-pgpool-bad-2026-04-12",
    ]
    assert publish["topic_example_count"] == 2
    assert publish["good_example_count"] == 1
    assert publish["bad_example_count"] == 1
    assert publish["paths"]["alice-pgpool-2026-04-10"]["card_md"].endswith(".md")
    assert publish["paths"]["bob-pgpool-bad-2026-04-12"]["raw_log"].endswith(".txt")

    day2 = signals["day_2_return"]["evidence"]
    assert day2["used_installed_config"] is True
    assert day2["config_server_url"] == report["wiki_url"]
    assert "hot-loaded alice-pgpool-2026-04-10" in day2["output_excerpt"]


def test_adoption_proof_artifacts_do_not_persist_private_keys() -> None:
    report = json.loads(REPORT_JSON.read_text(encoding="utf-8"))
    artifact_dir = Path(report["artifacts"]["dir"])

    persisted_files = [path.name for path in artifact_dir.rglob("*") if path.is_file()]
    assert not any("private" in name.lower() for name in persisted_files)
    assert not any(name.endswith(".pem") for name in persisted_files)
