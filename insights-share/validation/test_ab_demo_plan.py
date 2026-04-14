from __future__ import annotations

import html
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
INDEX_HTML = ROOT / "examples/index.html"
WITHOUT_REPRODUCE = ROOT / "insights-share/validation/without_reproduce.sh"
WITHOUT_ONELINE = ROOT / "insights-share/validation/without_oneline.sh"
WITH_REPRODUCE = ROOT / "insights-share/validation/with_reproduce.sh"
WITH_ONELINE = ROOT / "insights-share/validation/with_oneline.sh"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _extract_story_text(page: str, role: str) -> str:
    match = re.search(
        rf'<div id="story-{role}" class="story-box"(?: style="display:none;")?>(.*?)</div>',
        page,
        re.S,
    )
    assert match, f"missing story block for {role}"
    visible = re.sub(r"<[^>]+>", "", match.group(1))
    return "".join(html.unescape(visible).split())


def test_story_tabs_exist_and_backend_is_default() -> None:
    page = _read(INDEX_HTML)

    assert 'onclick="showStory(\'frontend\')"' in page
    assert 'onclick="showStory(\'backend\')"' in page
    assert 'onclick="showStory(\'dl\')"' in page
    assert 'onclick="showStory(\'noob\')"' in page
    assert 'class="story-tab active" data-role="backend"' in page
    assert 'id="story-backend" class="story-box"' in page
    assert 'id="story-frontend" class="story-box" style="display:none;"' in page
    assert 'id="story-dl" class="story-box" style="display:none;"' in page
    assert 'id="story-noob" class="story-box" style="display:none;"' in page
    assert "function showStory(id)" in page


def test_each_story_stays_short_and_keeps_the_alice_anchor() -> None:
    page = _read(INDEX_HTML)

    for role in ("frontend", "backend", "dl", "noob"):
        text = _extract_story_text(page, role)
        assert "alice-pgpool-2026-04-10" in text
        assert len(text) <= 400, f"{role} story is too long: {len(text)}"


def test_html_commands_use_split_with_without_workspaces() -> None:
    page = _read(INDEX_HTML)

    assert 'id="cmd1"' in page
    assert 'id="cmd2a"' in page
    assert 'id="cmd2b"' in page
    assert "mkdir -p /tmp/demo_insights_A && cd /tmp/demo_insights_A &&" in page
    assert "> /tmp/demo_insights_A/A_without.log" in page
    assert "mkdir -p /tmp/demo_insights_B && cd /tmp/demo_insights_B &&" in page
    assert "/tmp/demo_insights_B/isw-clone" in page
    assert 'echo "❌ git clone 失败，请检查 github 配置（ssh key / https token）后重试"' in page
    assert 'echo "✅ Step 2a: clone 完成 → /tmp/demo_insights_B/isw-clone"' in page
    assert "> /tmp/demo_insights_B/isd.log 2>&1" in page
    assert "> /tmp/demo_insights_B/B_with.log" in page
    assert (
        "grep -c alice-pgpool-2026-04-10 /tmp/demo_insights_A/A_without.log "
        "/tmp/demo_insights_B/B_with.log"
    ) in page


def test_validation_scripts_use_named_tmp_workspaces() -> None:
    without_reproduce = _read(WITHOUT_REPRODUCE)
    without_oneline = _read(WITHOUT_ONELINE)
    with_reproduce = _read(WITH_REPRODUCE)
    with_oneline = _read(WITH_ONELINE)

    assert 'WORKSPACE_A="/tmp/demo_insights_A"' in without_reproduce
    assert 'cd "${WORKSPACE_A}"' in without_reproduce
    assert 'RAW="${WORKSPACE_A}/A_without.raw"' in without_reproduce
    assert 'LOG="${WORKSPACE_A}/A_without.log"' in without_reproduce

    assert 'WORKSPACE_A="/tmp/demo_insights_A"' in without_oneline
    assert 'cd "${WORKSPACE_A}"' in without_oneline
    assert 'OUT_FILE="${WORKSPACE_A}/A_without.log"' in without_oneline

    assert 'WORKSPACE_B="/tmp/demo_insights_B"' in with_reproduce
    assert 'cd "${WORKSPACE_B}"' in with_reproduce
    assert 'CLONE_DIR="${WORKSPACE_B}/isw-clone"' in with_reproduce
    assert 'RAW="${WORKSPACE_B}/B_with.raw"' in with_reproduce
    assert 'LOG="${WORKSPACE_B}/B_with.log"' in with_reproduce

    assert 'WORKSPACE_B="/tmp/demo_insights_B"' in with_oneline
    assert 'cd "${WORKSPACE_B}"' in with_oneline
    assert 'CLONE="${WORKSPACE_B}/isw-clone"' in with_oneline
    assert 'OUT_FILE="${WORKSPACE_B}/B_with.log"' in with_oneline
