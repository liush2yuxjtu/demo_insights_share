---
name: share-publish
description: 发布一条新 insight 卡片到 LAN wiki。走 share-validator agent 做发布前校验；支持 --dry-run 不落盘，仅输出校验报告。
allowed-tools: Read, Bash, Grep
---

# /share-publish

把一张 insight 卡片发到 LAN `insightsd`。发布前先跑 `share-validator`
agent；校验通过才调 daemon `POST /insights`。

## 使用

```
/share-publish <card-path-or-json>              # 正式发布
/share-publish <card-path-or-json> --dry-run    # 仅跑校验，不调 daemon
/share-publish <card-path-or-json> --team team-a
```

示例：

- `/share-publish wiki_tree/database/alice-pgpool-2026-04-21.md`
- `/share-publish wiki_tree/frontend/carol-next-streaming-2026-04-21.md --dry-run`
- `/share-publish wiki_tree/database/postgres_pool.md --team team-a`

## 流程

1. **读卡片**：支持磁盘路径或内联 JSON
2. **调 `share-validator` agent**：拿 `{verdict, checks[], next}`
3. **分流**：
   - `verdict == REJECT` → 打印 checks，拒绝发布，给出修正建议（`next` 字段），退出非零
   - `verdict == WARN`  → 如 `--dry-run`，仅打印警告；否则发布 + 附带 warnings
   - `verdict == PASS`  → 发布
4. **发布**：`POST http://127.0.0.1:7821/insights` with 卡片 JSON
5. **回显**：卡片 ID、daemon 返回、statusline 更新

## --dry-run 行为

- 不调 daemon `POST`
- 不动磁盘 `wiki_tree/`
- 不改 `~/.cache/insights-share/today_count.json`
- 仅输出 validator 报告

目的：PM 演示场景零风险（对齐 proposal_plugin_design.md §"额外能力" `--dry-run`
行）。

## 数据契约

- 尊重 `proposal_conflict_design.md`：同 topic 下 Good/Bad 并列永远合法，不因
  「已有另一方向」而 REJECT
- 尊重 `proposal_wiki_card.md`：卡片落盘路径 `wiki_tree/{wiki_type}/{slug}.md`
- 若指定 `--team <name>`，写入卡片 JSON 的 `team` 字段，走逻辑 team namespace
- 禁止旁路 `share-validator`，即使 PM 指定 `--force`（M2 阶段不提供 `--force`）

## 和 M4 的边界

- M4：发布必带 ed25519 签名；未签名卡片在 M4 后直接 REJECT

## 参考

- proposal/proposal_plugin_design.md §"Plugin 槽位映射" commands/share-publish.md 行
- proposal/proposal_plugin_design.md §"额外能力" `--dry-run` 行
