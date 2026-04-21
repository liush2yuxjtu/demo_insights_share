---
name: share-diff
description: 按 topic 查看并列 Good/Bad 决策差异，只展示 diff 和适用场景，不挑最优、不做冲突裁决。
allowed-tools: Read, Bash, Grep
---

# /share-diff

把某个 topic 下的并列决策整理成 PM 和工程师都能快速扫读的 diff 视图。

## 使用

```
/share-diff <topic-id>
/share-diff <topic-id> --label good
/share-diff <topic-id> --label bad
/share-diff <topic-id> --team team-a
```

示例：

- `/share-diff postgres-pool-exhaustion`
- `/share-diff postgres-pool-exhaustion --label bad`
- `/share-diff postgres-pool-exhaustion --team team-a`

## 做什么

1. 调 daemon `GET /topics/{topic_id}/examples`
2. 读取每条 example 的 `label / summary / applies_when / do_not_apply_when / label_override`
3. 按 `GOOD` / `BAD` 分栏输出同一 topic 下的并列决策
4. 只总结**差异点**、适用场景、不要踩的坑
5. 若传 `--label`，仅显示对应一侧，但仍保留 topic 总数摘要

## 输出契约

- **不合并、不挑最优、不做冲突检测**：Alice good、Bob bad、Carol good 必须并列展示
- 只写 diff，不扩写成完整 SWOT 或统一结论
- 管理员曾覆盖过 label 时，必须同时显示原始 `label` 与 `label_override`
- topic 不存在时返回明确的 not found，而不是假装空结果

推荐 CLI 形态：

```text
topic: postgres-pool-exhaustion
GOOD
- alice-pgpool-good-001
  applies_when: postgres>=13, pgbouncer transaction mode
  diff: idle_in_transaction_session_timeout=30s + pool×2

BAD
- bob-pgpool-bad-001
  applies_when: 32 核 + IO 密集
  diff: 盲目把 pool_size 从 10 提到 50 会放大 IO 抖动
```

## 和 M4 的边界

- M4：若卡片签名校验失败，视图里追加 `sig-fail` 降级提示

## 参考

- proposal/proposal_plugin_design.md §"Plugin 槽位映射" commands/share-diff.md 行
- proposal/proposal_conflict_design.md §"核心思路"（并列共存，不挑最优）
