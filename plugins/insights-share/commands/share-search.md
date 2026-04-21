---
name: share-search
description: 在 LAN insightsd 中按关键词检索 topic 下并列的 Good/Bad 卡片，展示 top-k 命中。不挑最优、不合并。
allowed-tools: Bash, Read
---

# /share-search

按关键词查询 LAN wiki，展示同一 topic 下**并列**的 Good/Bad 卡片，由用户自行根据 `applies_when` / `do_not_apply_when` 匹配场景。

## 使用

```
/share-search <查询词>
```

示例：

- `/share-search postgres pool`
- `/share-search redis eviction`

## 做什么

1. 调用 daemon `GET /search?q=<查询词>&k=5`
2. 按 **topic** 分组展示结果，每 topic 下 Good/Bad 并列
3. 每张卡片输出：`id / author / label / applies_when / summary`
4. **不合并、不排序挑最优、不做冲突检测**（依据 `proposal/proposal_conflict_design.md`）
5. 若命中为 0，输出空结果并提示可触发 `/share-publish`（M2 提供）

## 输出契约

- 保留卡片原始 `label_override` 字段展示（管理员覆盖过的卡片要让用户看见）
- 用户 prompt 里带敏感信息时，检索 query 脱敏后再发 daemon（对齐根规则「默认脱敏」）
- 若配置了 team namespace，查询追加 `team=<name>`，只返回该团队命中的卡片
- daemon 不可达时当前版本仍以明确报错为主；离线 fallback 不在本轮 M3 范围内

## 和 M2+ 的边界

M1 只做一次性查询。M2 `share-validator` agent 上线后，本命令将联动 agent 对命中卡片做发布前合法性校验（不影响展示，仅附加 badge）。

## 参考

- proposal/proposal_plugin_design.md §"Plugin 槽位映射" commands/share-search.md 行
- proposal/proposal_conflict_design.md §"核心思路"（并列共存，不挑最优）
