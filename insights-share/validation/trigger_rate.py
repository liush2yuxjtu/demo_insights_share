#!/usr/bin/env python3
"""按 cases.yml 评测 insightsd 的触发率（precision/recall/f1）。

通过 HTTP GET /search?q=...&k=3 查已启动的 daemon，不依赖任何 Python 包。
严格规则：
- positive: top1.id == expected_card_id 且 score >= threshold → pass
- negative: 无 hit 或 top1.score < threshold → pass
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

DEFAULT_WIKI = "http://127.0.0.1:7821"


def parse_cases_yml(path: Path) -> list[dict[str, Any]]:
    """极简 YAML 解析器：只支持我们自己写的 cases.yml 的平铺结构。

    不引入 PyYAML 以保持零依赖。格式约定：
        cases:
          - id: t01
            problem: "..."
            should_trigger: true
            expected_card_id: foo
            split: train
            rationale: "..."
    """
    text = path.read_text(encoding="utf-8")
    cases: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for raw_line in text.splitlines():
        if raw_line.lstrip().startswith("#") or raw_line.strip() == "cases:":
            continue
        stripped = raw_line.strip()
        if not stripped:
            continue
        m_new = re.match(r"- id:\s*(\S+)", stripped)
        if m_new:
            if current:
                cases.append(current)
            current = {"id": m_new.group(1)}
            continue
        if current is None:
            continue
        m_kv = re.match(r"([a-z_]+):\s*(.*)$", stripped)
        if not m_kv:
            continue
        key = m_kv.group(1)
        val_raw = m_kv.group(2).strip()
        if val_raw.startswith('"') and val_raw.endswith('"'):
            val: Any = val_raw[1:-1]
        elif val_raw == "true":
            val = True
        elif val_raw == "false":
            val = False
        else:
            val = val_raw
        current[key] = val
    if current:
        cases.append(current)
    return cases


def search(wiki: str, q: str, k: int = 3) -> list[dict[str, Any]]:
    url = f"{wiki.rstrip('/')}/search?{urllib.parse.urlencode({'q': q, 'k': k})}"
    with urllib.request.urlopen(url, timeout=5.0) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return list(data.get("hits") or [])


def evaluate(
    cases: list[dict[str, Any]],
    wiki: str,
    threshold: float,
    split: str,
) -> dict[str, Any]:
    filtered = [c for c in cases if c.get("split") == split]
    per_case: list[dict[str, Any]] = []
    tp = fp = tn = fn = 0
    for case in filtered:
        problem = case["problem"]
        should = bool(case["should_trigger"])
        expected = case.get("expected_card_id")
        hits = search(wiki, problem, k=3)
        top = hits[0] if hits else None
        top_id = top.get("id") if top else None
        top_score = float(top.get("score") or 0) if top else 0.0
        triggered = bool(top and top_score >= threshold)
        if should:
            correct_id = triggered and (top_id == expected)
            if correct_id:
                tp += 1
                verdict = "TP"
            else:
                fn += 1
                verdict = "FN"
        else:
            if not triggered:
                tn += 1
                verdict = "TN"
            else:
                fp += 1
                verdict = "FP"
        per_case.append(
            {
                "id": case["id"],
                "split": split,
                "should_trigger": should,
                "expected_card_id": expected,
                "top_id": top_id,
                "top_score": top_score,
                "triggered": triggered,
                "verdict": verdict,
            }
        )

    total = len(filtered) or 1
    precision = tp / (tp + fp) if (tp + fp) > 0 else (1.0 if fn == 0 else 0.0)
    recall = tp / (tp + fn) if (tp + fn) > 0 else 1.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall) > 0
        else 0.0
    )
    accuracy = (tp + tn) / total

    return {
        "split": split,
        "threshold": threshold,
        "counts": {"tp": tp, "fp": fp, "tn": tn, "fn": fn, "total": total},
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "accuracy": round(accuracy, 4),
        "per_case": per_case,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    default_cases = Path(__file__).resolve().parent / "trigger_cases" / "cases.yml"
    ap.add_argument("--cases", default=str(default_cases))
    ap.add_argument("--split", choices=["train", "test", "all"], default="all")
    ap.add_argument("--wiki", default=DEFAULT_WIKI)
    ap.add_argument("--threshold", type=float, default=0.02)
    ap.add_argument("--report", default=None, help="可选 JSON 报告输出路径")
    args = ap.parse_args()

    cases = parse_cases_yml(Path(args.cases))
    if not cases:
        print("[TRIGGER_RATE] no cases parsed", file=sys.stderr)
        return 2

    splits = ["train", "test"] if args.split == "all" else [args.split]
    all_reports = []
    for split in splits:
        report = evaluate(cases, args.wiki, args.threshold, split)
        all_reports.append(report)
        print(
            f"[TRIGGER_RATE split={split}] "
            f"total={report['counts']['total']} "
            f"tp={report['counts']['tp']} fp={report['counts']['fp']} "
            f"tn={report['counts']['tn']} fn={report['counts']['fn']} "
            f"precision={report['precision']} recall={report['recall']} "
            f"f1={report['f1']} acc={report['accuracy']}"
        )
        for pc in report["per_case"]:
            print(
                f"  {pc['id']} [{pc['verdict']}] score={pc['top_score']:.4f} "
                f"top_id={pc['top_id']} expected={pc.get('expected_card_id')}"
            )

    if args.report:
        out = Path(args.report)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(all_reports, ensure_ascii=False, indent=2), encoding="utf-8")

    # 单 split 模式下按该 split 判定退出码；all 模式下取最弱
    final = min(r["f1"] for r in all_reports)
    return 0 if final > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
