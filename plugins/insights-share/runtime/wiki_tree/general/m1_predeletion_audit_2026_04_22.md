---
{
  "id": "m1-predeletion-audit-2026-04-22",
  "title": "删除前审计：盘点依赖再外科式删除",
  "author": "m1",
  "confidence": 0.88,
  "tags": ["delete", "audit", "data-safety", "dependency", "execution-strategy"],
  "status": "active",
  "applies_when": ["删除文件/表/配置前", "清理旧版本依赖前", "删除 hook/skill 前"],
  "do_not_apply_when": ["纯临时文件（明确无依赖）", "用户明确说不需要审计"],
  "topic_id": "execution-patterns",
  "label": "good",
  "label_note": "删除前必须盘点：谁引用它？删了谁会坏？回滚路径是什么？",
  "raw_log": null
}
---

# 删除前审计：盘点依赖再外科式删除

> author: m1 · confidence: 0.88

## 强制步骤

1. **盘点**：列出所有引用目标的地方
   ```bash
   grep -r "target_file" --include="*.py" --include="*.sh" .
   ```
2. **评估影响**：每个引用是否可安全移除
3. **备份**：分支备份或 `git stash`
4. **外科式删除**：精确 `git rm` / `rm`，不批量 `rm -rf`
5. **验证**：跑相关测试，确认无 break

## 禁止

- `rm -rf` 不先 `find` 盘点
- 删除有 import/require 的文件不更新引用方
- 删除 hook/skill 前不检查 `.claude/settings.json` 是否引用

## 删除审计清单

| 检查项 | 工具 |
|--------|------|
| git 历史引用 | `git log --all --oneline -- <file>` |
| 磁盘引用 | `grep -r` |
| 配置引用 | `grep -r` settings.json |
| 依赖声明 | package.json / requirements.txt |

## Applies when

- 删除文件/表/配置前
- 清理旧版本依赖前
- 删除 hook/skill 前

## Do NOT apply when

- 纯临时文件（明确无依赖）
- 用户明确说不需要审计
