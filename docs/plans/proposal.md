# proposal.md → 实现文件导航

源文档：[proposal.md](../../proposal.md)（只读）

---

## Situation — 现状与问题

| 问题编号 | 问题描述 | 相关实现文件 |
|----------|---------|-------------|
| #1 | 生成耗时过长 | [adapter.py](../../insights-share/demo_codes/adapter.py) — MiniMax 快速模型替换 |
| #2 | insights 仅对个人有效 | [seeds/](../../insights-share/demo_codes/seeds/) — 共享种子条目 |
| #3 | 沿用他人 insights 次优 | [adapter.py](../../insights-share/demo_codes/adapter.py) — 语义匹配逻辑 |
| #4 | 上传必须静默后台 | [insightsd/\_\_init\_\_.py](../../insights-share/demo_codes/insightsd/__init__.py) — 守护进程 |
| #5 | 用户无感知强制下载 | [insightsd/\_\_init\_\_.py](../../insights-share/demo_codes/insightsd/__init__.py) — UserPromptSubmit 预热 |
| #6 | 管理员 CRUD + 审核 | [ui.py](../../insights-share/demo_codes/ui.py) — 管理看板 |
| #7 | wiki-insights 作为 skill | 见 Task 部分 skill 清单 |

---

## Task — 任务目标

### 核心功能

| 功能 | 实现文件 |
|------|---------|
| 生成一条 insight | [adapter.py](../../insights-share/demo_codes/adapter.py) |
| wiki 渐进式披露系统 | [ui.py](../../insights-share/demo_codes/ui.py) |
| 遇新问题先检索 wiki | [insightsd/\_\_init\_\_.py](../../insights-share/demo_codes/insightsd/__init__.py) |
| 仅热加载 wiki-insights | [insightsd/\_\_init\_\_.py](../../insights-share/demo_codes/insightsd/__init__.py) |
| 快速比对并验证 insights | [insights-share/validation/minimax_smoke.py](../../insights-share/validation/minimax_smoke.py) |
| 携带 insights 继续工作 | [examples/B_with.human.md](../../examples/B_with.human.md) — 效果示例 |

### Skills

| Skill 名称 | Flags | 说明 |
|-----------|-------|------|
| `insights-wiki-server` | `--start`（默认）、`--ui` | 启动服务器或打开管理看板；仅分配给管理员 |
| `insights-wiki` | `--install` | 安装并验证连接到服务器 |

### 服务器地址

开发阶段监听：`0.0.0.0:7821`（局域网用户可通过 `http://192.168.22.42:7821` 访问）

### AI 模型配置

```
ANTHROPIC_BASE_URL   = https://api.minimaxi.com/anthropic
ANTHROPIC_MODEL      = MiniMax-M2.7-highspeed
```

（真实 token 仅放环境变量，不进仓库）

---

## Action — 执行

| 执行入口 | 文件路径 |
|---------|---------|
| demo 启动脚本 | [run_demo.sh](../../insights-share/demo_codes/run_demo.sh) |
| PM 演示文档 | [pm_walkthrough.md](../../insights-share/demo_docs/pm_walkthrough.md) |
| PM 演示（STAR 格式） | [pm_walkthrough_star.md](../../insights-share/demo_docs/pm_walkthrough_star.md) |
| 设计文档 | [design.md](../../insights-share/demo_docs/design.md) |

---

## Expected Results — 交付物

| 交付物 | 文件路径 |
|--------|---------|
| 提案线性时间线 HTML | [proposal_linear.html](../../insights-share/validation/reports/deliverables/proposal_linear.html) |
| 验证线性时间线 HTML | [validation_linear.html](../../insights-share/validation/reports/deliverables/validation_linear.html) |
| Claude 导出（有 insights） | [claude_export_WITH.md](../../insights-share/validation/reports/deliverables/claude_export_WITH.md) |
| Claude 导出（无 insights） | [claude_export_WITHOUT.md](../../insights-share/validation/reports/deliverables/claude_export_WITHOUT.md) |
| 服务器启停导出 | [server_host_export.txt](../../insights-share/validation/reports/deliverables/server_host_export.txt) |
| wiki 上传导出 | [wiki_upload.txt](../../insights-share/validation/reports/deliverables/wiki_upload.txt) |
| 交付物总览 | [DELIVERABLES_SUMMARY.html](../../insights-share/validation/reports/deliverables/DELIVERABLES_SUMMARY.html) |
| 终端快照 | [terminal_snapshot.md](../../insights-share/demo_docs/terminal_snapshot.md) |
