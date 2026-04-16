# 任务前必读四文件

## 规则

任何任务开始前，Agent 必须先读取以下四个文件，建立完整项目上下文后再执行：

1. [proposal.md](../../proposal.md) — 项目背景、目标、行动、交付物
2. [README.md](../../README.md) — 仓库简介与快速入口
3. [validation_AB.md](../../validation_AB.md) — A/B 对照实验门禁规则
4. [validation.md](../../validation.md) — 验证框架与验证任务

## 原因

这四个文件共同定义了：
- 项目的目标与边界（proposal.md）
- 现有资产的位置（README.md）
- 实验数据的完整性要求（validation_AB.md）
- 验收标准（validation.md）

跳过任意一个文件都可能导致操作与项目目标偏离，或破坏 A/B 实验的有效性。

## 如何执行

任务开始时，依次用 Read 工具读取上述四个文件，确认理解后再进行任何写入、编辑或执行操作。

## 例外

- 仅做文档索引更新（如更新 docs/plans/INDEX.md）时，可仅读取与本次更改直接相关的文件。
- 仅读取文件（不修改任何内容）的纯查询任务可豁免。
