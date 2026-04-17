from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "demo_codes" / "standalone_runtime_preview.html"


def test_standalone_runtime_page_is_self_contained() -> None:
    html = PAGE.read_text(encoding="utf-8")

    assert PAGE.is_file()
    assert "Preview 模式" in html
    assert "Ops 模式" in html
    assert "<style>" in html
    assert "<script>" in html
    assert 'href="/static/' not in html
    assert 'src="/static/' not in html
    assert "/api/stream" not in html
    assert "内置演示数据" in html
