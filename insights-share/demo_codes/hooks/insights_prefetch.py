"""UserPromptSubmit hook 调用的轻量预热脚本。

每次 Bob 按下回车后,后台静默调用本脚本:
1. GET http://127.0.0.1:7821/insights 拿全量卡片
2. 调 insights_cache.persist(card) 把每张卡片落盘到 ~/.cache/insights-wiki/

整个过程对用户完全无感:
- 任何异常都吃掉(LAN daemon 没起、网络超时、权限问题),退出码始终为 0
- 不写任何 stdout(避免污染 hook 协议)
- 不发额外通知

注意:本脚本只在 UserPromptSubmit 阶段跑,严禁在 Stop hook 阶段复用。
"""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

DEMO_CODES = Path(__file__).resolve().parent.parent
DEFAULT_WIKI = "http://127.0.0.1:7821"
TIMEOUT_SECONDS = 2.0


def _silent_main() -> int:
    try:
        sys.path.insert(0, str(DEMO_CODES / "hooks"))
        from insights_cache import persist  # noqa: E402

        url = f"{DEFAULT_WIKI}/insights"
        with urllib.request.urlopen(url, timeout=TIMEOUT_SECONDS) as resp:
            payload = json.loads(resp.read().decode("utf-8"))

        cards = payload.get("cards") or []
        for card in cards:
            if isinstance(card, dict):
                persist(card)
    except (
        urllib.error.URLError,
        urllib.error.HTTPError,
        TimeoutError,
        ConnectionError,
        json.JSONDecodeError,
        OSError,
    ):
        # 静默退出,绝不打断用户输入
        return 0
    except Exception:
        # 兜底:任何意外都不能让 hook 失败而打断 prompt 提交
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(_silent_main())
