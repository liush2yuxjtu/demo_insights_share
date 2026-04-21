# inbox-review — 收件箱 drain → AskUserQuestion → decide 一键流程

**用法**: `/inbox-review [inbox-dir]`

`inbox-dir` 默认 `docs/user_complaints_inbox`（相对于 repo 根目录）。

---

## 执行步骤

1. **Drain**：用 Bash 运行 `main_drain.py`，获取 pending proposals。
2. **状态报告**：输出 crash/summary/checkpoint 状态。
3. **逐条决策**：对 batch 里每条 proposal 调用 `AskUserQuestion`，选 Approve/Deny/Defer。
4. **写入决策**：每条答案立即调用 `main_decide.py` 写入 `decisions/<pid>.json`。
5. **循环友好**：无 pending 时输出 `[inbox-review] no pending proposals`，退出干净（方便 /loop 轮询）。

---

## Claude 执行指令

执行本命令时请严格按以下顺序操作：

### Step A — 确定路径

```bash
REPO_ROOT="$(git -C "$(dirname "$0")" rev-parse --show-toplevel 2>/dev/null || pwd)"
```

- `INBOX_DIR` = `$ARGUMENTS` 若非空，否则 `$REPO_ROOT/docs/user_complaints_inbox`
- 若 `$ARGUMENTS` 是相对路径，拼到 `$REPO_ROOT` 下。
- `LOOP_DIR` = `$REPO_ROOT/.claude/roleplan_agents/inbox_loop`
- `VENV_PY` = `$REPO_ROOT/insights-share/demo_codes/.venv/bin/python`（存在则用，否则 `python3`）

### Step B — 运行 drain

```bash
cd "$LOOP_DIR"
"$PY" main_drain.py --inbox-dir "$INBOX_DIR" --batch 4
```

解析 JSON 输出，提取：
- `total_pending`
- `batch`（proposal 列表，每条含 `proposal_id`, `title`, `rationale`, `impact`, `affected_roles`）
- `crash_detected`
- `summary_json_exists`
- `latest_checkpoint_iter`

### Step C — 状态摘要（文字输出给用户）

输出一行：
```
[inbox-review] 状态: pending={total_pending} | crash={crash_detected} | summary={summary_json_exists} | latest_iter={latest_checkpoint_iter}
```

若 `crash_detected=true`，警告用户：
```
⚠ subagent 疑似 crash（summary.json 缺失且最新 checkpoint 已超 30 分钟）。可用 launch.sh --resume 重启。
```

若 `total_pending == 0`：
```
[inbox-review] no pending proposals — 无需操作。
```
然后停止（不再调用 AskUserQuestion）。

### Step D — 逐条 AskUserQuestion

对 `batch` 中每条 proposal（最多 4 条），调用一次 **AskUserQuestion**：

- `question`: `"[{impact}] {title} — {rationale}\n\n如何处理这条 proposal？"`  
  （其中 `{impact}`, `{title}`, `{rationale}` 替换为实际值）
- `header`: `"Proposal 决策"`
- `options`:
  - `{ "label": "Approve", "description": "接受这条升级建议，写入 approved 状态" }`
  - `{ "label": "Deny",    "description": "拒绝，写入 denied 状态，不再出现" }`
  - `{ "label": "Defer",   "description": "推迟，最多 3 次后自动转 denied" }`

每次 AskUserQuestion 返回后，**立即** 执行 Step E，再处理下一条。

### Step E — 写入决策

```bash
cd "$LOOP_DIR"
"$PY" main_decide.py \
    --inbox-dir "$INBOX_DIR" \
    --proposal-id "$PID" \
    --answer "$ANSWER"
```

- `$PID` = 当前 proposal 的 `proposal_id`
- `$ANSWER` = AskUserQuestion 返回的 label（`Approve` / `Deny` / `Defer`）

输出一行确认：`[inbox-review] {pid} → {answer}`

### Step F — 完成摘要

所有 batch 处理完后输出：

```
[inbox-review] 本轮处理 {N} 条。remaining_pending 可再跑一次 /inbox-review 查看。
```

---

## /loop 用法示例

```bash
# 每 30 秒轮询一次
/loop 30s /inbox-review

# 或自定义路径
/loop 60s /inbox-review docs/my_inbox
```

无 pending 时 loop 安静过，有新 proposal 时自动弹出 AskUserQuestion。
