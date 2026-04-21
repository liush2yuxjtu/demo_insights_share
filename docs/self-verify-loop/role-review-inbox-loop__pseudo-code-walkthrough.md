# role-review-inbox loop — pseudo-code walkthrough

**目的**: 给进入这个 repo 的后来者 (包括被 compact 后重新加载的 agent) 一份"看完就能动手跑"的伪代码 + 真命令混合文档。

**关联文件**:

- 权威设计 (iter 4 shipped): [`self-verify-loop__demo_insights_share__main__role-review-inbox-loop__20260421-182231__forloop-run__iter4__shipped.md`](./self-verify-loop__demo_insights_share__main__role-review-inbox-loop__20260421-182231__forloop-run__iter4__shipped.md)
- 落地实现: [`.claude/roleplan_agents/inbox_loop/`](../../.claude/roleplan_agents/inbox_loop/)
- 落地说明: [`.claude/roleplan_agents/inbox_loop/README.md`](../../.claude/roleplan_agents/inbox_loop/README.md)
- 6 role prompts: [`.claude/roleplan_agents/prompt_*.md`](../../.claude/roleplan_agents/)

---

## 外层结构 (伪代码)

```text
# inputs
task              = "Review <artifact> for ship-readiness"
artifact_0        = <待审的 markdown/代码/设计>
roles             = [pm, oncall, tech_lead, newbie, curator, validator]
N                 = 5
inbox_dir         = docs/user_complaints_inbox/
judge             = ./judge.sh             # claudefast → haiku → claude fallback
ROLE_CONCURRENCY  = 2                       # 并行 role 上限, 防止 token 燃烧
DEFER_AFTER_K     = 3
MAX_PENDING       = 20

# state
artifact          = artifact_0
prior_ship_verdict = None
previously_shipped = False

for i in 1..N:
    # ---- step 1: ask 6 roles in parallel ----
    role_comments = {}
    ThreadPoolExecutor(max_workers=ROLE_CONCURRENCY) as pool:
        for role in roles:
            pool.submit(ask_one_role, role, i, artifact)
            # 每 role 写自己独立的 role_verdicts/{role}.jsonl (R1 single-writer)

    # ---- step 2: autofix via LLM judge ----
    fixed_or_nobug = llm_judge(autofix_prompt(task, artifact, role_comments))
    if fixed_or_nobug.startswith("FIXED:"):
        artifact_next = parse(fixed_or_nobug)
        append_jsonl(autofix_log.jsonl, {iter, diff, ts})
    else:
        artifact_next = artifact

    # ---- step 3: extract proposals — NO JUDGE ----
    raw = llm_extract(extract_prompt(role_comments))
    for d in json_parse(raw):
        if not schema_valid(d):           # ← non-LLM structural gate
            continue
        pid = sha256(task + "|" + d.title + "|" + d.rationale)[:16]
        append_jsonl(proposals_appended.jsonl, {pid, iter, d, ts})
    # step 3 绝不 break, 绝不问用户, 只 append

    # ---- ship verdict via LLM judge (忽略 step 3 内容) ----
    verdict = llm_judge(ship_prompt(task, artifact_next, role_comments))
    write_atomic(checkpoints/iter_{i}.json, {iter, artifact_next, verdict, ts})

    # ---- termination (free-text 阅读, 不做关键词 hack) ----
    if verdict_says_ship(verdict):              # 见下方 SHIP_MARKERS
        verdict_tag = "shipped"; break
    if verdict == prior_ship_verdict:           # 两轮自然语言一字不差相同
        verdict_tag = ("converged" if previously_shipped else "stuck"); break
    prior_ship_verdict = verdict
    previously_shipped = verdict_says_ship(verdict)
    artifact = artifact_next
else:
    verdict_tag = "maxed"

write_atomic(summary.json, {verdict_tag, iters_used, pending_hint, ...})
```

---

## LLM-as-judge 调用层 (真文件)

**`.claude/roleplan_agents/inbox_loop/judge.sh`**:

```bash
#!/usr/bin/env bash
set -uo pipefail
PROMPT="$(cat)"
[ -z "$PROMPT" ] && { echo "[judge] empty prompt" >&2; exit 2; }

try_layer() {
  local label="$1"; shift
  local out
  out="$(printf '%s' "$PROMPT" | "$@" 2>/dev/null)"
  local rc=$?
  if [ $rc -eq 0 ] && [ -n "$out" ]; then
    printf '%s' "$out"
    return 0
  fi
  echo "[judge] $label failed rc=$rc" >&2
  return 1
}

try_layer "claudefast"   /Users/m1/.local/bin/claudefast -p && exit 0
try_layer "claude-haiku" claude -p --model haiku           && exit 0
try_layer "claude-full"  claude -p                         && exit 0
echo "[judge] ALL LAYERS FAILED" >&2
exit 3
```

macOS 没有 `timeout` 命令; 依赖 `claudefast` 内部的 `API_TIMEOUT_MS=3000000`。

**Python 侧调用 (真 `subagent.py`)**:

```python
def llm_judge(prompt: str) -> str:
    result = subprocess.run(
        ["./judge.sh"],
        input=prompt,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"judge exit={result.returncode}")
    return result.stdout.strip()
```

---

## 3 个不同的 judge prompt 形状

### step 1 — 单个 role 评论 (×6, 并行)

```text
<贴 .claude/roleplan_agents/prompt_{role}.md 全文>

---
## review iter {i}

```markdown
{artifact}
```

Give your role-specific review in free text.
Separate concrete bugs from upgrade proposals.
```

每 role 写入 `role_verdicts/{role}.jsonl` (append-only, single-writer per file)。

### step 2 — autofix (LLM judge, 产出可执行修正)

```text
You are a bug-fix bot. Find only concrete bugs in the artifact below.

TASK:
{task}

ARTIFACT:
```
{artifact}
```

ROLE COMMENTS (for context, only the bug parts):
### pm
...
### oncall
...

If concrete bugs (code / logic / schema / contract / typo / path) exist, output:
FIXED:
<full rewritten artifact>

If none, output exactly: NOBUG

Ignore upgrade proposals; they belong to step 3.
```

Python 侧解析:

```python
verdict = llm_judge(autofix_prompt)
if verdict.startswith("FIXED:"):
    artifact_next = verdict[len("FIXED:"):].lstrip("\n")
    fixed = True
else:
    artifact_next = artifact
    fixed = False
```

### step 3 — extract-only (NO judge, 仍经 claudefast)

```text
Extract-only task. No judging, no scoring.

From the role comments below, extract each *upgrade proposal* into a JSON object with fields:
  title           (>=5 chars)
  rationale       (>=20 chars)
  impact          (exactly one of: low, medium, high)
  affected_roles  (array of role names)

Output a JSON array. Nothing else — no prose, no markdown fences.

ROLE COMMENTS:
{combined}
```

Python 侧解析 + **非 LLM** schema gate:

```python
raw = llm_extract(prompt)
match = re.search(r"\[[\s\S]*\]", raw)
designs = json.loads(match.group(0)) if match else []

for d in designs:
    if not schema_valid(d):    # ← pure Python; no LLM judge here
        continue                # ← spam dropped, user 永不看到格式垃圾
    pid = sha256(task + "|" + d["title"] + "|" + d["rationale"])[:16]
    append_jsonl(proposals_appended.jsonl, {pid, iter, d, ts})
```

**`schema_valid()` 实现要点** (`core.py`):

```python
REQUIRED_FIELDS = ("title", "rationale", "impact", "affected_roles")
VALID_IMPACT    = {"low", "medium", "high"}
INVALID_IMPACT  = {"", "minimal", "none", "n/a", "tbd"}

def schema_valid(d):
    if not isinstance(d, dict): return False
    for f in REQUIRED_FIELDS:
        if not d.get(f): return False
    impact = str(d["impact"]).strip().lower()
    if impact in INVALID_IMPACT or impact not in VALID_IMPACT: return False
    if len(d["title"].strip())     < 5:  return False
    if len(d["rationale"].strip()) < 20: return False
    if not isinstance(d["affected_roles"], list): return False
    if len(d["affected_roles"]) == 0: return False
    return True
```

**关键**: step 3 用 `claudefast -p` 只做**结构提取**, 不打分, 不判 ship/revise — 这就是 user spec "LLM-as-judge EXCEPT 3" 的准确落点。

### ship verdict (LLM judge, 终端裁决)

```text
TASK:
{task}

ARTIFACT (after autofix = {fixed}):
```
{artifact_next}
```

ROLE COMMENTS:
{combined}

Decide if this artifact is ready to ship.

IGNORE any upgrade proposals — those are user-side decisions filed to the
inbox and do not block shipping. Base decision on role bug-level feedback
plus whether autofix was applied.

Reply freely. Use 'ship-ready' or 'ready to ship' or 'no blockers' if and
only if you approve. Otherwise list concrete revisions.
```

---

## 怎么"读"verdict (不做硬编码关键词匹配)

```python
SHIP_MARKERS = (
    "ship-ready",
    "ship ready",
    "ready to ship",
    "no blockers",
    "可出货",
)

def verdict_says_ship(verdict: str) -> bool:
    lowered = verdict.lower()
    return any(marker in lowered for marker in SHIP_MARKERS)
```

MARKERS 是**裁判自然会用的短语**, 不是打分表, 不是正则。裁判列出具体修复清单时, 句中没有这些短语 → 判 revise。

---

## self-verify 的语义

循环每轮结束后, 都请**全新的、无记忆的 `claudefast -p`** 做裁判:

- 裁判不是关键词匹配器
- 裁判不是固定 schema 打分
- 裁判是自由文本 + 几个可读的 ship 短语
- 连续两轮 verdict 字面一字不差 → stuck 或 converged, 停止烧 token

配合 checkpoint 机制 (`checkpoints/iter_<N>.json` atomic rename), subagent crash 后用 `--resume` 可从最新 checkpoint 继续。

---

## 一次实际运行后 inbox 长这样 🦆

```text
docs/user_complaints_inbox/
├── role_verdicts/
│   ├── pm.jsonl              # N 行, 每行 = 一轮 pm 的 free-text 评论
│   ├── oncall.jsonl
│   ├── tech_lead.jsonl
│   ├── newbie.jsonl
│   ├── curator.jsonl
│   └── validator.jsonl
├── autofix_log.jsonl         # 仅 step 2 真修的轮次
├── proposals_appended.jsonl  # schema_valid 过关的升级建议 (允许同 pid 重复, main 侧 dedup)
├── decisions/
│   └── <pid>.json            # main 单写; terminal (approve/deny) 不可回退
├── checkpoints/
│   └── iter_<N>.json         # atomic rename; .tmp 孤儿自动跳过
├── summary.json              # subagent normal exit 才写; 缺失 = crash_detected() 触发
├── summary.md                # 同上, 人读版
├── final_artifact.md         # subagent 写
├── subagent.log              # launch.sh stdout+stderr
└── run.pid                   # launch.sh 写
```

---

## 跑一次的最小命令

```bash
# 1. 备输入
echo "Review M5_RENAME plugin deliverables for ship-readiness." > /tmp/task.txt
cp proposal/proposal_rename_to_insights_share.md /tmp/artifact.md

# 2. 后台 kick off (nohup + --resume)
./.claude/roleplan_agents/inbox_loop/launch.sh \
    /tmp/task.txt \
    /tmp/artifact.md \
    docs/user_complaints_inbox \
    5

# 3. main session 读 pending (任何时候, 不阻塞 subagent)
.venv/bin/python .claude/roleplan_agents/inbox_loop/main_drain.py \
    --inbox-dir docs/user_complaints_inbox

# 4. 对每条 batch 调 AskUserQuestion, 回写
.venv/bin/python .claude/roleplan_agents/inbox_loop/main_decide.py \
    --inbox-dir docs/user_complaints_inbox \
    --proposal-id <pid> \
    --answer Approve
```

`launch.sh` 使用 `/Users/m1/projects/demo_insights_share/insights-share/demo_codes/.venv/bin/python` (已验证存在), 回退系统 python3。

---

## 为什么 step 3 不上 LLM judge

user 原文: *"use claudefast -p to offer LLM-as-judge EXCEPT 3"*

解读:

- step 1 roles、step 2 autofix、ship verdict 都是 **LLM-as-judge** (LLM 做 ship/revise/bug 有无 的判决)
- step 3 的 LLM 只做**结构提取** (从 free-text 中抽 JSON), 不判决内容好坏
- 所以 step 3 仍然调用 `claudefast -p`, 但不把 LLM 当 judge — 只当 JSON extractor
- spam 过滤由 `schema_valid()` (纯 Python) + user 侧 `AskUserQuestion` 的 Defer/Deny 兜底, LLM 永不参与 step 3 的价值判断

这样 inbox 里可能出现 user 视角的"垃圾建议", 但:

1. `schema_valid` 拦住结构不合格的 (空字段、impact=minimal、title<5ch 等)
2. `MAX_PENDING=20` 软上限, 避免 UI 溢出
3. `DEFER_AFTER_K=3` 硬上限, 被 Defer 3 次自动降为 denied, 不再占名额
4. Approve/Deny 是 terminal 态, 不可回退

与 user spec 严格对齐。

---

## 单测覆盖 (无 LLM, 0.022s)

```bash
.venv/bin/python -m unittest discover \
    -s .claude/roleplan_agents/inbox_loop/tests -v
```

23 tests pass:

- `proposal_id` 稳定性 + 字段敏感性
- `schema_valid` 6 类拒绝路径
- `atomic_write_json` 无 .tmp 残留
- `derive_pending` dedup + terminal exclusion + defer_K exclusion
- `crash_detected` 4 场景 (no-ckpt / summary-present / stale-ckpt / fresh-ckpt)
- `latest_checkpoint` 最高 iter + .tmp 过滤
- `apply_answer` terminal 不回退 + Defer 升级 denied + 未知 answer raises

---

## 下一步待做

- 跑 1 次真实 end-to-end LLM pass, 验证 inbox 目录实际产出与文档一致
- (可选) 加 slash command 把 drain → AskUserQuestion → decide 打包
- (可选) 接入 `start.demo.sh` self-verify 链路 (当前刻意不接, 因为 inbox_loop 是开发者工具非 PM demo surface)
