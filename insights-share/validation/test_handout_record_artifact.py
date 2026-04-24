from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
HANDOUT_RECORD = ROOT / "insights-share/validation/scripts/handout_record.mjs"


def test_handout_record_requires_real_mp4_artifact() -> None:
    script = HANDOUT_RECORD.read_text(encoding="utf-8")

    assert "recordVideo" in script
    assert "ensureVideoArtifact(pageVideo)" in script
    assert "stat(filePath)" in script
    assert "isUsableFile(VIDEO_PATH)" in script
    assert "Playwright 视频转码 mp4 失败" in script
    assert "录屏产物缺失" in script
    assert script.index("await ensureVideoArtifact(pageVideo);") < script.index("await writeFile(MANIFEST_PATH")
