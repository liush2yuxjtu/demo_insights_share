---
{
  "id": "m1-read-before-task-2026-04-22",
  "title": "任务前必读 proposal + README + validation 四文件",
  "author": "m1",
  "confidence": 0.95,
  "tags": ["proposal", "README", "validation", "context", "read-first"],
  "status": "active",
  "applies_when": ["每个新任务开始前"],
  "do_not_apply_when": ["用户已提供完整上下文且明确说跳过", "紧急 hotfix 但无暇阅读"],
  "topic_id": "execution-patterns",
  "label": "good",
  "label_note": "先读 proposal/INDEX.md 及其全部 proposal_*.md，建立 CEO 级 plan 上下文",
  "raw_log": null
}
---

# 任务前必读 proposal + README + validation 四文件

> author: m1 · confidence: 0.95

## 必读文件

1. `proposal.md`
2. `README.md`
3. `validation_AB.md`
4. `validation.md`

## 扩展：proposal 目录

读 proposal.md 后必须跟进读：
- `proposal/INDEX.md`
- 及其所列全部设计 md

## 目的

建立完整上下文，避免：
- 做 feature 时不知道已有 proposal 冲突
- 忽略已在 validation.md 里记录的约束
- 用"应该没问题"代替实际读取

## Applies when

- 每个新任务开始前

## Do NOT apply when

- 用户已提供完整上下文且明确说跳过
- 紧急 hotfix 但无暇阅读（少见）
