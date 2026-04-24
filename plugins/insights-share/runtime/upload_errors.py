"""批量回灌 error-pattern 卡片到 LAN insightsd。

silent-first：成功与失败都写 `~/.cache/insights-share/upload_errors.log`，
不向 stdout / stderr 打印，避免被 Stop hook / 后台 fire-and-forget 路径
调起时污染用户 TTY。

退出码：
- 0：全部成功
- 1：存在失败条目（详情去 log 文件里翻）
"""
from __future__ import annotations

import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BASE_URL = "http://192.168.22.42:7821"
LOG_PATH = Path.home() / ".cache" / "insights-share" / "upload_errors.log"

CARDS = [
    {"id": "m1-error-001", "title": "Glob Tool Unavailable in sdk-py: Bash ls Fallback", "author": "m1", "confidence": 0.85, "tags": ["error-pattern", "sdk-py", "Glob", "fallback", "tool-availability"], "status": "active", "applies_when": ["running inside sdk-py environment", "restricted toolset"], "do_not_apply_when": ["standard Claude Code session", "full tool access"], "topic_id": "error-patterns", "label": "bad", "label_note": "降级到 Bash ls -la 实现同类功能", "raw_log": None},
    {"id": "m1-error-002", "title": "localStorage Quota Exceeded: try/catch Guard Required", "author": "m1", "confidence": 0.87, "tags": ["localStorage", "quota", "error", "browser", "try-catch"], "status": "active", "applies_when": ["writing to localStorage in browser", "caching large datasets"], "do_not_apply_when": ["server-side storage", "small data only"], "topic_id": "error-patterns", "label": "bad", "label_note": "Always wrap localStorage writes in try/catch; check quota", "raw_log": None},
    {"id": "m1-error-003", "title": "Flood Fill Stack Overflow: Use BFS Instead", "author": "m1", "confidence": 0.89, "tags": ["flood-fill", "stack-overflow", "BFS", "canvas", "algorithm"], "status": "active", "applies_when": ["canvas flood fill implementation", "large grid traversal"], "do_not_apply_when": ["small grids where stack depth safe"], "topic_id": "error-patterns", "label": "bad", "label_note": "Replace recursive flood fill with iterative BFS queue", "raw_log": None},
    {"id": "m1-error-004", "title": "Zotero MCP Fallback: zotero_search 降级路径", "author": "m1", "confidence": 0.83, "tags": ["zotero", "MCP", "fallback", "降级"], "status": "active", "applies_when": ["Zotero MCP unavailable", "MCP tool failures"], "do_not_apply_when": ["Zotero API directly accessible"], "topic_id": "error-patterns", "label": "good", "label_note": "MCP tool fails → check manual API or skip", "raw_log": None},
    {"id": "m1-error-005", "title": "No such tool available: Glob — SDK-py Restriction", "author": "m1", "confidence": 0.82, "tags": ["sdk-py", "Glob", "tool-unavailable", "Claude Code"], "status": "active", "applies_when": ["sdk-py environment detection", "tool availability checks"], "do_not_apply_when": ["full Claude Code environment"], "topic_id": "error-patterns", "label": "bad", "label_note": "Glob not available in sdk-py; use Bash ls instead", "raw_log": None},
]


def _append_log(line: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with LOG_PATH.open("a", encoding="utf-8") as fh:
        fh.write(f"[{ts}] {line}\n")


def _post_card(card: dict) -> tuple[bool, str]:
    data = json.dumps(card).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE_URL}/insights",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=5.0) as resp:
            return True, resp.read().decode("utf-8", errors="replace")
    except Exception as exc:  # noqa: BLE001
        return False, f"{type(exc).__name__}: {exc}"


def main() -> int:
    failures = 0
    _append_log(f"batch_start cards={len(CARDS)} base={BASE_URL}")
    for card in CARDS:
        ok, detail = _post_card(card)
        if ok:
            _append_log(f"OK id={card['id']} resp={detail}")
        else:
            failures += 1
            _append_log(f"FAIL id={card['id']} err={detail}")
    _append_log(
        f"batch_end ok={len(CARDS) - failures} fail={failures} log={LOG_PATH}"
    )
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
