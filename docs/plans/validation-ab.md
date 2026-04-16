# validation_AB.md → 实现文件导航

源文档：[validation_AB.md](../../validation_AB.md)（只读）

---

## A/B 实验设计

**唯一变量**：`insights-wiki` skill + daemon 是否存在  
**控制变量**：两侧使用完全相同的 prompt

---

## Canonical Prompt（唯一真源）

| 内容 | 文件路径 |
|------|---------|
| 共用 prompt 文本 | [examples/COMMON_PROMPT.txt](../../examples/COMMON_PROMPT.txt) |

**规则**：脚本和测试只从此文件读取，禁止内联副本。

---

## A/B 录制资产

| 侧 | 环境 | 导出文件 |
|----|------|---------|
| A（对照） | 不加载 `insights-wiki` | [examples/A_without.human.md](../../examples/A_without.human.md) |
| B（实验） | 加载 `insights-wiki` + daemon | [examples/B_with.human.md](../../examples/B_with.human.md) |

原始 agent 格式（供程序解析）：
- [examples/A_without.agent.json](../../examples/A_without.agent.json)
- [examples/B_with.agent.json](../../examples/B_with.agent.json)

---

## 录制脚本

| 脚本 | 文件路径 |
|------|---------|
| A/B 人工录制入口 | [examples/run_human_AB.sh](../../examples/run_human_AB.sh) |
| 单次无 wiki 录制 | [insights-share/validation/without_oneline.sh](../../insights-share/validation/without_oneline.sh) |
| 单次有 wiki 录制 | [insights-share/validation/with_oneline.sh](../../insights-share/validation/with_oneline.sh) |
| 无 wiki 完整复现 | [insights-share/validation/without_reproduce.sh](../../insights-share/validation/without_reproduce.sh) |
| 有 wiki 完整复现 | [insights-share/validation/with_reproduce.sh](../../insights-share/validation/with_reproduce.sh) |
| tmux 双屏对比录制 | [insights-share/validation/tmux_with_without.sh](../../insights-share/validation/tmux_with_without.sh) |

---

## 门禁验证

### Hard Gate 规则

- A/B 首个用户 prompt 必须**完全相同**（规范化后逐字符匹配）
- 不允许 prompt 泄漏实验意图（如"若意外出现 LAN 卡片…"这类提示）
- 录制前必须清空 `~/.cache/insights-wiki/` 防止缓存污染

### 验证脚本

| 内容 | 文件路径 |
|------|---------|
| prompt 一致性检查命令 | [examples/validate_commands.sh](../../examples/validate_commands.sh) |
| 自动化测试（pytest） | [insights-share/validation/test_examples_demo_scripts.py](../../insights-share/validation/test_examples_demo_scripts.py) |
| AB demo plan 测试 | [insights-share/validation/test_ab_demo_plan.py](../../insights-share/validation/test_ab_demo_plan.py) |

### 通过标准

1. A/B 抽取出的 prompt 完全一致
2. A/B 唯一变量只剩 skill / daemon 是否存在

---

## 对比报告

| 报告 | 文件路径 |
|------|---------|
| A/B diff 分析 | [reports/deliverables/diff.md](../../insights-share/validation/reports/deliverables/diff.md) |
| Claude 导出（有 insights） | [reports/deliverables/claude_export_WITH.md](../../insights-share/validation/reports/deliverables/claude_export_WITH.md) |
| Claude 导出（无 insights） | [reports/deliverables/claude_export_WITHOUT.md](../../insights-share/validation/reports/deliverables/claude_export_WITHOUT.md) |
| A/B 浏览对比页 | [examples/index.html](../../examples/index.html) |
