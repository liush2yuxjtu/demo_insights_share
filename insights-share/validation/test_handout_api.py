from pathlib import Path

from demo_codes.insightsd import server


def test_dashboard_links_to_handout_and_pm_script() -> None:
    dashboard_html = Path(server.__file__).with_name("dashboard.html").read_text(encoding="utf-8")
    assert 'href="/handout"' in dashboard_html
    assert 'href="/pm-script"' in dashboard_html


def test_handout_and_pm_script_routes_are_served(tmp_path, monkeypatch) -> None:
    latest = tmp_path / "latest.json"
    latest.write_text('{"status": "passed"}\n', encoding="utf-8")
    monkeypatch.setattr(server, "HANDOUT_LATEST_PATH", latest)

    class Dummy(server.Handler):
        def __init__(self) -> None:
            self.responses = []
            self._page = None
            self.path = "/"

        def _serve_page(self, filename: str) -> None:
            self._page = filename

        def _send_json(self, payload, status: int = 200) -> None:
            self.responses.append((status, payload))

        def _not_found(self) -> None:
            self.responses.append((404, None))

    handout = Dummy()
    handout.path = "/handout"
    handout.do_GET()
    assert handout._page == "handout.html"

    pm_script = Dummy()
    pm_script.path = "/pm-script"
    pm_script.do_GET()
    assert pm_script._page == "pm_script.html"

    latest_request = Dummy()
    latest_request.path = "/artifacts/validation/artifacts/handout/latest.json"
    latest_request.do_GET()
    assert latest_request.responses[-1][0] == 200
    assert latest_request.responses[-1][1]["status"] == "passed"
