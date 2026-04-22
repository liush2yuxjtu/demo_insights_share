# User-Unaware Download 实现文档

> 日期：2026-04-22
> 状态：已实现

## 问题背景

原始 proposal.md 约定：
> uploading/downloading insights must be SILENT-IN-BACKGROUND
> force downloading insights to users when users are not aware as long as they load our insights tool

用户打开 Claude Code 时，卡片必须已在本地，无需用户主动触发。

## 实现方案

### 1. SessionStart 双阶段预热

**Phase 1（原有）**：topics.json warm
- `session-start.sh` → `GET /topics` → `~/.cache/insights-share/warm/topics.json`
- 提供 topic 列表元数据，首轮搜索省 ~300ms

**Phase 2（新增）**：完整卡片预取
- `session-start.sh` → 调用 `session_start_full_fetch.py`
- `GET /insights` 拉全量卡片（full cards，非 sparse metadata）
- `persist()` 落盘到 `~/.cache/insights-share/<id>.json`
- manifest 维护 `etag` 字段

### 2. Delta Sync（ETag）

**服务端**（`insightsd/server.py`）：
```
GET /insights       → ETag: "MD5(JSON content)" header
GET /insights       → If-None-Match: <etag>
                      = match → 304 Not Modified（不返回 body）
```
- `/insights` 改用 `store.load()` 替代 `list_all()`，返回完整卡片
- `/topics` 同样加 ETag 支持

**客户端**（`insights_prefetch.py` + `session_start_full_fetch.py`）：
- manifest 缓存 `etag`
- 请求时带 `If-None-Match: <etag>`
- 304 时从本地 `~/.cache/insights-share/*.json` 读取已缓存卡片
- 新数据到达后更新 manifest etag

### 3. UserPromptSubmit 降级

当 daemon 304 时，`insights_prefetch.py` 从本地 cache 读取已持久化卡片，
仍能构建 `additionalContext`，不依赖网络。

## 文件清单

| 文件 | 职责 |
|------|------|
| `insights-share/demo_codes/hooks/session_start_full_fetch.py` | 新增：SessionStart 全量卡片拉取 + ETag 追踪 |
| `insights-share/demo_codes/hooks/insights_prefetch.py` | 修改：支持 If-None-Match + 304 cache fallback |
| `insights-share/demo_codes/insightsd/server.py` | 修改：/insights + /topics 加 ETag + 304 |
| `plugins/insights-share/hooks/session-start.sh` | 修改：Phase 2 调用 full fetch 脚本 |
| `plugins/insights-share/scripts/self_check.sh` | 修改：加 SessionStart + full_fetch 检查 |

## 验证

```bash
bash plugins/insights-share/scripts/self_check.sh | grep -E "SessionStart|session_start"
# 输出：
# hook SessionStart (full download): OK
# session_start_full_fetch.py: OK
```

## 未完成

- `cache_first: true` MCP transport 落地（声明在 `wiki-server.json`，未实现）
