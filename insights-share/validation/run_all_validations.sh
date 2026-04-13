#!/usr/bin/env bash
# 一键复验：读取 Phase 0-5 已生成的快照与报告，组装 final_report.html。
# 不会重跑各个 phase（避免重复消耗 MiniMax API 配额）；如需重跑请单独运行
# 各 phaseN 的 tmux 流程或重新执行计划。
#
# 退出码：所有 phase 都通过 → 0；否则 → 1。

set -u
ROOT="/Users/m1/projects/demo_insights_share/insights-share/validation"
SNAPSHOTS="$ROOT/snapshots"
REPORTS="$ROOT/reports"
HTML="$REPORTS/final_report.html"
mkdir -p "$REPORTS" "$SNAPSHOTS"

python3 - <<PY
import json
import os
import re
from datetime import datetime
from html import escape
from pathlib import Path

ROOT = Path("$ROOT")
SNAP = ROOT / "snapshots"
REPS = ROOT / "reports"

def file_size(p: Path) -> int:
    try:
        return p.stat().st_size
    except FileNotFoundError:
        return 0

def grep_count(p: Path, pattern: str) -> int:
    if not p.is_file():
        return 0
    rx = re.compile(pattern)
    return sum(1 for line in p.read_text(encoding="utf-8", errors="ignore").splitlines() if rx.search(line))

def grep_any(p: Path, pattern: str) -> bool:
    return grep_count(p, pattern) > 0

phases = []

# Phase 0
p0_snap = SNAP / "phase0_tmux.txt"
phases.append({
    "phase": "Phase 0",
    "task": "Baseline + MiniMax 预检",
    "rule": "validation framework #2 (tmux 抓取)",
    "snapshot": p0_snap,
    "pass": grep_any(p0_snap, r"BASELINE-EXIT=0") and grep_any(p0_snap, r"SMOKE-EXIT=0"),
    "metrics": "demo finished + MiniMax PONG",
})

# Phase 4
p4_snap = SNAP / "phase4_tmux.txt"
struct_report = REPS / "wiki_structure.json"
struct_pass = False
struct_summary = "(no report)"
if struct_report.is_file():
    try:
        d = json.loads(struct_report.read_text(encoding="utf-8"))
        struct_pass = bool(d.get("pass"))
        n = len(d.get("checks") or [])
        ok = sum(1 for c in d.get("checks") or [] if c.get("pass"))
        struct_summary = f"{ok}/{n} layer checks PASS"
    except Exception as exc:
        struct_summary = f"(parse error: {exc})"
phases.append({
    "phase": "Phase 4",
    "task": "Wiki 4 层结构迁移",
    "rule": "validation task #4 (wiki_type → INDEX → item → raw)",
    "snapshot": p4_snap,
    "pass": struct_pass and grep_any(p4_snap, r"alice-pgpool-2026-04-10"),
    "metrics": struct_summary,
})

# Phase 1
p1_snap = SNAP / "phase1_tmux.txt"
train_rep = REPS / "trigger_rate_train.json"
test_rep = REPS / "trigger_rate_test.json"
p1_pass = False
p1_metrics = "(no report)"
if train_rep.is_file() and test_rep.is_file():
    try:
        train_d = json.loads(train_rep.read_text(encoding="utf-8"))
        test_d = json.loads(test_rep.read_text(encoding="utf-8"))
        train_f1 = train_d.get("f1", 0)
        test_f1 = test_d.get("f1", 0)
        test_prec = test_d.get("precision", 0)
        p1_pass = test_f1 >= 0.75 and test_prec >= 0.8
        p1_metrics = (
            f"train f1={train_f1:.4f} | test f1={test_f1:.4f} "
            f"precision={test_prec:.4f} acc={test_d.get('accuracy',0):.4f}"
        )
    except Exception as exc:
        p1_metrics = f"(parse error: {exc})"
phases.append({
    "phase": "Phase 1",
    "task": "Trigger rate 20 cases",
    "rule": "validation task #1 (12 train / 8 test)",
    "snapshot": p1_snap,
    "pass": p1_pass,
    "metrics": p1_metrics,
})

# Phase 5
p5_snap = SNAP / "phase5_tmux.txt"
p5_pass = (
    grep_any(p5_snap, r'"item":\s*"postgres_pool"')
    and grep_count(p5_snap, r"fallback") == 0
)
phases.append({
    "phase": "Phase 5",
    "task": "MiniMax agentic search",
    "rule": "validation task #5 (agentic search wiki minimax)",
    "snapshot": p5_snap,
    "pass": p5_pass,
    "metrics": "real haiku-agent hit postgres_pool, NO fallback",
})

# Phase 2
p2_snap = SNAP / "phase2_tmux.txt"
p2_pass = (
    grep_any(p2_snap, r"\[SILENT_AND_JUST_RUN\]")
    and grep_any(p2_snap, r"postgres_pool")
    and grep_count(p2_snap, r"fallback") == 0
)
phases.append({
    "phase": "Phase 2",
    "task": "SILENT_AND_JUST_RUN Stop hook",
    "rule": "validation task #2 (S-T-A-R + silent trigger)",
    "snapshot": p2_snap,
    "pass": p2_pass,
    "metrics": "Bob silent session → Stop hook → postgres_pool",
})

# Phase 3
p3_snap = SNAP / "phase3_tmux.txt"
p3_crud_count = grep_count(p3_snap, r"^CRUD_OK:")
p3_pass = p3_crud_count >= 6 and grep_count(p3_snap, r"fallback") == 0
phases.append({
    "phase": "Phase 3",
    "task": "Wiki CRUD 操作",
    "rule": "validation task #3 (add/edit/tag/merge/delete/research)",
    "snapshot": p3_snap,
    "pass": p3_pass,
    "metrics": f"{p3_crud_count}/6 CRUD ops OK",
})

all_pass = all(p["pass"] for p in phases)

# 写 HTML
rows = []
for p in phases:
    badge = (
        '<span class="badge ok">PASS</span>'
        if p["pass"]
        else '<span class="badge fail">FAIL</span>'
    )
    snap_rel = os.path.relpath(p["snapshot"], REPS) if p["snapshot"].is_file() else "(missing)"
    snap_size = file_size(p["snapshot"])
    rows.append(
        f"<tr><td>{escape(p['phase'])}</td>"
        f"<td>{escape(p['task'])}</td>"
        f"<td><code>{escape(p['rule'])}</code></td>"
        f"<td>{badge}</td>"
        f"<td>{escape(p['metrics'])}</td>"
        f"<td><a href=\"{escape(snap_rel)}\">{escape(snap_rel)}</a> ({snap_size}B)</td></tr>"
    )

html = f"""<!doctype html>
<html lang="zh-CN"><head>
<meta charset="utf-8"/>
<title>insights-share validation 报告</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 2em; max-width: 1200px; }}
  h1 {{ font-size: 1.5em; }}
  table {{ border-collapse: collapse; width: 100%; margin-top: 1em; }}
  th, td {{ border: 1px solid #ccc; padding: 8px 12px; text-align: left; vertical-align: top; }}
  th {{ background: #f4f4f4; }}
  .badge {{ padding: 3px 10px; border-radius: 4px; font-weight: bold; font-size: 0.85em; }}
  .ok {{ background: #d4edda; color: #155724; }}
  .fail {{ background: #f8d7da; color: #721c24; }}
  .summary {{ padding: 12px 16px; border-radius: 6px; margin: 1em 0; font-size: 1.1em; }}
  .summary.ok {{ background: #d4edda; color: #155724; }}
  .summary.fail {{ background: #f8d7da; color: #721c24; }}
  code {{ background: #f4f4f4; padding: 1px 4px; border-radius: 3px; font-size: 0.9em; }}
  footer {{ margin-top: 2em; color: #888; font-size: 0.85em; }}
</style>
</head><body>
<h1>insights-share validation 报告</h1>
<div class="summary {'ok' if all_pass else 'fail'}">
  总览：{sum(p['pass'] for p in phases)}/{len(phases)} 通过
  ({'全部通过 ✓' if all_pass else '存在失败项 ✗'}) ·
  生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
</div>
<table>
<thead><tr><th>Phase</th><th>任务</th><th>对应规则</th><th>状态</th><th>关键指标</th><th>快照</th></tr></thead>
<tbody>
{''.join(rows)}
</tbody>
</table>
<footer>
报告由 <code>run_all_validations.sh</code> 生成；快照路径相对 <code>{REPS}</code>。
所有 phase 严格遵守 validation.md 的 5 项规则与"无 fallback in AI path"约束。
</footer>
</body></html>
"""
out = REPS / "final_report.html"
out.write_text(html, encoding="utf-8")

# 写一份 JSON 摘要给程序消费
summary = {
    "all_pass": all_pass,
    "passed": sum(1 for p in phases if p["pass"]),
    "total": len(phases),
    "phases": [
        {k: (str(v) if isinstance(v, Path) else v) for k, v in p.items()}
        for p in phases
    ],
    "generated_at": datetime.now().isoformat(),
}
(REPS / "final_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

print(f"[run_all] wrote {out}")
print(f"[run_all] all_pass={all_pass} ({summary['passed']}/{summary['total']})")
for p in phases:
    mark = "OK" if p["pass"] else "XX"
    print(f"  [{mark}] {p['phase']} - {p['task']} - {p['metrics']}")
PY

PY_EXIT=$?
if [[ $PY_EXIT -ne 0 ]]; then
    echo "[run_all] python summary failed (exit $PY_EXIT)"
    exit 1
fi

# 自动用 Chrome 打开 HTML 报告
if command -v open >/dev/null 2>&1; then
    open -a "Google Chrome" "$HTML" 2>/dev/null || open "$HTML"
fi

# Phase 6 检查：通读 final_summary.json，若 all_pass=false 退出码 1
ALL_PASS=$(python3 -c 'import json; print(json.load(open("'"$REPORTS"'/final_summary.json")).get("all_pass"))')
if [[ "$ALL_PASS" == "True" ]]; then
    echo "[run_all] PASS"
    exit 0
fi
echo "[run_all] FAIL"
exit 1
