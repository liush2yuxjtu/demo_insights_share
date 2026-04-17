from __future__ import annotations

import os
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


_ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]")


def _clean_terminal_text(text: str) -> str:
    cleaned = text.replace("\r", "")
    while True:
        collapsed = re.sub(r".\x08", "", cleaned)
        if collapsed == cleaned:
            break
        cleaned = collapsed
    cleaned = _ANSI_RE.sub("", cleaned)
    return cleaned.replace("\u00a0", " ")


class TerminalBridge:
    def __init__(self, app_root: Path) -> None:
        self.app_root = Path(app_root)
        self.repo_root = self.app_root.parent
        self.tmux_bin = shutil.which("tmux")
        self.tmux_env = dict(os.environ)
        if not self.tmux_env.get("TMUX_TMPDIR") and self.tmux_env.get("TMPDIR"):
            self.tmux_env["TMUX_TMPDIR"] = self.tmux_env["TMPDIR"]

    def _run_tmux(self, args: list[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [self.tmux_bin or "tmux", *args],
            capture_output=True,
            text=True,
            check=False,
            env=self.tmux_env,
        )

    def _transcript_specs(self) -> list[tuple[str, str, Path]]:
        root = self.repo_root
        app = self.app_root
        return [
            ("examples/B_with.human.md", "A/B WITH 导出", root / "examples" / "B_with.human.md"),
            ("examples/A_without.human.md", "A/B WITHOUT 导出", root / "examples" / "A_without.human.md"),
            ("export_template.txt", "导出模板", root / "export_template.txt"),
            (
                "validation/reports/deliverables/claude_export_WITH.txt",
                "Validation WITH 导出",
                app / "validation" / "reports" / "deliverables" / "claude_export_WITH.txt",
            ),
            (
                "validation/reports/deliverables/claude_export_WITHOUT.txt",
                "Validation WITHOUT 导出",
                app / "validation" / "reports" / "deliverables" / "claude_export_WITHOUT.txt",
            ),
            (
                "validation/reports/deliverables/server_host_export.txt",
                "Server Host 导出",
                app / "validation" / "reports" / "deliverables" / "server_host_export.txt",
            ),
            (
                "validation/reports/deliverables/wiki_upload.txt",
                "Wiki Upload 导出",
                app / "validation" / "reports" / "deliverables" / "wiki_upload.txt",
            ),
        ]

    def list_transcripts(self) -> list[dict[str, Any]]:
        transcripts: list[dict[str, Any]] = []
        for transcript_id, label, path in self._transcript_specs():
            if not path.is_file():
                continue
            stat = path.stat()
            transcripts.append(
                {
                    "id": transcript_id,
                    "label": label,
                    "path": str(path),
                    "mtime": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "size": stat.st_size,
                }
            )
        transcripts.sort(key=lambda item: str(item["mtime"]), reverse=True)
        return transcripts

    def read_transcript(self, transcript_id: str) -> dict[str, Any] | None:
        for item in self.list_transcripts():
            if item["id"] != transcript_id:
                continue
            path = Path(item["path"])
            return {
                **item,
                "content": path.read_text(encoding="utf-8", errors="replace"),
            }
        return None

    def list_tmux_panes(self) -> dict[str, Any]:
        if not self.tmux_bin:
            return {"available": False, "connected": False, "panes": []}

        proc = self._run_tmux(
            [
                "list-panes",
                "-a",
                "-F",
                "#{session_name}:#{window_index}.#{pane_index}\t#{session_name}\t#{window_name}\t#{pane_current_command}\t#{pane_title}",
            ]
        )
        if proc.returncode != 0:
            return {"available": True, "connected": False, "panes": []}

        panes: list[dict[str, Any]] = []
        for line in proc.stdout.splitlines():
            parts = line.split("\t")
            if len(parts) != 5:
                continue
            panes.append(
                {
                    "target": parts[0],
                    "session": parts[1],
                    "window": parts[2],
                    "command": parts[3],
                    "title": parts[4],
                }
            )
        return {"available": True, "connected": True, "panes": panes}

    def capture_tmux(self, target: str, *, lines: int = 240) -> dict[str, Any]:
        proc = self._run_tmux(["capture-pane", "-p", "-J", "-S", f"-{max(20, min(lines, 2000))}", "-t", target])
        if proc.returncode != 0:
            raise ValueError(proc.stderr.strip() or f"capture failed for {target}")
        return {
            "target": target,
            "content": _clean_terminal_text(proc.stdout),
            "updated_at": datetime.now().isoformat(),
        }

    def send_tmux_input(
        self,
        target: str,
        *,
        text: str | None = None,
        enter: bool = True,
        control: str | None = None,
    ) -> None:
        if control:
            key = {"c": "C-c", "z": "C-z", "l": "C-l"}.get(control.lower())
            if not key:
                raise ValueError(f"unsupported control: {control}")
            proc = self._run_tmux(["send-keys", "-t", target, key])
            if proc.returncode != 0:
                raise ValueError(proc.stderr.strip() or f"send-keys failed for {target}")
            return

        payload = (text or "").strip("\n")
        if not payload:
            raise ValueError("empty input")
        proc = self._run_tmux(["send-keys", "-t", target, "-l", payload])
        if proc.returncode != 0:
            raise ValueError(proc.stderr.strip() or f"send-keys failed for {target}")
        if enter:
            proc = self._run_tmux(["send-keys", "-t", target, "Enter"])
            if proc.returncode != 0:
                raise ValueError(proc.stderr.strip() or f"send Enter failed for {target}")

    def tmux_summary(self, *, input_enabled: bool) -> dict[str, Any]:
        tmux = self.list_tmux_panes()
        tmux["input_enabled"] = input_enabled
        return tmux
