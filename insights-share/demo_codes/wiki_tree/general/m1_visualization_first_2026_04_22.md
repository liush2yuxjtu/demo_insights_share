---
{
  "id": "m1-visualization-first-2026-04-22",
  "title": "可视化优先：复杂数据/结构优先生成 HTML/ASCII",
  "author": "m1",
  "confidence": 0.85,
  "tags": ["visualization", "html", "ascii", "output", "html-example-archive"],
  "status": "active",
  "applies_when": ["复杂数据结构需要直观理解", "多人 review 需要快速传阅", "diff 展示"],
  "do_not_apply_when": ["纯文本摘要", "代码片段", "单一变量值"],
  "topic_id": "output-patterns",
  "label": "good",
  "label_note": "先图表后文字；HTML 输出自动开 chrome 预览；参考 html-example-archive",
  "raw_log": null
}
---

# 可视化优先：复杂数据/结构优先生成 HTML/ASCII

> author: m1 · confidence: 0.85

## 规则

- 复杂数据 → HTML table / tree / graph
- 结构 diff → ASCII art 框图
- 多人 review → HTML 文件 chrome 预览

## Good example

```bash
# 生成分组表格
echo "<table><tr><th>Card</th><th>Status</th></tr>" > /tmp/cards.html
git log --oneline -20 | while read hash msg; do
  echo "<tr><td>$hash</td><td>published</td></tr>" >> /tmp/cards.html
done
open /tmp/cards.html
```

## Bad example

```bash
# ❌ 贴 50 行纯文本，reviewer 无法快速定位
git log --oneline -50
```

## ASCII art 示例

```
┌─────────────────────────────────┐
│  CLAUDE.md 改动审计              │
├─────────────────────────────────┤
│  ✗ 删除：user_design/           │
│  ✗ 修改：根目录 MD               │
│  ✓ 新增：atomic-commits.md      │
└─────────────────────────────────┘
```

## Applies when

- 复杂数据结构需要直观理解
- 多人 review 需要快速传阅
- diff 展示

## Do NOT apply when

- 纯文本摘要
- 代码片段
- 单一变量值
