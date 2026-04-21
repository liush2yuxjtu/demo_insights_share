---
name: share-review
description: 管理员入口：列 topic 下并列 Good/Bad 卡片，支持 label_override、archive、open kanban。委托 share-curator agent 执行。非管理员会话不触发。
allowed-tools: Read, Bash, Grep
---

# /share-review

管理员 review 入口。委托 `share-curator` agent 完成看板操作。

## 使用

```
/share-review                               # 列当前全部 topic 概览
/share-review <topic-id>                    # 列某 topic 下全部并列 Good/Bad 卡片
/share-review <topic-id> --team team-a      # 只看某团队 namespace
/share-review <topic-id> --kanban           # 打开 kanban dashboard（走 insights-share-server --ui）
/share-review <card-id> --override <good|bad>
/share-review <card-id> --archive
```

示例：

- `/share-review postgres-pool-exhaustion`
- `/share-review postgres-pool-exhaustion --team team-a`
- `/share-review alice-pgpool-2026-04-10 --override bad`
- `/share-review --kanban`

## 流程

1. 解析子命令（list / override / archive / open_kanban）
2. 调 `share-curator` agent 拿 JSON 结果
3. 对写操作（override / archive）：
   - 先打印 before/after
   - **二次确认**（AskUserQuestion 式）才发 daemon 请求
4. 回显操作结果 + 受影响卡片 ID

## Good/Bad 并列展示

`/share-review <topic>` 输出必须是**并列**视图，不合并不排序挑最优。推荐 CLI
格式：

```
topic: postgres-pool-exhaustion
├── GOOD (3)
│   ├── alice-pgpool-2026-04-10 · PgBouncer txn mode / pool size ×2
│   ├── dave-pgpool-2026-04-15 · 动态伸缩 pool size by lag p99
│   └── erin-pgpool-2026-04-18 · 应用侧 backpressure + 队列
└── BAD (2)
    ├── bob-pgpool-bad-2026-04-12 · session pooling + retry-all
    └── carol-pgpool-bad-2026-04-14 · 盲目 ×10 pool size
```

## 权限

- 仅管理员会话触发；非管理员 prompt 一律返回"本命令仅对管理员可见"
- M2 阶段管理员判定：环境变量 `INSIGHTS_SHARE_ROLE=admin` 或 sandbox 标记
- M4 引入签名 + auth 后走 daemon-issued token

## 和 M4 的边界

- M4：所有 override / archive 必须重新签名；未签名卡片的 override 直接 REJECT

## 参考

- proposal/proposal_plugin_design.md §"Plugin 槽位映射" commands/share-review.md 行
- proposal/proposal_conflict_design.md §"核心思路"（并列视图）
