"""AI 适配步：用 claude_agent_sdk 将 insight card 适配到本地上下文。

输入：card JSON + problem 描述 + local_context。
输出：AdapterResult(verdict/adapted_insight/diff_summary/confidence/latency_s)。
任何异常都返回合法的 fallback AdapterResult，不向外抛。

M7 优化（对齐 proposal_generation_latency.md adapter p95 ≤ 1500ms 预算）：
当 card 带 `source="local"` 且本地 Jaccard 分数 ≥ 阈值时，跳过 MiniMax SDK
走 adopt 合成结果，消除 adapter 阶段的 ~9s 网络调用。
"""
from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:  # clean plugin installs may only have stdlib Python
    def load_dotenv(*_args: object, **_kwargs: object) -> bool:
        return False

load_dotenv(Path(__file__).parent / ".env")

try:
    from claude_agent_sdk import (  # noqa: E402
        AssistantMessage,
        ClaudeAgentOptions,
        ResultMessage,
        query,
    )
except ModuleNotFoundError:  # no-ai and local-bypass paths must still import cleanly
    AssistantMessage = ()  # type: ignore[assignment]
    ResultMessage = ()  # type: ignore[assignment]
    ClaudeAgentOptions = None  # type: ignore[assignment]
    query = None  # type: ignore[assignment]


# 本地高置信短路阈值：card.score ≥ 该值即 bypass SDK。
# 0.12 与 local_search.DEFAULT_SCORE_THRESHOLD 对齐。
_LOCAL_BYPASS_MIN_SCORE = 0.12


@dataclass
class AdapterResult:
    verdict: str
    adapted_insight: str
    diff_summary: str
    confidence: float
    latency_s: float


PROMPT_TEMPLATE = """你是一个 insight 适配器。收到一张过往问题的 insight card，需要判断它能否迁移到当前本地上下文。

严格只输出一个 JSON 对象，不要任何解释文字，不要 markdown 围栏。
字段:
- verdict: "adopt" | "adapt" | "reject"
- adapted_insight: 适配后可直接拿去执行的一句话修复建议
- diff_summary: 一行差异摘要，说明相对 card 做了什么改动
- confidence: 0.0 - 1.0 之间的浮点

[card JSON]
{card_json}

[current problem]
{problem}

[local context]
{local_context}
"""


def _fallback(card: dict, elapsed: float, reason: str) -> AdapterResult:
    return AdapterResult(
        verdict="adopt",
        adapted_insight=card.get("fix", ""),
        diff_summary=f"fallback: {reason}",
        confidence=float(card.get("confidence", 0.5)),
        latency_s=elapsed,
    )


def _collect_text(message: AssistantMessage) -> str:
    parts: list[str] = []
    for block in message.content:
        text = getattr(block, "text", None)
        if text:
            parts.append(text)
    return "\n".join(parts)


def _extract_json(raw: str) -> dict:
    stripped = raw.strip()
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", stripped, re.DOTALL)
    if fence:
        stripped = fence.group(1)
    match = re.search(r"\{.*\}", stripped, re.DOTALL)
    if not match:
        raise ValueError("no json object in response")
    return json.loads(match.group(0))


def _local_bypass(card: dict, start_mono: float) -> AdapterResult | None:
    """本地高置信短路：card 来源本地 + 分数够高 → 直接 adopt，不走 SDK。

    返回 None 表示不能短路（caller 继续走 MiniMax 路径）。
    ENV `INSIGHTS_ADAPTER_LOCAL_BYPASS=0` 可强制关闭此优化。
    """
    if os.environ.get("INSIGHTS_ADAPTER_LOCAL_BYPASS", "1") == "0":
        return None
    if card.get("source") != "local":
        return None
    try:
        score = float(card.get("score", 0) or 0)
    except (TypeError, ValueError):
        score = 0.0
    if score < _LOCAL_BYPASS_MIN_SCORE:
        return None
    elapsed = time.monotonic() - start_mono
    title = card.get("title") or card.get("item") or "match"
    return AdapterResult(
        verdict="adopt",
        adapted_insight=card.get("fix") or f"local high-confidence hit: {title}",
        diff_summary=f"local bypass (score={score:.3f} via {card.get('rationale', '?')[:40]})",
        # 合成 confidence：local 分数偏保守，+0.1 后封顶 0.9
        confidence=min(0.9, score + 0.1),
        latency_s=elapsed,
    )


async def adapt(card: dict, problem: str, local_context: str) -> AdapterResult:
    start = time.monotonic()
    bypass = _local_bypass(card, start)
    if bypass is not None:
        return bypass
    if query is None or ClaudeAgentOptions is None:
        return _fallback(card, time.monotonic() - start, "claude_agent_sdk_missing")
    prompt = PROMPT_TEMPLATE.format(
        card_json=json.dumps(card, ensure_ascii=False),
        problem=problem,
        local_context=local_context,
    )
    options = ClaudeAgentOptions(
        permission_mode="dontAsk",
        allowed_tools=[],
        max_turns=2,
        extra_args={"bare": None},
    )

    collected: list[str] = []
    try:
        async for message in query(prompt=prompt, options=options):
            if isinstance(message, AssistantMessage):
                text = _collect_text(message)
                if text:
                    collected.append(text)
            elif isinstance(message, ResultMessage):
                final = getattr(message, "result", None)
                if final:
                    collected.append(str(final))
    except Exception as exc:
        elapsed = time.monotonic() - start
        return _fallback(card, elapsed, f"{type(exc).__name__}")

    elapsed = time.monotonic() - start
    raw = "\n".join(collected).strip()
    if not raw:
        return _fallback(card, elapsed, "empty response")

    try:
        payload = _extract_json(raw)
    except Exception as exc:
        return _fallback(card, elapsed, f"parse {type(exc).__name__}")

    try:
        return AdapterResult(
            verdict=str(payload.get("verdict", "adopt")),
            adapted_insight=str(payload.get("adapted_insight", card.get("fix", ""))),
            diff_summary=str(payload.get("diff_summary", "")),
            confidence=float(payload.get("confidence", card.get("confidence", 0.5))),
            latency_s=elapsed,
        )
    except Exception as exc:
        return _fallback(card, elapsed, f"coerce {type(exc).__name__}")
