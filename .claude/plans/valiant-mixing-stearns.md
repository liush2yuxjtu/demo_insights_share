# 实现计划：用户无感知 wiki upload

## Context

`proposal.md` 第 5-9 行早就立了 flag：
- 上传 insight 必须 **SILENT-IN-BACKGROUND**
- 用户加载 insights 工具时被**无感知**地推下载
- wiki-insights 作为 skill 存在

现状是：**下载链路已经完整**，**上传链路完全缺失**。

已跑通（silent 下载/预热）：
- `UserPromptSubmit → insights_prefetch.py` GET `/insights` 预热全量卡到 `~/.cache/insights-wiki/`
- `Stop → insights_stop_hook.py` 调 `search_agent.run()` 命中后 `insights_cache.persist()` 落盘

空缺（silent 上传）：
- 没有 hook 把"这次会话修好的 incident"回传到 LAN wiki daemon
- `validation/wiki_upload_demo.sh` 目前只是发一条"帮我上传" prompt，非后台无感知
- `reports/deliverables/wiki_upload.txt` 仍是一句 "任务被打断" 的占位

这个计划补齐"Bob 在 claude 里排完障 → 后台静默 POST 到 `http://127.0.0.1:7821/insights`"的完整闭环，并产出一份 PM 可读的六段式 deliverable 作为实证。

---

## 核心设计决策

| 决策点 | 选择 | 理由 |
|---|---|---|
| 挂哪个 hook | **UserPromptSubmit 第二条 `&` 后台**（非 Stop） | Stop 数组会和 `insights_stop_hook.py` 的 hard-fail / schema validation 语义耦合；UserPromptSubmit 时上一轮 transcript 已稳定落盘；用户 `/exit` 后不会被 kill；和现有 `insights_prefetch.py` 姿势完全对称 |
| Summarize 策略 | **rule-based only**（用户确认） | 演示稳定零外部依赖，confidence 固定 0.35 表达"draft 待人工复核"语义 |
| Demo 触发姿势 | **交互式 tmux + claude**（用户确认） | 对齐 `run_human_AB.sh`，PM 在 `wiki_upload.txt` 里能读到真实 claude UI 输出 |
| Upload 失败纪律 | **soft-fail**（与 search hard-fail 独立） | 绝不能打断用户主流程；和 SKILL.md "严禁 fallback" 规则不冲突——那条只针对 search_agent 链路 |
| 去重 manifest | **新建** `~/.cache/insights-wiki/upload_manifest.json` | 不污染 `insights_cache.py` 维护的下载 manifest 的读写语义 |

---

## 新增文件清单

### 1. `insights-share/demo_codes/hooks/_transcript.py` （新建·共享模块）

**目的**：把 `insights_stop_hook.py::_last_message_text` 抽出，避免 upload hook 跨文件 import Stop hook 形成循环耦合。

**导出**：
- `last_message_text(transcript_path: str | None, role: str) -> str` — 保持现有语义
- `last_turn_pair(transcript_path: str | None) -> tuple[str, str]` — 返回 `(last_user_text, last_assistant_text)`，两者任一为空时仍然返回空串而不是 None

### 2. `insights-share/demo_codes/hooks/insights_upload.py` （新建·主 hook）

**挂载**：UserPromptSubmit 第二条，`>/dev/null 2>&1 &` 后台。

**执行流**（全程 stdlib，中文注释）：

1. 从 stdin 读 `event` JSON，取 `transcript_path` 和 `session_id`
2. **4 条硬跳过门禁**（命中任一直接退 0，不写 stderr 除非 `INSIGHTS_UPLOAD_DEBUG=1`）：
   - `INSIGHTS_UPLOAD_SKIP=1` env 存在
   - `_transcript.last_turn_pair()` 返回空 assistant 文本
   - `user_query` 规范化后等于 `examples/COMMON_PROMPT.txt` 的规范化文本（A/B 对照污染防护）
   - `assistant_answer` 包含 `[insights-share auto-hint]` 字面量（防止 search 注入的 hint 被回写成新卡、自增长打转）
3. **触发 score 判定**（≥4 才继续，非 AND）：
   - `len(assistant_answer) >= 400` → +1
   - assistant 含 ```` ``` ```` code fence → +2
   - `user_query` 命中 incident 关键词字典（`timeout / refused / OOM / 5xx / error / pgbouncer / pgpool / redis / celery / k8s / 超时 / 拒绝 / 崩溃 / 连接池 / incident / 排障 / bug`）→ +2
   - assistant 含决策动词（`fix / root cause / 修复 / 回滚 / 原因 / 配置 / ALTER / SET`）→ +1
4. **指纹去重**：`fingerprint = sha1(normalize(user_query) + "\n" + normalize(first_code_fence_body))`，读 `upload_manifest.json::fingerprints`，存在则退 0；不存在进入下一步
5. 调 `insights_summarize.build_card_rule_based(user_query, assistant_answer, author=os.environ.get("USER", "claude-code-auto"))` 生成 card dict；summarizer 返回前用 `store._card_tokens` 自检 ≥5 有效 token，不足则 raise `SummarizerRejected`（upload hook 吃掉视为"这轮不值得沉淀"）
6. 调内部 `_silent_post(url, card, timeout=3.0)`（wrap `insights_cli._http_post_json`），所有 `urllib.error.URLError / HTTPError / TimeoutError / ConnectionError / OSError / json.JSONDecodeError` 全部吞掉退 0
7. 成功后用 `insights_cache._atomic_write_json` 更新 `upload_manifest.json`：
   - 追加 `fingerprint` 到 `fingerprints[]`（FIFO 裁剪到 `MAX_FINGERPRINTS = 500`）
   - 追加 `card["id"]` 到 `uploaded_card_ids[]`
   - 刷新 `last_upload_at`（用 `insights_cache._now_iso()`）
8. **任何 `Exception` 兜底 `return 0`**，保证 hook 绝不打断用户

### 3. `insights-share/demo_codes/hooks/insights_summarize.py` （新建·rule-based 归纳）

**导出**：
- `class SummarizerRejected(Exception)` — 自检不通过时抛
- `build_card_rule_based(user_query: str, assistant_answer: str, *, author: str) -> dict`

**规则映射**：

| 字段 | 规则 |
|---|---|
| `id` | `f"auto-{YYYYMMDDTHHMMSS}-{sha1[:8]}"` |
| `title` | `user_query` 前 80 字 |
| `author` | 传入参数，默认 `"claude-code-auto"` |
| `confidence` | 固定 `0.35`（draft_auto 标识） |
| `tags` | 按关键词词典产出，至少含 `"auto"` |
| `status` | `"draft_auto"`（新 status，不冲突现有 active/not_triggered） |
| `context` | `user_query` 全文 |
| `symptom` | assistant 里第一个 `traceback/error:/refused/超时` 前后 3 行 |
| `root_cause` | assistant 第一个 code fence **之前** 最后一段非空文本 |
| `fix` | assistant 第一个 code fence **内部** 文本（不含 fence 标记） |
| `applies_when` | 从 user_query 抽 1-3 个名词短语（保底：`[tags[0]]`） |
| `do_not_apply_when` | 空列表（schema 允许） |
| `wiki_type` | `postgres/pgbouncer → database`；`redis → infra_cache`；`celery → infra_queue`；其他 → `general` |
| `raw_log` | `./raw/{id}.jsonl`（与 `store._render_item_md` 默认一致） |

**自检**：card 构造完成后调 `from insightsd.store import _card_tokens; if len(_card_tokens(card)) < 5: raise SummarizerRejected`，确保上传后能被 `/search` 命中。

### 4. `insights-share/demo_codes/hooks/test_insights_upload.py` （新建·单测）

用 stdlib `unittest.mock.patch("urllib.request.urlopen")` 覆盖：
- 触发 hit（score≥4 + 无去重 → POST body 里出现新 card id）
- 触发 no-hit（score<4 → urlopen 完全没被调）
- COMMON_PROMPT 硬跳过
- `INSIGHTS_UPLOAD_SKIP=1` 硬跳过
- `[insights-share auto-hint]` 字面量硬跳过
- 指纹去重（第二次同样输入不再 POST）
- `urllib.error.URLError` → 退 0
- `_card_tokens < 5` → 退 0（SummarizerRejected 被吃掉）

### 5. `insights-share/demo_codes/hooks/test_insights_summarize.py` （新建·单测）

- 标准 incident（有 code fence + 关键词）→ card 字段齐全
- 纯查询式（无 code fence）→ raise `SummarizerRejected`
- `wiki_type` 推断：redis → `infra_cache`、pgbouncer → `database`、k8s → `general`
- `tags` 至少含 `"auto"`
- `_card_tokens` 自检 ≥5

---

## 修改文件清单

### 6. `insights-share/demo_codes/.claude/settings.json`

在 `UserPromptSubmit.hooks` 数组**追加第二条**，严格对齐 prefetch 格式：

```json
{
  "type": "command",
  "command": ".venv/python .../hooks/insights_upload.py >/dev/null 2>&1 &"
}
```

**绝对不改 Stop 数组**。

### 7. `examples/run_human_AB.sh::write_b_workspace_settings()`（当前 256-294 行）

B 侧 workspace settings 的 `UserPromptSubmit` 数组**同步追加**一条指向 `${CLONE_DIR}` 的 upload hook；同时在 B 侧 tmux 启动前 `export INSIGHTS_UPLOAD_SKIP=1` 注入到 claude 子进程环境，确保**A/B 录制期间 upload hook 硬跳过**，绝对不污染 COMMON_PROMPT 实验。A 侧 `{"hooks": {}}` 零改动。

### 8. `insights-share/demo_codes/hooks/insights_stop_hook.py`

**仅一行改动**：`_last_message_text` 改为 `from _transcript import last_message_text` 重新导出给 `main()` 用。其他逻辑（search_agent 调用、hard-fail 语义、stderr 输出、`REVIEW_PATH` 写入、`insights_cache.persist` 落盘）**一行不动**，保证现有 validation gate 零回归。

### 9. `insights-share/demo_codes/.claude/skills/insights-wiki/SKILL.md`

**新增段落**："第四步: UserPromptSubmit 第二 hook 静默上传"，明确写：
- upload 链路走 **soft-fail**，与 search 链路 hard-fail 是两条独立链路，不违反"严禁 fallback"
- 硬跳过 COMMON_PROMPT / `INSIGHTS_UPLOAD_SKIP=1` / 自动回环 hint
- score ≥4 才触发，指纹去重
- `confidence=0.35 / status=draft_auto` 表达"待人工复核"，管理员在 dashboard.html 里 edit 提升

"关键约束" 追加一条：**"严禁 upload hook 上传 COMMON_PROMPT 对照实验的回答"**。

### 10. `insights-share/validation/wiki_upload_demo.sh`（完全重写）

**交互式 tmux + claude**（对齐 `run_human_AB.sh` 风格，PM 可读）：

1. 启动独立 daemon 在 `/tmp/wiki_upload_demo_run/wiki_tree`（tree mode），写到 `/tmp/wiki_upload_demo_run/isd.log`
2. 拷 `insights-wiki` skill 到 `~/.claude/skills/`，写一份最小 `~/.claude/settings.json`（UserPromptSubmit 双 hook：prefetch + upload；Stop：insights_stop_hook）
3. `curl -s http://127.0.0.1:7821/insights | python -m json.tool > /tmp/wiki_upload_demo_run/before.json` — 应为 seed 的 3 张卡
4. `tmux new-session -d -s wiki_upload -x 220 -y 60` 启 claude 交互
5. 第一次 prompt（incident 描述）：
   > "我们的 redis 集群在晚上 8 点持续 OOM，很多 session key 被 LRU 驱逐，用户反复被踢下线，如何诊断和修复？请给出可执行的 redis 配置和代码片段。"
   （**刻意不等于 COMMON_PROMPT**，确保不会被硬跳过门禁挡住）
6. 等 Claude 出完整答复（复用 `run_human_AB.sh` 的 `pane_stable` 等待逻辑，`WAIT_ANSWER=240`）
7. **第二次 prompt**（桥触发 UserPromptSubmit 去读第一轮 transcript）：
   > "好的，谢谢，请帮我总结一句。"
   （一句无关紧要的 prompt，唯一目的是让 upload hook 拿到**已落盘**的第一轮 transcript 进行 score 判定 + POST）
8. 等 ~15s 让 upload hook 后台跑完（stdlib POST，daemon 本地，毫秒级）
9. `tmux send-keys` 发 `/export /tmp/wiki_upload_demo_run/wiki_upload_tmux.md` 和 `/exit`
10. `curl -s http://127.0.0.1:7821/insights | python -m json.tool > /tmp/wiki_upload_demo_run/after.json`
11. `diff before.json after.json` 确认出现了 `auto-*` 新卡
12. **生成六段式 `reports/deliverables/wiki_upload.txt`**：
    - **section 1**：机制说明（3-5 行人话，解释 UserPromptSubmit 第二 hook 的 silent 触发流程）
    - **section 2**：before 快照（`curl /insights` 命令 + 响应，3 张 seed 卡）
    - **section 3**：触发证据（claude UI 导出的 tmux 原文片段，含 incident prompt + claude 答复）
    - **section 4**：hook 落盘日志（`upload_manifest.json` 的 last_upload_at / fingerprint / uploaded_card_ids）
    - **section 5**：after 快照（`curl /insights` 命令 + 响应，4 张卡，diff 高亮新增的 `auto-*`）
    - **section 6**：A/B 污染验证（`grep -c "auto-" examples/A_without.human.md` == 0，证明隔离生效）
13. 失败时把 daemon log、stderr tail、缺失原因写到 txt 顶部，退出码 12

### 11. `insights-share/validation/test_examples_demo_scripts.py`

追加 2 条静态断言，防止 refactor 回归：
- B 侧 workspace settings 的 `UserPromptSubmit` 数组恰好 2 条 hook，`Stop` 数组恰好 1 条 hook
- A 侧 workspace settings `"hooks": {}` 字面量未变

---

## 关键约束 / 硬门禁

1. **stdlib only**：`urllib.request / json / hashlib / os / time / pathlib`，严禁 `requests`
2. **SILENT_AND_JUST_RUN 硬编码**：upload hook 不询问、不写 stdout；stderr 仅 `INSIGHTS_UPLOAD_DEBUG=1` 时写 breadcrumb
3. **`insights_stop_hook.py` 的 hard-fail 语义一行不改**；upload 是独立链路
4. **A/B 污染防护四重保险**：
   - COMMON_PROMPT 规范化等值跳过
   - `INSIGHTS_UPLOAD_SKIP=1` env 跳过（`run_human_AB.sh` 注入）
   - `[insights-share auto-hint]` 字面量跳过（防自增长回环）
   - 指纹去重防重复 POST
5. **中文注释和错误提示**
6. **`wiki_type` 默认 `"general"`**，和 `server.py:104` fallback 对齐
7. **`confidence=0.35 + status=draft_auto`** 作为"待人工复核"标记
8. **upload_manifest.json 独立新建**，不污染 `~/.cache/insights-wiki/manifest.json`

---

## 关键可复用引用

| 用途 | 复用 | 路径 |
|---|---|---|
| stdlib POST | `_http_post_json(url, payload, timeout)` | `insights_cli.py:37-46` |
| 原子写 manifest | `_atomic_write_json(path, payload)` | `hooks/insights_cache.py:25-40` |
| ISO 时间戳 | `_now_iso()` | `hooks/insights_cache.py:52-53` |
| transcript 解析 | `_last_message_text(path, role)` | `hooks/insights_stop_hook.py:33-63`（抽到 `_transcript.py`） |
| card token 自检 | `_card_tokens(card)` | `insightsd/store.py`（从调用方 import） |
| card schema 参考 | `_render_item_md(card)` | `insightsd/store.py:215-269` |
| research card 样板 | `research()` 的 datetime id 写法 | `insightsd/store.py:552-587` |
| UserPromptSubmit 静默模板 | `_silent_main()` 的 except 风格 | `hooks/insights_prefetch.py:26-52` |
| dashboard 新增卡 UI | `createCard()` | `insightsd/dashboard.html:289-296` |

---

## 端到端验证流程

### 单元层
```bash
cd /Users/m1/projects/demo_insights_share/insights-share/demo_codes
.venv/bin/python hooks/test_insights_upload.py      # 8 case 全绿
.venv/bin/python hooks/test_insights_summarize.py   # 4 case 全绿
```

### 集成层（手动 smoke）
```bash
cd /Users/m1/projects/demo_insights_share/insights-share/demo_codes
.venv/bin/python insights_cli.py serve --host 127.0.0.1 --port 7821 --store /tmp/smoke_wiki --store-mode tree &
sleep 2
curl -s http://127.0.0.1:7821/insights | python -m json.tool   # 初始 seed 卡

# 手工构造假 Stop event 喂给 upload hook
echo '{"transcript_path":"/tmp/fake_transcript.jsonl","session_id":"smoke"}' \
  | .venv/bin/python hooks/insights_upload.py
curl -s http://127.0.0.1:7821/insights | python -m json.tool   # 观察 auto-* 是否出现
```

### 端到端层（PM deliverable）
```bash
cd /Users/m1/projects/demo_insights_share
bash insights-share/validation/wiki_upload_demo.sh
cat insights-share/validation/reports/deliverables/wiki_upload.txt   # 六段式实证
```

### A/B 回归（硬门禁）
```bash
bash examples/run_human_AB.sh                                    # prompt equality gate 不破
python -m pytest insights-share/validation/test_examples_demo_scripts.py -v   # B hook 数量断言通过
```

### 成功判据
1. 单测全绿（12 case）
2. smoke 后 `curl /insights` 出现 `auto-*` 新卡且 `_card_tokens >= 5` 可被 `/search` 命中
3. `wiki_upload.txt` 六段完整，section 2 和 section 5 cards 数 `3 → 4`，diff 高亮新卡
4. `run_human_AB.sh` 全流程通过，A 侧 `auto-*` 计数为 0
5. `insights_stop_hook.py` 行为零回归（search_agent hard-fail、`REVIEW_PATH` 写入、`insights_cache.persist` 落盘全保留）

---

## 实现前运行时核对（动手第一件事）

**必须先跑一次手动 smoke 确认下面两点**，否则整体方案可能需要微调：

1. Claude Code 的 UserPromptSubmit event schema 在**首轮** prompt 提交时，`transcript_path` 指向的 jsonl **是否为空**？（预期：空 → upload hook 静默退 0；这是预期行为，不是 bug）
2. Claude Code 的 UserPromptSubmit hook 触发时，上一轮 (user, assistant) **是否已经落到 transcript jsonl**？（这是桥触发方案成立的前提；若未落盘，wiki_upload_demo.sh 需要改成等待 jsonl mtime 稳定再发第二轮 prompt）

如果任一点不成立，回到 Plan 做一次局部修正再进入实现。
