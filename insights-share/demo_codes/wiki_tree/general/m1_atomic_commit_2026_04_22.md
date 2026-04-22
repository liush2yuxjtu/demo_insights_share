---
{
  "id": "m1-atomic-commit-2026-04-22",
  "title": "Write/Edit 后立即原子 commit",
  "author": "m1",
  "confidence": 0.9,
  "tags": ["git", "atomic", "commit", "write", "edit"],
  "status": "active",
  "applies_when": ["任意 Write/Edit/文件移动/删除操作完成后", "每次 Bash 批量改文件后"],
  "do_not_apply_when": ["纯阅读/纯 Bash 查询", "用户显式说先不 commit"],
  "topic_id": "git-patterns",
  "label": "good",
  "label_note": "每次编辑按单一关注点立即 commit，回滚粒度可控",
  "raw_log": null
}
---

# Write/Edit 后立即原子 commit

> author: m1 · confidence: 0.9

## Rule

任意 Write / Edit / 文件移动 / 文件删除操作完成后，**立即**按单一关注点执行原子 git commit。禁止累积多个无关变更到同一 commit。

## 执行模板

```bash
git add <具体文件列表>
git commit -m "$(cat <<'EOF'
<type>: <单一关注点描述>

<可选 why / 关联规则>
EOF
)"
```

## 原子定义

- 一次重命名 = 一个 commit
- 一次规则新增 = 一个 commit
- 一次索引更新 = 一个 commit
- **不**把"移动文件 + 改规则 + 改索引"塞进同一 commit

## 禁止

- `git add -A` / `git add .`（可能带入 .env / 大文件）
- `git commit --amend` 覆盖已推送 commit（除非用户显式授权）
- 跳过 hook（`--no-verify`）

## Why

- 回滚粒度可控：坏改动只回退它自己
- history 可读：每条 log 对应一个意图
- review 友好：diff 聚焦单一关注点

## Applies when

- 任意 Write/Edit/文件移动/删除操作完成后
- 每次 Bash 批量改文件后

## Do NOT apply when

- 纯阅读/纯 Bash 查询
- 用户显式说先不 commit
