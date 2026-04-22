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
| `/topics` | POST | 新建 topic (前置, 必须先有 topic_id) |
| `/topics/{id}/examples?label=...` | GET | 列卡片 |
| `/insights` | POST | 新增卡 (主上传入口) |
| `/insights/{id}/edit` | POST | patch 字段 |
| `/insights/{id}/tag` | POST | 加 tag |
| `/insights/merge` | POST | 合并 |

## Daemon 卡片真实 schema (wiki_tree/general/bob_pgpool_bad_*.json 实测)
```json
{
  "id": "<slug-with-hyphens>",
  "title": "<≤60字 摘要>",
  "author": "<名字>",
  "confidence": 0.5,
  "tags": ["..."],
  "status": "active",
  "topic_id": "<已存在 topic id>",
  "label": "good|bad",
  "label_note": "<rationale 摘要>",
  "raw_log_type": "export"
}
```

## Mapper (我的卡 → daemon schema)
| 我的字段 | daemon 字段 | 转换 |
|----------|-------------|------|
| scenario | title | 截 60 字 |
| decision | label | 直传 |
| rationale | label_note | 截 200 字 |
| labels | tags | 直传 |
| topic | topic_id | 从 staging 子目录名读取真实 topic (`database`/`infra_cache`/`tooling`/...)；若 daemon `/topics` 缺，则 POST /topics 按需补建，wiki_type 取同名 |
| author | author | 直传 |
| (无) | confidence | 0.4 (auto-extracted 默认低) |
| (无) | status | "active" |

## 前置 topic 注册 (按 staging 真实子目录动态生成)
```bash
# 1) 列 staging 已抽出的 topic
TOPICS=$(ls /tmp/insights_upload_staging/)
# 2) 列 daemon 已知 topic
KNOWN=$(curl -s --noproxy '*' http://127.0.0.1:7821/topics | jq -r '.topics[].id')
# 3) 缺的补建
for t in $TOPICS; do
  TID="auto-${t}"  # 加前缀避免和 demo seeds 冲突
  if ! echo "$KNOWN" | grep -qx "$TID"; then
    curl -s --noproxy '*' -X POST http://127.0.0.1:7821/topics \
      -H "Content-Type: application/json" \
      -d "{\"id\":\"$TID\",\"title\":\"自动抽取: $t\",\"tags\":[\"auto-extracted\",\"$t\"],\"created_by\":\"extract_lessons.py\",\"wiki_type\":\"$t\"}"
  fi
done
```

## Daemon 启动绝对路径 (实测命令)
```bash
cd /Users/m1/projects/demo_insights_share/insights-share/demo_codes && \
  nohup .venv/bin/python insights_cli.py serve --host 127.0.0.1 --port 7821 \
  --store wiki_tree --store-mode tree > /tmp/insightsd.log 2>&1 &
echo $! > /tmp/insightsd.pid
```

## Self-verify 闭环说明
judge probe 不是循环调用 plan，而是用 LLM 复述 plan 内容 + 缺项检测。retreat condition: judge 给 PASS 或 5 轮上限；REFINE 触发本文件 edit；FAIL 升级 `claude -p` (非 fast)。

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
