from __future__ import annotations

import subprocess
import sys
import tomllib
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_release_version_matches_pyproject() -> None:
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert pyproject["project"]["version"] == version
    assert version == "1.0.0"


def test_build_release_produces_versioned_bundle(tmp_path: Path) -> None:
    out_dir = tmp_path / "dist"
    subprocess.run(
        [sys.executable, "release/build_release.py", "--output-dir", str(out_dir)],
        cwd=ROOT,
        check=True,
    )

    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    prefix = f"insights-share-v{version}"
    zip_path = out_dir / f"{prefix}.zip"
    manifest_path = out_dir / f"{prefix}.manifest.txt"
    sha_path = out_dir / f"{prefix}.zip.sha256"

    assert zip_path.is_file()
    assert manifest_path.is_file()
    assert sha_path.is_file()

    manifest_lines = manifest_path.read_text(encoding="utf-8").splitlines()
    assert "demo_codes/insights_cli.py" in manifest_lines
    assert "demo_codes/insightsd/dashboard.html" in manifest_lines
    assert "demo_docs/design.md" in manifest_lines
    assert "validation/test_release_package.py" in manifest_lines
    assert "demo_codes/.env" not in manifest_lines
    assert "demo_codes/wiki.json" not in manifest_lines
    assert not any(".claude/settings.json" in line for line in manifest_lines)
    assert not any(".venv/" in line for line in manifest_lines)
    assert not any(".pytest_cache/" in line for line in manifest_lines)
    assert not any("__pycache__/" in line for line in manifest_lines)

    with zipfile.ZipFile(zip_path) as zf:
        names = set(zf.namelist())

    assert f"{prefix}/VERSION" in names
    assert f"{prefix}/pyproject.toml" in names
    assert f"{prefix}/demo_codes/insights_cli.py" in names
    assert f"{prefix}/demo_codes/insightsd/dashboard.html" in names
    assert f"{prefix}/demo_docs/design.md" in names
    assert f"{prefix}/validation/test_release_package.py" in names
    assert f"{prefix}/demo_codes/.env" not in names
    assert f"{prefix}/demo_codes/wiki.json" not in names
