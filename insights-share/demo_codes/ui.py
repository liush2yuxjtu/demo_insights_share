"""ANSI 终端辅助：颜色、面板、banner、spinner、timer、diff badge。

纯 stdlib，无 rich/colorama 依赖。
对非 TTY 输出自动降级为纯文本。
"""
from __future__ import annotations

import sys
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass

_ANSI = {
    "red": "\033[31m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "blue": "\033[34m",
    "magenta": "\033[35m",
    "cyan": "\033[36m",
    "dim": "\033[2m",
    "bold": "\033[1m",
}
_RESET = "\033[0m"

_WIDTH = 80


def _tty() -> bool:
    try:
        return sys.stdout.isatty()
    except Exception:
        return False


def color(text: str, c: str) -> str:
    if not _tty() or c not in _ANSI:
        return text
    return f"{_ANSI[c]}{text}{_RESET}"


def _visible_len(s: str) -> int:
    out, i = 0, 0
    while i < len(s):
        if s[i] == "\033":
            while i < len(s) and s[i] != "m":
                i += 1
            i += 1
            continue
        out += 1
        i += 1
    return out


def panel(title: str, body: str, color_name: str = "green") -> str:
    lines = body.splitlines() or [""]
    inner = max(_visible_len(title) + 2, max(_visible_len(ln) for ln in lines))
    inner = min(inner, _WIDTH - 4)
    top = "+" + "-" * (inner + 2) + "+"
    title_line = "| " + title + " " * (inner - _visible_len(title)) + " |"
    body_lines = []
    for ln in lines:
        pad = inner - _visible_len(ln)
        body_lines.append("| " + ln + " " * max(pad, 0) + " |")
    sep = "+" + "-" * (inner + 2) + "+"
    raw = "\n".join([top, title_line, sep, *body_lines, top])
    return color(raw, color_name)


def banner(text: str) -> str:
    pad = max(0, (_WIDTH - _visible_len(text)) // 2)
    line = " " * pad + text
    return color(line, "bold")


class _Spinner:
    FRAMES = "|/-\\"

    def __init__(self, msg: str):
        self.msg = msg
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def _run(self) -> None:
        i = 0
        while not self._stop.is_set():
            frame = self.FRAMES[i % len(self.FRAMES)]
            if _tty():
                sys.stdout.write(f"\r{frame} {self.msg}")
                sys.stdout.flush()
            i += 1
            self._stop.wait(0.1)

    def start(self) -> None:
        if not _tty():
            sys.stdout.write(self.msg + "\n")
            sys.stdout.flush()
            return
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=0.5)
        if _tty():
            sys.stdout.write("\r" + " " * (len(self.msg) + 4) + "\r")
            sys.stdout.flush()


@contextmanager
def spinner(msg: str):
    sp = _Spinner(msg)
    sp.start()
    try:
        yield sp
    finally:
        sp.stop()


@dataclass
class _Timer:
    start: float = 0.0
    elapsed: float = 0.0


@contextmanager
def timer():
    t = _Timer(start=time.monotonic())
    try:
        yield t
    finally:
        t.elapsed = time.monotonic() - t.start


def diff_badge(before: str, after: str) -> str:
    delta = len(after) - len(before)
    sign = "+" if delta >= 0 else ""
    label = f"[diff {sign}{delta} chars, {len(before)}->{len(after)}]"
    return color(label, "cyan")
