"""共享的 claude_agent_sdk 初始化代码。供 adapter.py / search_agent.py 复用。

只做一件事：从 demo_codes/.env 加载 MiniMax 凭据，然后导出 SDK 类。
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# 模块加载时只 load 一次
_ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(_ENV_PATH)


def get_haiku_model() -> str:
    """返回当前 .env 中配置的 haiku 模型名（默认 MiniMax-M2.7-highspeed）。"""
    return os.environ.get("ANTHROPIC_DEFAULT_HAIKU_MODEL", "MiniMax-M2.7-highspeed")


def env_summary() -> str:
    """返回脱敏的 env 摘要，便于日志打印。"""
    token = os.environ.get("ANTHROPIC_AUTH_TOKEN", "")
    masked = (token[:8] + "..." + token[-4:]) if len(token) > 16 else "(unset)"
    return (
        f"ANTHROPIC_AUTH_TOKEN={masked} "
        f"ANTHROPIC_BASE_URL={os.environ.get('ANTHROPIC_BASE_URL','(unset)')} "
        f"HAIKU={get_haiku_model()}"
    )
