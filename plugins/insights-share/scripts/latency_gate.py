#!/usr/bin/env python3
"""latency_gate.py — M6_LATENCY 数值门。

读取 metrics jsonl + baseline(budget) → 输出 PASS/FAIL JSON；退出码 0/1。

## 用法

    python latency_gate.py \
        --metrics ~/.cache/insights-share/metrics/2026-04-22.jsonl \
        --baseline proposal/baselines/latency_baseline.json \
        [--previous proposal/baselines/latency_prev.json] \
        [--out gate_result.json]

## 输入 jsonl 每行 schema

    {"stage":"search_agent","status":"ok","latency_ms":3421,
     "cache":"miss","turns":3,"model":"MiniMax-M2.7-highspeed",
     "ts":"2026-04-22T11:55:00Z","run_id":"abc"}

## 三道门

1. `gate_baseline_recorded`     — baseline.samples ≥ 5 即 PASS
2. `gate_p95_budget`             — end-to-end + per-stage p95 全部 ≤ budget
3. `gate_no_regression`          — 任何 stage p95 相对 previous 不得涨 > tolerance_pct

任一 FAIL 即整体 FAIL，退出码 1；否则退出码 0。
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any


def _percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    k = (len(ordered) - 1) * (pct / 100.0)
    lo = math.floor(k)
    hi = math.ceil(k)
    if lo == hi:
        return ordered[lo]
    return ordered[lo] + (ordered[hi] - ordered[lo]) * (k - lo)


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    out: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid jsonl line in {path}: {exc}") from exc
    return out


def _group_latencies(samples: list[dict[str, Any]]) -> dict[str, list[float]]:
    by_stage: dict[str, list[float]] = {}
    for s in samples:
        stage = s.get("stage")
        lat = s.get("latency_ms")
        if not stage or not isinstance(lat, (int, float)):
            continue
        by_stage.setdefault(stage, []).append(float(lat))
    return by_stage


def _end_to_end_split(samples: list[dict[str, Any]]) -> dict[str, list[float]]:
    hit: list[float] = []
    miss: list[float] = []
    for s in samples:
        if s.get("stage") != "end_to_end":
            continue
        lat = s.get("latency_ms")
        if not isinstance(lat, (int, float)):
            continue
        cache = (s.get("cache") or "").lower()
        if cache == "hit":
            hit.append(float(lat))
        elif cache == "miss":
            miss.append(float(lat))
    return {"cache_hit": hit, "cache_miss": miss}


def gate_baseline_recorded(baseline: dict[str, Any]) -> tuple[str, str]:
    n = len(baseline.get("samples") or [])
    if n >= 5:
        return "PASS", f"baseline has {n} samples"
    return "FAIL", f"baseline has only {n} samples (< 5)"


def gate_p95_budget(
    samples: list[dict[str, Any]], baseline: dict[str, Any]
) -> tuple[str, list[str]]:
    budget = baseline.get("budget") or {}
    notes: list[str] = []
    ok = True

    # per-stage
    per_stage = (budget.get("per_stage") or {})
    for stage, lats in _group_latencies(samples).items():
        if stage == "end_to_end":
            continue
        limit = (per_stage.get(stage) or {}).get("p95_ms")
        if limit is None:
            continue
        p95 = _percentile(lats, 95)
        status = "PASS" if p95 <= limit else "FAIL"
        if status == "FAIL":
            ok = False
        notes.append(f"{stage} p95={p95:.0f}ms budget={limit}ms {status}")

    # end-to-end
    e2e_budget = budget.get("end_to_end") or {}
    for label, lats in _end_to_end_split(samples).items():
        if not lats:
            continue
        limit = (e2e_budget.get(label) or {}).get("p95_ms")
        if limit is None:
            continue
        p95 = _percentile(lats, 95)
        status = "PASS" if p95 <= limit else "FAIL"
        if status == "FAIL":
            ok = False
        notes.append(f"end_to_end[{label}] p95={p95:.0f}ms budget={limit}ms {status}")

    return ("PASS" if ok else "FAIL"), notes


def gate_no_regression(
    samples: list[dict[str, Any]],
    previous: dict[str, Any],
    tolerance_pct: float,
) -> tuple[str, list[str]]:
    prev_samples = previous.get("samples") or []
    if not prev_samples:
        return "SKIP", ["no previous baseline — skip regression check"]

    cur_by = _group_latencies(samples)
    prev_by = _group_latencies(prev_samples)
    ok = True
    notes: list[str] = []
    for stage, prev_lats in prev_by.items():
        cur_lats = cur_by.get(stage)
        if not cur_lats:
            continue
        prev_p95 = _percentile(prev_lats, 95)
        cur_p95 = _percentile(cur_lats, 95)
        if prev_p95 <= 0:
            continue
        delta_pct = (cur_p95 - prev_p95) / prev_p95 * 100.0
        status = "PASS" if delta_pct <= tolerance_pct else "FAIL"
        if status == "FAIL":
            ok = False
        notes.append(
            f"{stage} prev_p95={prev_p95:.0f}ms cur_p95={cur_p95:.0f}ms "
            f"delta={delta_pct:+.1f}% tol={tolerance_pct:.0f}% {status}"
        )
    return ("PASS" if ok else "FAIL"), notes


def run(metrics_path: Path, baseline_path: Path, previous_path: Path | None) -> dict[str, Any]:
    metrics = _load_jsonl(metrics_path)
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    previous = (
        json.loads(previous_path.read_text(encoding="utf-8"))
        if previous_path and previous_path.is_file()
        else {}
    )
    tolerance = float((baseline.get("budget") or {}).get("regression_tolerance_pct", 10))

    g1_status, g1_reason = gate_baseline_recorded(baseline)
    g2_status, g2_notes = gate_p95_budget(metrics, baseline)
    g3_status, g3_notes = gate_no_regression(metrics, previous, tolerance)

    gates = [
        {"name": "gate_baseline_recorded", "status": g1_status, "notes": [g1_reason]},
        {"name": "gate_p95_budget",         "status": g2_status, "notes": g2_notes},
        {"name": "gate_no_regression",      "status": g3_status, "notes": g3_notes},
    ]
    blocking = [g for g in gates if g["status"] == "FAIL"]
    verdict = "FAIL" if blocking else "PASS"
    return {
        "verdict": verdict,
        "metrics_path": str(metrics_path),
        "baseline_path": str(baseline_path),
        "sample_count": len(metrics),
        "gates": gates,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--metrics", required=True, type=Path)
    ap.add_argument("--baseline", required=True, type=Path)
    ap.add_argument("--previous", type=Path, default=None)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    result = run(args.metrics, args.baseline, args.previous)
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        args.out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0 if result["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
