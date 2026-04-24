---
{
  "id": "m1-surgical-rollback-2026-04-22",
  "title": "外科式回滚：精准定位，仅回滚有害变更",
  "author": "m1",
  "confidence": 0.9,
  "tags": ["rollback", "git", "surgical", "execution-strategy", "data-safety"],
  "status": "active",
  "applies_when": ["需要回滚已推送的坏 commit", "需要恢复误删文件", "需要撤销部分变更保留其他"],
  "do_not_apply_when": ["全新未推送的本地改动（直接 reset 即可）", "整个 branch 需要重建"],
  "topic_id": "execution-patterns",
  "label": "good",
  "label_note": "回滚前先盘点，不做破坏性全量 revert，先备份再操作",
  "raw_log": null
}
---

# 外科式回滚：精准定位，仅回滚有害变更

> author: m1 · confidence: 0.9

## 数据安全协议

回滚前必做：
1. **盘点**：列出所有受影响文件
2. **备份**：`git branch backup-<date>-<desc>`
3. **外科式操作**：精准 git revert 或 git checkout，不用 `git reset --hard`

## git revert vs git reset

| 场景 | 工具 |
|------|------|
| 已推送，需要保留历史 | `git revert <commit>` |
| 未推送，本地清理 | `git reset --soft HEAD~1` |
| 需要回滚多个 commit | `git revert <A>..<B>` |

## 禁止

- `git push --force`（除非用户明确授权）
- `git reset --hard` 在有未 commit 工作时（先 `git stash`）
- 跳过 pre-commit hook 的 `--no-verify`

## Good workflow

```bash
git log --oneline -10    # 找到目标 commit
git branch backup-$(date +%Y%m%d)-bad-fix    # 备份
git revert <bad-commit-hash>    # 生成反向 commit
git push    # 不 force，保留历史
```

## Applies when

- 需要回滚已推送的坏 commit
- 需要恢复误删文件
- 需要撤销部分变更保留其他

## Do NOT apply when

- 全新未推送的本地改动（直接 reset 即可）
- 整个 branch 需要重建
