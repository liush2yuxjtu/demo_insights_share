---
{
  "id": "m1-git-worktree-2026-04-22",
  "title": "git worktree 隔离并行开发",
  "author": "m1",
  "confidence": 0.85,
  "tags": ["git", "worktree", "parallel", "isolation", "branch"],
  "status": "active",
  "applies_when": ["需要并行在多个 branch 上工作", "需要在隔离环境跑测试不干扰主工作目录"],
  "do_not_apply_when": ["单 branch 开发", "磁盘空间紧张"],
  "topic_id": "git-patterns",
  "label": "good",
  "label_note": "worktree 把同一 repo 克隆到不同目录，各自独立，互不干扰",
  "raw_log": null
}
---

# git worktree 隔离并行开发

> author: m1 · confidence: 0.85

## 概念

git worktree 把同一 repo 克隆到多个目录，每个 tree 可以 checkout 不同 branch，**共享同一个 .git 对象库**，磁盘占用极低。

## Good example

```bash
# 添加一个新 worktree
git worktree add ../feature-x-webrecht feature-x

# 在新目录里工作，不干扰主目录
cd ../feature-x-webrecht
git checkout -b new-feature
# work done...

# 清理
git worktree remove ../feature-x-webrecht
```

## vs clone

- `git clone`：完整复制，磁盘大，.git 完全独立
- `git worktree`：共享 .git，磁盘极小，切换代价为零

## 常见场景

- feature 开发与 main 并行，不污染 working tree
- 需要在旧 commit 上重现 bug，同时保留当前工作
- CI pipeline 需要并行跑多个版本的测试

## Applies when

- 需要并行在多个 branch 上工作
- 需要在隔离环境跑测试不干扰主工作目录

## Do NOT apply when

- 单 branch 开发
- 磁盘空间紧张
