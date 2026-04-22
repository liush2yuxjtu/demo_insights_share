# Finish Log — /qa S11 + E2E + 5 slash 独立探针 + 契约对齐

日期：2026-04-23
关联文档：
- `docs/qa/plugin_qa_plan.md`（§2 S11 / §3 E2E / §4 5 slash）
- `docs/finish_log/2026-04-23_qa-s1-s10-precheck.md`（上一轮 S1–S10）

## 做了什么

### 1. S11 Sandbox Demo 可自动化部分

| 要素 | 状态 | 证据 |
|------|------|------|
| 右 pane self_check.sh | ✅ | ALL GREEN 18/18（包含 M5–M8 前向兼容契约）|
| 右 pane statusline preview | ✅ | `[share ✗ 0/today]` rc=0（daemon 起后 0 hit 符合 ✗ 态语义）|
| 左 pane `guide_loop.sh` | ✅ | 存在 + `bash -n` 语法 OK + 信号驱动模式 |
| 沙箱脚本 `start.demo.sh` | ✅ | 存在 + `mktemp -d /tmp/demo-sandbox-*` + trap cleanup |
| tmux 双 pane attach + F12 退出 | ⏸️ | Bash tool 不能 attach；需 user 在 Terminal 手动跑 |

### 2. §3 E2E Daemon Endpoints 独立探针

起 `insights_cli.py serve --port 7821` 跑 4 端点：

| 端点 | 期望 | 实测 |
|------|------|------|
| `/healthz` | 200 ok | `200 {"ok":true}` ✅ |
| `/insights` | 200 cards 数组 | `200 {"cards":[200 条]}` ✅ |
| `/search?q=postgres&k=3` | 200 hits 数组 | `200 {"hits":[{id:m1-kb-aa-003,score:0.1}]}` ✅ |
| `/topics` (flat 模式) | 400 topics_not_supported | `400 {"error":"topics_not_supported"}` ✅ |

E2E Bob postgres prompt 注入 manifest + statusline 递增：⏸️ 需活 claude REPL。

### 3. §4 5 slash 独立探针

全部 5 个 md 结构 + frontmatter：

```
share-diff:    frontmatter OK
share-install: frontmatter OK
share-publish: frontmatter OK
share-review:  frontmatter OK
share-search:  frontmatter OK
```

Slash 实际 exec：⏸️ 需 Claude Code REPL 触发。

### 4. 发现 + 修 Bug #3

- commit `2b2b4a2` docs(qa): S10 daemon 探针契约与 daemon 实际 API 对齐

原契约假设 `/insights?topic=database` 能 filter，实际 daemon：
- `/insights` 只支持 `team` 参数，不支持 `topic`（topic filter 是 client 任务，不是 daemon 职责）
- flat 模式 `/topics` 返 400 `topics_not_supported`（仅 tree 模式支持）
- 搜索语义走 `/search?q=...&k=N`

改 S10 契约为四端点组合 `/healthz + /insights + /search + /topics`，
覆盖 flat 模式实际可验的全部端点 + 预期错误码契约。

## 本轮累计 commit 清单（7 条）

```
2b2b4a2 docs(qa): S10 daemon 探针契约与 daemon 实际 API 对齐
871a1e8 docs(finish_log): 落盘本轮 QA S1-S10 预检 + 2 bug fix + 工作树清零证据
16d6534 fix(insightsd): flat InsightStore.load 接受 team kwarg + 同步 QA plan 端点契约
2691e72 fix(insights-share): self_check.sh manifest 契约升级 M5 -> M5+M6+M7+M8 前向兼容
958e6ac chore(insights-share): general 批量入盘 226 张 KB 卡片 + team6 verify topic
8432251 chore(insights-share): database 清理 ghost 卡片 + postgres_pool label_override
4cadad3 docs(qa): plugin /qa 计划 markdown (审阅用，未执行)  [已有，非本轮]
```

本轮新增 commit: `8432251 → 2b2b4a2` 共 6 条（不含 `4cadad3`）。

## 本轮未验的交互部分（留下一轮）

| 探针 | 阻塞原因 | 下一轮触发方式 |
|------|----------|----------------|
| S11 tmux 双 pane attach + 沙箱交互 | Bash tool 不能 attach | user 在 Terminal 跑 `bash start.demo.sh` |
| §3 E2E Bob postgres prompt 注入 manifest | 需活 claude REPL | user 在 sandbox 右 pane 发 COMMON_PROMPT.txt |
| §4 5 slash 实际 exec | 需 Claude Code REPL 触发 | user 在沙箱 claude 里打 `/share-search postgres` 等 |

## PASS/FAIL 收尾

- **PASS**：S1–S10 全绿 + S11/E2E/slash 自动可验部分全绿 + 3 bug fix + 契约对齐
- **PARTIAL**：S11/E2E/slash 交互部分未跑（设计性阻塞：Bash tool 无法替代 user 交互）
- **下一步候选**：/review M7 landed commit + 本轮 7 commit / /benchmark latency baseline / M8_LATENCY_INDEX
