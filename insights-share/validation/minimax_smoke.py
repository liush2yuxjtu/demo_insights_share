"""MiniMax 凭据烟测：最小 claude_agent_sdk.query 调用。

用途：Phase 0 预检，在开始正式 validation 之前确认 .env 中的 MiniMax
token 真实可用、可完成一次端到端 AI 调用。

**严禁 fallback**：任何异常直接 raise，退出码非 0。
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv

DEMO_CODES = Path(__file__).resolve().parent.parent / "demo_codes"
load_dotenv(DEMO_CODES / ".env")

from claude_agent_sdk import (  # noqa: E402
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    query,
)


async def main() -> int:
    options = ClaudeAgentOptions(
        permission_mode="dontAsk",
        allowed_tools=[],
        max_turns=1,
        extra_args={"bare": None},
    )
    prompt = "Reply with the single word PONG (all caps) and nothing else."
    collected: list[str] = []
    async for message in query(prompt=prompt, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                text = getattr(block, "text", None)
                if text:
                    collected.append(text)
        elif isinstance(message, ResultMessage):
            final = getattr(message, "result", None)
            if final:
                collected.append(str(final))

    raw = "\n".join(collected).strip()
    if not raw:
        print("[SMOKE FAIL] empty response from MiniMax", file=sys.stderr)
        return 1
    print(f"[SMOKE OK] response_len={len(raw)} preview={raw[:80]!r}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
