# upload_plan.md — jsonl 教训抽取 + 上传到 insights-share

## 目标
扫本地 `~/.claude/projects/**/*.jsonl` (3740 文件, 849M)，抽 reusable lessons，转 wiki card 格式，上传 LAN insightsd (port 7821)。

## 输入
- 源: `~/.claude/projects/-Users-m1-projects-demo-insights-share/*.jsonl` (本项目优先)
- 单条 jsonl 行 schema: `type` ∈ {user, assistant, system, attachment, file-history-snapshot, last-prompt, queue-operation}
- 配对单元: 同 sessionId 内 `user` → `assistant` 相邻消息

## 输出
- 暂存: `/tmp/insights_upload_staging/<topic>/<author>_<slug>_<date>.json`
- 卡片 schema (对齐 `wiki_tree/general/bob_pgpool_bad_2026_04_12.md` 结构):
  ```json
  {
    "id": "<uuid>",
    "topic": "<推断>",
    "author": "claude_session_<sessionId 前 8 位>",
    "scenario": "<user prompt 摘要 ≤80 字>",
    "decision": "good|bad",
    "rationale": "<assistant 给出根因/方案 ≤300 字>",
    "evidence_jsonl": "<源 jsonl 路径>:<line>",
    "date": "YYYY-MM-DD",
    "labels": ["auto-extracted"]
  }
  ```
- 同步 markdown 摘要 `<slug>.md`

## 抽取规则 (lesson 信号)
**保留**:
1. user 含 `bug|error|fix|fail|crash|stuck|为什么|不工作|报错` 等故障关键词
2. assistant 回复含具体定位 (file_path:line / 命令 / 配置项)
3. assistant 给出 fix (Edit/Write/具体配置改动)

**丢弃**:
- 闲聊、文档查询、纯 list 命令
- assistant 回复 < 50 字
- 重复 (同 root cause 已存在 wiki_tree 卡片 → skip)

## 执行步骤
1. **daemon 起动 (precondition)**: `cd insights-share/demo_codes && .venv/bin/python insights_cli.py serve --host 0.0.0.0 --port 7821 --store wiki_tree --store-mode tree &`，pid 写 `/tmp/insightsd.pid`
2. **dry-run**: 扫单一 jsonl (`7a4bcb58-...jsonl`, 342 行)，输出 staging，**不上传**
3. **judge probe**: `claudefast -p "@upload_plan.md @<jsonl> @<staging_dir> what would you do with this plan? ONLY EXPLAIN"` 验证理解
4. **judge 回 PASS** → 跑 fixed `scripts/extract_lessons.sh` 全量扫描
5. **JSON 上传**: `curl --noproxy '127.0.0.1,localhost' -X POST http://127.0.0.1:7821/insights -H "Content-Type: application/json" -d @<card.json>` 每张卡
6. **gate**: 上传后 `curl --noproxy '*' http://127.0.0.1:7821/topics` 含新 topic → PASS

## Daemon API (server.py 已确认)
| 路由 | 方法 | 用途 |
|------|------|------|
| `/topics` | GET | 列 topic |
| `/topics/{id}/examples?label=...` | GET | 列卡片 |
| `/insights` | POST | 新增卡 (主上传入口) |
| `/insights/{id}/edit` | POST | patch 字段 |
| `/insights/{id}/tag` | POST | 加 tag |
| `/insights/merge` | POST | 合并 |

## 系统 proxy 注意
本机 `http_proxy=http://127.0.0.1:7897` (Clash) 会拦截 loopback。所有 curl 必须加 `--noproxy '127.0.0.1,localhost'`，否则 502 Bad Gateway。Python urllib 同理需 `proxies={}`。

## 安全 / 隔离
- staging 目录: `/tmp/insights_upload_staging/` (非 ~/.claude，避免污染)
- 不删源 jsonl
- 上传走 LAN-only (127.0.0.1)，不出公网
- `INSIGHTS_EVENTS_URL` 仍空，emitter.py 不触发外部 POST

## Self-verify gate
| Gate | 检查 | 通过条件 |
|------|------|----------|
| G1 plan 可执行 | judge probe 复述 5 项 (输入/输出/规则/步骤/安全) | 5/5 命中 |
| G2 dry-run 输出 | staging 目录有 ≥1 张卡 + markdown | 文件数 > 0 |
| G3 schema 合规 | 每张卡 JSON parse + 字段齐 | 100% pass |
| G4 daemon 接受 | curl POST 返 200 / 201 | HTTP 2xx |
| G5 kanban 可见 | GET / 含新卡 ID | grep 命中 |

## 失败回滚
- staging 仅 `/tmp/`，rm -rf 即清
- daemon CRUD 失败 → 不重试，记 `staging/upload_failed.log`
- 任一 gate FAIL → 回写 plan 修订，重跑 judge
