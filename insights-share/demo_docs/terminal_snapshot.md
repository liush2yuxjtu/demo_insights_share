# Terminal Snapshot

本文档记录 `run_demo.sh` 与 `insights_cli.py solve` 的实际捕获运行（已剥除 ANSI 控制序列）。

捕获环境：
- 日期：2026-04-13
- 路径：`/Users/m1/projects/demos/insights-share/demo_codes`
- 代理绕行：`NO_PROXY=127.0.0.1,localhost`（本机 127.0.0.1 HTTP 不走 socks5 代理 7897）
- Python：pyenv 3.12.0

断言摘要：
- `/healthz` 返回 `{"ok": true}`
- `/search?q=postgres+pool&k=3` 首个 hit id == `alice-pgpool-2026-04-10`
- `solve --no-ai` 退出码 0
- `solve`（AI 路径）因 `.env` 占位 token 命中 adapter 的 fallback 分支，`AdapterResult(verdict="adopt", adapted_insight=...non-empty, diff_summary="fallback: Exception", confidence=0.82)`，退出码 0
- `bash run_demo.sh --no-ai` 退出码 0，trap EXIT 正确清理，无 `insights_cli` 残留进程

## 一键 demo（`bash run_demo.sh --no-ai`）

```text

[notice] A new release of pip is available: 23.2.1 -> 26.0.1
[notice] To update, run: pip install --upgrade pip
                          DEMO: Bob hits prod incident

restate: Our checkout API is timing out, postgres is rejecting new connections during the lunch spike

hot-loaded alice-pgpool-2026-04-10 from alice (score=0.0364)

+------------------------------------------------------------------------------+
| Set idle_in_transaction_session_timeout=30s and bump pool size to 2x worker count |
+------------------------------------------------------------------------------+
| raw (no-ai) confidence=0.82                                                  |
+------------------------------------------------------------------------------+

fast path: 0.0s (no-ai)   slow path baseline: ~62s

demo finished
```

## AI 路径（`solve` 命中 adapter → fallback，演示保底）

```text
                          DEMO: Bob hits prod incident

restate: Our checkout API is timing out, postgres is rejecting new connections during the lunch spike

hot-loaded alice-pgpool-2026-04-10 from alice (score=0.0364)

validating against your context...
Fatal error in message reader: Command failed with exit code 1 (exit code: 1)
Error output: Check stderr output for details
+------------------------------------------------------------------------------+
| Set idle_in_transaction_session_timeout=30s and bump pool size to 2x worker count |
+------------------------------------------------------------------------------+
| verdict=adopt confidence=0.82 diff=fallback: Exception                       |
+------------------------------------------------------------------------------+

fast path: 0.0s (adapter: 187.7s)   slow path baseline: ~62s
```

说明：AI 路径输出里的 `verdict=adopt confidence=0.82 diff=fallback: Exception` 是 `adapter.py` 的 try/except 分支——`claude_agent_sdk` 拉起 Claude CLI 子进程后因 MiniMax 鉴权失败抛 exception，adapter 将其转为合法 `AdapterResult(verdict="adopt", adapted_insight=card["fix"], diff_summary="fallback: Exception", confidence=0.82, latency_s=<测得墙钟>)`。这是 #5 任务描述里约定的 fallback 行为，端到端链路依然算通过。
