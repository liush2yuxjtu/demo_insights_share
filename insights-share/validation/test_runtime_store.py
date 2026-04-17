from __future__ import annotations

from pathlib import Path

from insightsd.runtime import RuntimeStore


def test_runtime_store_persists_session_and_event_sequence(tmp_path: Path) -> None:
    store = RuntimeStore(tmp_path / "runtime")

    session = store.start_session(kind="demo", title="Bob 午高峰事故")
    store.append_event(
        session["id"],
        stage="bootstrap",
        status="running",
        source="runner",
        message="启动 demo",
    )
    store.append_event(
        session["id"],
        stage="result",
        status="ok",
        source="adapter",
        message="生成修复建议",
        metrics={"fast_path_s": 1.2, "confidence": 0.82},
        artifact_refs=[{"label": "PM 演示", "href": "/artifacts/demo_docs/pm_walkthrough.md"}],
    )

    reloaded = RuntimeStore(tmp_path / "runtime")
    saved = reloaded.get_session(session["id"])
    assert saved is not None
    assert saved["kind"] == "demo"
    assert saved["current_stage"] == "result"
    assert saved["progress"] > 0
    assert saved["headline_metrics"]["fast_path_s"] == 1.2
    assert saved["latest_message"] == "生成修复建议"

    events = reloaded.get_events(session["id"])
    assert [event["stage"] for event in events] == ["bootstrap", "result"]
    assert events[-1]["artifact_refs"][0]["label"] == "PM 演示"


def test_runtime_store_filters_and_summary(tmp_path: Path) -> None:
    store = RuntimeStore(tmp_path / "runtime")

    demo = store.start_session(kind="demo", title="Demo")
    validation = store.start_session(kind="validation", title="Validation")

    store.append_event(
        demo["id"],
        stage="summary",
        status="completed",
        source="runner",
        message="demo 完成",
        metrics={"fast_path_s": 1.1},
    )
    store.append_event(
        validation["id"],
        stage="phase2",
        status="running",
        source="validation",
        message="Stop hook 检查中",
    )

    running_validation = store.list_sessions(kind="validation", status="running")
    assert [item["id"] for item in running_validation] == [validation["id"]]

    summary = store.system_summary()
    assert summary["counts"]["total"] == 2
    assert summary["counts"]["by_kind"]["demo"] == 1
    assert summary["counts"]["by_kind"]["validation"] == 1
    assert summary["counts"]["by_status"]["running"] == 1
    assert summary["live_session"]["id"] == validation["id"]
