"""后台 runner：给 Ops 页面触发 demo / validation。"""

from __future__ import annotations

import asyncio
import json
import threading
import time
from pathlib import Path
from typing import Any

import adapter
from insights_cli import DEFAULT_LOCAL_CONTEXT, DEFAULT_PROBLEM

from .runtime import RuntimeStore
from .store import InsightStore, TreeInsightStore, search_cards


class RunnerManager:
    def __init__(
        self,
        *,
        store: InsightStore | TreeInsightStore,
        runtime: RuntimeStore,
        app_root: Path,
    ) -> None:
        self.store = store
        self.runtime = runtime
        self.app_root = Path(app_root)
        self.demo_codes = self.app_root / "demo_codes"
        self.demo_docs = self.app_root / "demo_docs"
        self.validation_root = self.app_root / "validation"

    def _artifact(self, rel: str, label: str) -> dict[str, str]:
        return {"label": label, "href": f"/artifacts/{rel}"}

    def start_demo(
        self,
        *,
        problem: str | None = None,
        local_context: str | None = None,
        use_ai: bool = False,
    ) -> str:
        if not self.runtime.runner_enabled:
            raise PermissionError("runners disabled")
        title = "Bob 午高峰 PostgreSQL 故障演示"
        session = self.runtime.start_session(
            kind="demo",
            title=title,
            artifact_refs=[
                self._artifact("demo_docs/pm_walkthrough.md", "PM 演示"),
                self._artifact("demo_docs/design.md", "系统设计"),
            ],
        )
        thread = threading.Thread(
            target=self._run_demo,
            args=(session["id"], problem or DEFAULT_PROBLEM, local_context or DEFAULT_LOCAL_CONTEXT, use_ai),
            daemon=True,
        )
        thread.start()
        return session["id"]

    def _seed_cards(self) -> list[dict[str, Any]]:
        cards: list[dict[str, Any]] = []
        for path in sorted((self.demo_codes / "seeds").glob("*.json")):
            cards.append(json.loads(path.read_text(encoding="utf-8")))
        return cards

    def _demo_search_cards(self, seed_cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
        merged: dict[str, dict[str, Any]] = {}
        for card in self.store.load():
            if not isinstance(card, dict) or not card.get("id"):
                continue
            merged[str(card["id"])] = dict(card)
        for card in seed_cards:
            if not isinstance(card, dict) or not card.get("id"):
                continue
            merged[str(card["id"])] = dict(card)
        return list(merged.values())

    def _run_demo(self, session_id: str, problem: str, local_context: str, use_ai: bool) -> None:
        start = time.monotonic()
        try:
            self.runtime.append_event(
                session_id,
                stage="bootstrap",
                status="running",
                source="demo-runner",
                message="准备 demo 环境",
            )
            cards = self._seed_cards()
            self.runtime.append_event(
                session_id,
                stage="publish",
                status="ok",
                source="demo-runner",
                message=f"已加载 {len(cards)} 张 demo 样本卡片（只读回放）",
                metrics={"published_count": len(cards)},
                artifact_refs=[self._artifact("demo_codes/seeds/alice_pgpool.json", "Alice 种子卡")],
            )
            hits = search_cards(
                self._demo_search_cards(cards),
                problem,
                k=3,
                skip_not_triggered=isinstance(self.store, TreeInsightStore),
            )
            if not hits:
                self.runtime.append_event(
                    session_id,
                    stage="search",
                    status="failed",
                    source="search",
                    message="未命中任何卡片",
                )
                self.runtime.append_event(
                    session_id,
                    stage="summary",
                    status="failed",
                    source="demo-runner",
                    message="demo 失败：没有可用卡片",
                    metrics={"fast_path_s": round(time.monotonic() - start, 3)},
                )
                return
            top = hits[0]
            self.runtime.append_event(
                session_id,
                stage="search",
                status="ok",
                source="search",
                message=f"命中 {top.get('id')} (score={top.get('score')})",
                metrics={"score": top.get("score", 0)},
                payload={"card_id": top.get("id"), "title": top.get("title")},
                artifact_refs=[self._artifact("demo_docs/pm_walkthrough_star.md", "STAR 讲解")],
            )

            if use_ai:
                result = asyncio.run(adapter.adapt(top, problem, local_context))
                self.runtime.append_event(
                    session_id,
                    stage="adapt",
                    status="ok",
                    source="adapter",
                    message=result.diff_summary or "AI 适配完成",
                    metrics={"adapter_latency_s": round(result.latency_s, 3)},
                    payload={"verdict": result.verdict},
                )
            else:
                result = adapter.AdapterResult(
                    verdict="adopt",
                    adapted_insight=str(top.get("fix", "")),
                    diff_summary="runner 默认走 no-ai 路径",
                    confidence=float(top.get("confidence", 0.5)),
                    latency_s=0.0,
                )

            self.runtime.append_event(
                session_id,
                stage="result",
                status="ok",
                source="demo-runner",
                message=result.adapted_insight,
                metrics={
                    "confidence": round(result.confidence, 3),
                    "fast_path_s": round(time.monotonic() - start, 3),
                },
                payload={
                    "verdict": result.verdict,
                    "diff_summary": result.diff_summary,
                    "card_id": top.get("id"),
                },
                artifact_refs=[
                    self._artifact("demo_docs/terminal_snapshot.md", "终端快照"),
                    self._artifact("validation/reports/final_report.html", "验证总览"),
                ],
            )
            self.runtime.append_event(
                session_id,
                stage="summary",
                status="completed",
                source="demo-runner",
                message="demo 完成，可进入历史回放",
                metrics={
                    "fast_path_s": round(time.monotonic() - start, 3),
                    "slow_path_s": 62.0,
                },
            )
        except Exception as exc:  # noqa: BLE001
            self.runtime.append_event(
                session_id,
                stage="summary",
                status="failed",
                source="demo-runner",
                message=f"demo 异常：{type(exc).__name__}: {exc}",
                metrics={"fast_path_s": round(time.monotonic() - start, 3)},
            )

    def start_validation(self) -> str:
        if not self.runtime.runner_enabled:
            raise PermissionError("runners disabled")
        session = self.runtime.start_session(
            kind="validation",
            title="Phase 0-5 验证流",
            artifact_refs=[
                self._artifact("validation/reports/final_report.html", "验证报告"),
                self._artifact(
                    "validation/reports/deliverables/DELIVERABLES_SUMMARY.html",
                    "交付物证据",
                ),
            ],
        )
        thread = threading.Thread(target=self._run_validation, args=(session["id"],), daemon=True)
        thread.start()
        return session["id"]

    def _phase_specs(self) -> list[dict[str, Any]]:
        reports = self.validation_root / "reports"
        snapshots = self.validation_root / "snapshots"
        return [
            {
                "stage": "phase0",
                "message": "Baseline + MiniMax 预检",
                "ok": (snapshots / "phase0_tmux.txt").is_file(),
                "metrics": {"snapshot": "phase0_tmux.txt"},
            },
            {
                "stage": "phase1",
                "message": "Trigger rate 20 cases",
                "ok": (reports / "trigger_rate_test.json").is_file(),
                "metrics": {"report": "trigger_rate_test.json"},
            },
            {
                "stage": "phase2",
                "message": "SILENT_AND_JUST_RUN Stop hook",
                "ok": (snapshots / "phase2_tmux.txt").is_file(),
                "metrics": {"snapshot": "phase2_tmux.txt"},
            },
            {
                "stage": "phase3",
                "message": "Wiki CRUD 操作",
                "ok": (snapshots / "phase3_tmux.txt").is_file(),
                "metrics": {"snapshot": "phase3_tmux.txt"},
            },
            {
                "stage": "phase4",
                "message": "Wiki 4 层结构迁移",
                "ok": (reports / "wiki_structure.json").is_file(),
                "metrics": {"report": "wiki_structure.json"},
            },
            {
                "stage": "phase5",
                "message": "MiniMax agentic search",
                "ok": (snapshots / "phase5_tmux.txt").is_file(),
                "metrics": {"snapshot": "phase5_tmux.txt"},
            },
        ]

    def _run_validation(self, session_id: str) -> None:
        passed = 0
        total = 0
        for spec in self._phase_specs():
            total += 1
            self.runtime.append_event(
                session_id,
                stage=spec["stage"],
                status="running",
                source="validation-runner",
                message=f"{spec['message']} 检查中",
            )
            time.sleep(0.05)
            stage_status = "ok" if spec["ok"] else "failed"
            if spec["ok"]:
                passed += 1
            self.runtime.append_event(
                session_id,
                stage=spec["stage"],
                status=stage_status,
                source="validation-runner",
                message=spec["message"],
                metrics=spec["metrics"],
                artifact_refs=[
                    self._artifact("validation/reports/final_report.html", "验证报告"),
                ],
            )

        self.runtime.append_event(
            session_id,
            stage="summary",
            status="completed" if passed == total else "failed",
            source="validation-runner",
            message=f"Phase 验证完成：{passed}/{total} 通过",
            metrics={"passed": passed, "total": total},
            artifact_refs=[
                self._artifact("validation/reports/final_report.html", "验证报告"),
                self._artifact(
                    "validation/reports/deliverables/DELIVERABLES_SUMMARY.html",
                    "交付物证据",
                ),
            ],
        )
