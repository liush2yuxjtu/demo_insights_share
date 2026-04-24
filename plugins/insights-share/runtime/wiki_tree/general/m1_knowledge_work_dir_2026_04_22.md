---
{
  "id": "m1-knowledge-work-2026-04-22",
  "title": "竞品/销售/法务任务前先 cd ~/projects/knowledge-work",
  "author": "m1",
  "confidence": 0.85,
  "tags": ["knowledge-work", "competitive-brief", "skill", "directory", "workflow"],
  "status": "active",
  "applies_when": ["竞品分析", "销售支持", "法务文档", "任一 knowledge-work skill 使用前"],
  "do_not_apply_when": ["纯工程任务（编码/debug/重构）"],
  "topic_id": "execution-patterns",
  "label": "good",
  "label_note": "knowledge-work 目录存 17 个项目级 skill，含 competitive-brief 等",
  "raw_log": null
}
---

# 竞品/销售/法务任务前先 cd ~/projects/knowledge-work

> author: m1 · confidence: 0.85

## 目录约定

`~/projects/knowledge-work/` 存 17 个项目级 skill，包括：
- `competitive-brief` — 竞品分析
- 销售支持类 skill
- 法务文档类 skill

## 正确流程

```
cd ~/projects/knowledge-work
<invoke relevant skill>
```

## 原因

knowledge-work 目录有独立 skill set，与 demo_insights_share 等工程 repo 的 skill 体系不同。混用会导致 context 混乱或找不到 skill。

## Bad example

```
仍在 demo_insights_share/ 内，试图用 knowledge-work skill
→ skill not found
```

## Good example

```
cd ~/projects/knowledge-work
skill competitive-brief "compare product X vs Y"
```

## Applies when

- 竞品分析
- 销售支持
- 法务文档
- 任一 knowledge-work skill 使用前

## Do NOT apply when

- 纯工程任务（编码/debug/重构）
