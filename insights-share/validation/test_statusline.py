from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STATUSLINE = ROOT / "plugin" / "statusline" / "insights_wiki_statusline.sh"
ROOT_STATUSLINE = ROOT.parents[0] / "statusline" / "insights_wiki_statusline.sh"


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _run_statusline(home: Path, *, ttl_seconds: int = 86400) -> str:
    env = os.environ.copy()
    env["HOME"] = str(home)
    env["WIKI_STATUSLINE_NO_COLOR"] = "1"
    env["WIKI_STATUSLINE_STALE_TTL_SECONDS"] = str(ttl_seconds)
    completed = subprocess.run(
        ["bash", str(STATUSLINE)],
        cwd=ROOT.parents[1],
        capture_output=True,
        text=True,
        check=True,
        env=env,
    )
    return completed.stdout.strip()


def test_root_and_plugin_statusline_scripts_stay_identical() -> None:
    assert STATUSLINE.read_text(encoding="utf-8") == ROOT_STATUSLINE.read_text(encoding="utf-8")


def test_statusline_shows_green_badge_when_cache_is_fresh(tmp_path: Path) -> None:
    home = tmp_path / "home"
    (home / ".claude" / "skills" / "insights-wiki").mkdir(parents=True)
    (home / ".claude" / "skills" / "insights-wiki" / "SKILL.md").write_text("ok", encoding="utf-8")
    cache_dir = home / ".cache" / "insights-wiki"
    cache_dir.mkdir(parents=True)
    (cache_dir / ".health_cache").write_text("ok", encoding="utf-8")
    _write_json(
        cache_dir / "today_count.json",
        {
            "date": datetime.now().date().isoformat(),
            "count": 4,
            "last_card_id": "alpha-pool-card",
            "last_trigger_at": datetime.now().astimezone().strftime("%Y-%m-%dT%H:%M:%S%z"),
        },
    )
    _write_json(
        cache_dir / "manifest.json",
        {
            "last_sync_at": datetime.now().astimezone().strftime("%Y-%m-%dT%H:%M:%S%z"),
            "cards": ["alpha-pool-card"],
        },
    )

    assert _run_statusline(home) == "[wiki ✓ 4/today]"


def test_statusline_shows_stale_badge_when_manifest_is_expired(tmp_path: Path) -> None:
    home = tmp_path / "home"
    (home / ".claude" / "skills" / "insights-wiki").mkdir(parents=True)
    (home / ".claude" / "skills" / "insights-wiki" / "SKILL.md").write_text("ok", encoding="utf-8")
    cache_dir = home / ".cache" / "insights-wiki"
    cache_dir.mkdir(parents=True)
    (cache_dir / ".health_cache").write_text("ok", encoding="utf-8")
    _write_json(
        cache_dir / "today_count.json",
        {
            "date": datetime.now().date().isoformat(),
            "count": 2,
            "last_card_id": "alpha-pool-card",
            "last_trigger_at": datetime.now().astimezone().strftime("%Y-%m-%dT%H:%M:%S%z"),
        },
    )
    _write_json(
        cache_dir / "manifest.json",
        {
            "last_sync_at": (datetime.now().astimezone() - timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%S%z"),
            "cards": ["alpha-pool-card"],
        },
    )

    assert _run_statusline(home, ttl_seconds=60) == "[wiki ⚠ stale]"


def test_statusline_shows_sig_fail_badge_when_manifest_records_signature_failure(tmp_path: Path) -> None:
    home = tmp_path / "home"
    (home / ".claude" / "skills" / "insights-wiki").mkdir(parents=True)
    (home / ".claude" / "skills" / "insights-wiki" / "SKILL.md").write_text("ok", encoding="utf-8")
    cache_dir = home / ".cache" / "insights-wiki"
    cache_dir.mkdir(parents=True)
    (cache_dir / ".health_cache").write_text("ok", encoding="utf-8")
    _write_json(
        cache_dir / "today_count.json",
        {
            "date": datetime.now().date().isoformat(),
            "count": 1,
            "last_card_id": "tampered-card",
            "last_trigger_at": datetime.now().astimezone().strftime("%Y-%m-%dT%H:%M:%S%z"),
        },
    )
    _write_json(
        cache_dir / "manifest.json",
        {
            "last_sync_at": datetime.now().astimezone().strftime("%Y-%m-%dT%H:%M:%S%z"),
            "cards": ["tampered-card"],
            "signature": {
                "failures": ["tampered-card"],
                "last_status": "invalid",
            },
        },
    )

    assert _run_statusline(home) == "[wiki 🔒 sig-fail]"
