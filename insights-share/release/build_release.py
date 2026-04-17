"""构建带版本号的 release 压缩包与校验文件。"""

from __future__ import annotations

import argparse
import hashlib
import tomllib
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = ROOT / "dist"
INCLUDE_PATHS = [
    ROOT / "VERSION",
    ROOT / "pyproject.toml",
    ROOT / "plan.md",
    ROOT / "release" / "README.txt",
    ROOT / "demo_codes",
    ROOT / "demo_docs",
    ROOT / "validation",
]
EXCLUDE_NAMES = {
    ".DS_Store",
    ".env",
    ".venv",
    ".pytest_cache",
    "__pycache__",
    ".coverage",
    "dist",
    "build",
}
EXCLUDE_SUFFIXES = {".pyc", ".pyo"}
EXCLUDE_FILES = {
    ROOT / "demo_codes" / "wiki.json",
}


def read_version() -> str:
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    if not version:
        raise ValueError("VERSION 不能为空")
    return version


def read_pyproject_version() -> str:
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    return str(data["project"]["version"]).strip()


def should_skip(path: Path) -> bool:
    if path in EXCLUDE_FILES:
        return True
    if any(part in EXCLUDE_NAMES for part in path.parts):
        return True
    if ".claude" in path.parts and path.name.startswith("settings.json"):
        return True
    if path.suffix in EXCLUDE_SUFFIXES:
        return True
    return False


def iter_release_files() -> list[Path]:
    files: list[Path] = []
    for item in INCLUDE_PATHS:
        if item.is_file():
            if not should_skip(item):
                files.append(item)
            continue
        if item.is_dir():
            for path in sorted(item.rglob("*")):
                if path.is_dir():
                    continue
                if should_skip(path):
                    continue
                files.append(path)
    return files


def sha256_of_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_release(output_dir: Path) -> tuple[Path, Path, Path]:
    version = read_version()
    pyproject_version = read_pyproject_version()
    if version != pyproject_version:
        raise ValueError(
            f"VERSION({version}) 与 pyproject.toml({pyproject_version}) 不一致"
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    prefix = f"insights-share-v{version}"
    zip_path = output_dir / f"{prefix}.zip"
    manifest_path = output_dir / f"{prefix}.manifest.txt"
    sha_path = output_dir / f"{prefix}.zip.sha256"

    files = iter_release_files()
    manifest_lines: list[str] = []

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for src in files:
            rel = src.relative_to(ROOT)
            arcname = Path(prefix) / rel
            zf.write(src, arcname.as_posix())
            manifest_lines.append(rel.as_posix())

    manifest_path.write_text("\n".join(manifest_lines) + "\n", encoding="utf-8")
    sha_path.write_text(
        f"{sha256_of_file(zip_path)}  {zip_path.name}\n",
        encoding="utf-8",
    )
    return zip_path, manifest_path, sha_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="构建 insights-share release 压缩包")
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="输出目录，默认是 insights-share/dist",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    zip_path, manifest_path, sha_path = build_release(Path(args.output_dir))
    print(f"release zip: {zip_path}")
    print(f"manifest: {manifest_path}")
    print(f"sha256: {sha_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
