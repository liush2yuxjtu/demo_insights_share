#!/usr/bin/env bash
# P7 验证汇总：
# - 路径从脚本自身位置解析，不依赖开发者 home 目录
# - 默认仍写兼容报告路径：
#   insights-share/validation/reports/final_report.html
# - 默认执行确定性必需门；昂贵或强本机依赖的门通过环境变量显式开启。

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
REPORTS_DIR="${VALIDATION_REPORTS_DIR:-${SCRIPT_DIR}/reports}"
mkdir -p "${REPORTS_DIR}"

export VALIDATION_SCRIPT_DIR="${SCRIPT_DIR}"
export VALIDATION_REPO_ROOT="${REPO_ROOT}"
export VALIDATION_REPORTS_DIR="${REPORTS_DIR}"

python3 - <<'PY'
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from html import escape
from pathlib import Path
from time import monotonic


SCRIPT_DIR = Path(os.environ["VALIDATION_SCRIPT_DIR"])
REPO_ROOT = Path(os.environ["VALIDATION_REPO_ROOT"])
REPORTS_DIR = Path(os.environ["VALIDATION_REPORTS_DIR"])
GATE_LOG_DIR = REPORTS_DIR / "gate_logs"
HTML_PATH = REPORTS_DIR / "final_report.html"
SUMMARY_PATH = REPORTS_DIR / "final_summary.json"


def env_value(name: str, default: str) -> str:
    value = os.environ.get(name)
    if value is None or value == "":
        return default
    return value


def truthy(value: str) -> bool:
    return value.lower() in {"1", "true", "yes", "on"}


def falsey(value: str) -> bool:
    return value.lower() in {"0", "false", "no", "off"}


def command_exists(name: str) -> bool:
    return shutil.which(name) is not None


def gate_enabled(mode: str, auto_check=None) -> tuple[bool, str]:
    if truthy(mode):
        return True, "enabled"
    if falsey(mode):
        return False, f"disabled by env value {mode!r}"
    if mode == "auto":
        if auto_check is None:
            return False, "auto mode has no availability check"
        ok, reason = auto_check()
        return ok, reason
    return False, f"invalid env value {mode!r}"


def run_gate(
    *,
    gate_id: str,
    title: str,
    expectation: str,
    command: list[str],
    cwd: Path = REPO_ROOT,
    mode: str = "1",
    auto_check=None,
    required_when_enabled: bool = True,
) -> dict:
    enabled, enable_reason = gate_enabled(mode, auto_check)
    log_path = GATE_LOG_DIR / f"{gate_id.lower().replace('-', '_')}.log"
    gate = {
        "id": gate_id,
        "title": title,
        "expectation": expectation,
        "command": command,
        "cwd": str(cwd),
        "mode": mode,
        "enabled": enabled,
        "required": bool(enabled and required_when_enabled),
        "status": "SKIP",
        "exit_code": None,
        "duration_ms": 0,
        "log": str(log_path),
        "reason": enable_reason,
    }

    if not enabled:
        log_path.write_text(f"[{gate_id}] SKIP: {enable_reason}\n", encoding="utf-8")
        return gate

    started = monotonic()
    proc = subprocess.run(
        command,
        cwd=cwd,
        env=os.environ.copy(),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    gate["duration_ms"] = int((monotonic() - started) * 1000)
    gate["exit_code"] = proc.returncode
    gate["status"] = "PASS" if proc.returncode == 0 else "FAIL"
    gate["reason"] = "exit 0" if proc.returncode == 0 else f"exit {proc.returncode}"

    header = [
        f"[{gate_id}] {gate['status']}",
        f"cwd={cwd}",
        "command=" + " ".join(command),
        f"duration_ms={gate['duration_ms']}",
        "",
    ]
    log_path.write_text("\n".join(header) + proc.stdout, encoding="utf-8")
    return gate


def start_demo_auto_check() -> tuple[bool, str]:
    missing = [cmd for cmd in ("claude", "tmux") if not command_exists(cmd)]
    if missing:
        return False, "auto skip: missing " + ", ".join(missing)
    return True, "auto enabled: claude and tmux are available"


def node_auto_check() -> tuple[bool, str]:
    missing = [cmd for cmd in ("npm", "node") if not command_exists(cmd)]
    if missing:
        return False, "auto skip: missing " + ", ".join(missing)
    return True, "auto enabled: npm and node are available"


def tmux_auto_check() -> tuple[bool, str]:
    if not command_exists("tmux"):
        return False, "auto skip: missing tmux"
    return True, "auto enabled: tmux is available"


def main() -> int:
    GATE_LOG_DIR.mkdir(parents=True, exist_ok=True)

    run_start_demo_dry = env_value(
        "RUN_START_DEMO_DRY",
        env_value("RUN_START_DEMO", "0"),
    )
    gates = [
        run_gate(
            gate_id="P0",
            title="gstack 环境门",
            expectation="~/.claude/skills/gstack/bin 必须存在",
            command=["bash", "-lc", "test -d ~/.claude/skills/gstack/bin"],
        ),
        run_gate(
            gate_id="P3",
            title="pytest 合同门",
            expectation="start/plugin/release/statusline/topic/adoption 合同测试可执行",
            command=["bash", "insights-share/validation/run_contract_tests.sh"],
            mode=env_value("RUN_CONTRACT_TESTS", "1"),
        ),
        run_gate(
            gate_id="AP-1",
            title="adoption proof 门",
            expectation="clean-machine install、first relevant hit、first publish、day-2 return 四信号",
            command=["bash", "insights-share/validation/run_adoption_proof.sh"],
            mode=env_value("RUN_ADOPTION_PROOF", "1"),
        ),
        run_gate(
            gate_id="P1",
            title="start.demo.sh dry-run hero",
            expectation="沙箱、plugin install 与脚本结构可复验",
            command=["bash", "start.demo.sh", "--dry-run"],
            mode=run_start_demo_dry,
            auto_check=start_demo_auto_check,
            required_when_enabled=True,
        ),
        run_gate(
            gate_id="P2",
            title="start.demo.sh live hero",
            expectation="PM 可见实机闭环，默认关闭以避免误起交互 session",
            command=["bash", "start.demo.sh"],
            mode=env_value("RUN_START_DEMO_LIVE", "0"),
            auto_check=start_demo_auto_check,
            required_when_enabled=True,
        ),
        run_gate(
            gate_id="P4",
            title="Playwright handout record",
            expectation="录完整 user-flow mp4/console/manifest",
            command=["npm", "run", "handout:record"],
            cwd=SCRIPT_DIR,
            mode=env_value("RUN_HANDOUT_RECORD", "0"),
            auto_check=node_auto_check,
            required_when_enabled=True,
        ),
        run_gate(
            gate_id="P5",
            title="Playwright handout verify",
            expectation="回放 latest manifest 并门控退出码",
            command=["npm", "run", "handout:verify"],
            cwd=SCRIPT_DIR,
            mode=env_value("RUN_HANDOUT_VERIFY", "0"),
            auto_check=node_auto_check,
            required_when_enabled=True,
        ),
        run_gate(
            gate_id="P6",
            title="tmux start-script smoke",
            expectation="start.claude.sh / start.codex.sh 批量实机 smoke",
            command=["bash", "insights-share/validation/run_start_tmux_smoke.sh"],
            mode=env_value("RUN_TMUX_SMOKE", "0"),
            auto_check=tmux_auto_check,
            required_when_enabled=True,
        ),
    ]

    required_failures = [g for g in gates if g["required"] and g["status"] != "PASS"]
    p7_status = "PASS" if not required_failures else "FAIL"
    gates.append(
        {
            "id": "P7",
            "title": "validation aggregate report",
            "expectation": "生成 final_report.html / final_summary.json，并汇总当前 P0-P7 + AP-1 口径",
            "command": ["bash", "insights-share/validation/run_all_validations.sh"],
            "cwd": str(REPO_ROOT),
            "mode": "1",
            "enabled": True,
            "required": True,
            "status": p7_status,
            "exit_code": 0 if p7_status == "PASS" else 1,
            "duration_ms": 0,
            "log": "",
            "reason": "required gates passed" if p7_status == "PASS" else "required gate failure",
        }
    )

    required_total = sum(1 for g in gates if g["required"])
    required_passed = sum(1 for g in gates if g["required"] and g["status"] == "PASS")
    enabled_total = sum(1 for g in gates if g["enabled"])
    enabled_passed = sum(1 for g in gates if g["enabled"] and g["status"] == "PASS")
    all_required_pass = required_passed == required_total

    summary = {
        "schema_version": "validation-aggregate/v2",
        "repo_root": str(REPO_ROOT),
        "reports_dir": str(REPORTS_DIR),
        "final_report": str(HTML_PATH),
        "all_pass": all_required_pass,
        "required_passed": required_passed,
        "required_total": required_total,
        "enabled_passed": enabled_passed,
        "enabled_total": enabled_total,
        "generated_at": datetime.now().isoformat(),
        "env_flags": {
            "RUN_CONTRACT_TESTS": env_value("RUN_CONTRACT_TESTS", "1"),
            "RUN_ADOPTION_PROOF": env_value("RUN_ADOPTION_PROOF", "1"),
            "RUN_START_DEMO_DRY": run_start_demo_dry,
            "RUN_START_DEMO_LIVE": env_value("RUN_START_DEMO_LIVE", "0"),
            "RUN_HANDOUT_RECORD": env_value("RUN_HANDOUT_RECORD", "0"),
            "RUN_HANDOUT_VERIFY": env_value("RUN_HANDOUT_VERIFY", "0"),
            "RUN_TMUX_SMOKE": env_value("RUN_TMUX_SMOKE", "0"),
        },
        "gates": gates,
    }
    SUMMARY_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    HTML_PATH.write_text(render_html(summary), encoding="utf-8")

    print(f"[run_all] wrote {HTML_PATH}")
    print(
        "[run_all] required_pass="
        f"{all_required_pass} ({required_passed}/{required_total}); "
        f"enabled={enabled_passed}/{enabled_total}"
    )
    for gate in gates:
        print(f"  [{gate['status']}] {gate['id']} - {gate['title']} - {gate['reason']}")

    if truthy(env_value("RUN_OPEN_REPORT", "0")) and sys.platform == "darwin":
        subprocess.run(["open", str(HTML_PATH)], check=False)

    return 0 if all_required_pass else 1


def render_html(summary: dict) -> str:
    rows = []
    for gate in summary["gates"]:
        status = gate["status"]
        cls = {
            "PASS": "ok",
            "FAIL": "fail",
            "SKIP": "skip",
        }.get(status, "skip")
        log_cell = ""
        if gate.get("log"):
            try:
                rel_log = os.path.relpath(gate["log"], REPORTS_DIR)
            except ValueError:
                rel_log = gate["log"]
            log_cell = f'<a href="{escape(rel_log)}">{escape(rel_log)}</a>'
        rows.append(
            "<tr>"
            f"<td>{escape(gate['id'])}</td>"
            f"<td>{escape(gate['title'])}</td>"
            f"<td>{escape(gate['expectation'])}</td>"
            f'<td><span class="badge {cls}">{escape(status)}</span></td>'
            f"<td>{'yes' if gate['required'] else 'no'}</td>"
            f"<td>{escape(str(gate.get('duration_ms', 0)))}ms</td>"
            f"<td><code>{escape(' '.join(gate['command']))}</code></td>"
            f"<td>{escape(gate['reason'])}</td>"
            f"<td>{log_cell}</td>"
            "</tr>"
        )

    flags = "\n".join(
        f"{name}={value}" for name, value in summary["env_flags"].items()
    )
    summary_cls = "ok" if summary["all_pass"] else "fail"
    summary_text = (
        f"required {summary['required_passed']}/{summary['required_total']} PASS; "
        f"enabled {summary['enabled_passed']}/{summary['enabled_total']} PASS"
    )
    return f"""<!doctype html>
<html lang="zh-CN"><head>
<meta charset="utf-8"/>
<title>insights-share 验证汇总</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 2em; max-width: 1280px; }}
  h1 {{ font-size: 1.5em; margin-bottom: 0.2em; }}
  table {{ border-collapse: collapse; width: 100%; margin-top: 1em; }}
  th, td {{ border: 1px solid #ccc; padding: 8px 10px; text-align: left; vertical-align: top; }}
  th {{ background: #f4f4f4; }}
  .badge {{ display: inline-block; min-width: 44px; padding: 3px 8px; border-radius: 4px; font-weight: 700; font-size: 0.85em; text-align: center; }}
  .ok {{ background: #d4edda; color: #155724; }}
  .fail {{ background: #f8d7da; color: #721c24; }}
  .skip {{ background: #e2e3e5; color: #383d41; }}
  .summary {{ padding: 12px 16px; border-radius: 6px; margin: 1em 0; font-size: 1.05em; }}
  code, pre {{ background: #f4f4f4; padding: 2px 4px; border-radius: 3px; }}
  pre {{ padding: 10px 12px; overflow-x: auto; }}
  footer {{ margin-top: 2em; color: #666; font-size: 0.9em; }}
</style>
</head><body>
<h1>insights-share 验证汇总</h1>
<div class="summary {summary_cls}">
  总览：{escape(summary_text)} · 生成时间：{escape(summary['generated_at'])}
</div>
<p>
当前口径覆盖 P0-P7 与 AP-1 adoption proof。P0 / P3 / AP-1 默认执行；
P1/P2/P4/P5/P6 是本机增强门，按环境变量开启。
</p>
<pre>{escape(flags)}</pre>
<table>
<thead><tr><th>Gate</th><th>名称</th><th>期望</th><th>状态</th><th>Required</th><th>耗时</th><th>命令</th><th>原因</th><th>日志</th></tr></thead>
<tbody>
{''.join(rows)}
</tbody>
</table>
<footer>
报告由 <code>run_all_validations.sh</code> 生成；默认输出保持在
<code>insights-share/validation/reports/final_report.html</code>。
完整本机增强门示例：
<code>RUN_START_DEMO_DRY=1 RUN_HANDOUT_VERIFY=1 RUN_TMUX_SMOKE=1 bash insights-share/validation/run_all_validations.sh</code>
</footer>
</body></html>
"""


raise SystemExit(main())
PY
