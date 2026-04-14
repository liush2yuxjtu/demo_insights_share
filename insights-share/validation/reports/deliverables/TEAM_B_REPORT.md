# Team B 交付报告 — proposal/validation 线性时间线

生成于 2026-04-14 · 任务 #2 · owner: team-b

## 交付清单

| 文件 | 说明 |
|------|------|
| `insights-share/validation/tools/extract_linear_timeline.py` | 从 Claude Code 会话 jsonl 抽取按时间排序的关键词事件（默认读 `~/.claude/projects/-Users-m1-projects-demo-insights-share/*.jsonl`） |
| `insights-share/validation/reports/deliverables/proposal_linear.html` | 关键词 `proposal.md` 的线性时间线，42 条事件 |
| `insights-share/validation/reports/deliverables/validation_linear.html` | 关键词 `validation.md` + `validation/` 的线性时间线，118 条事件 |

## 执行流程

1. 采样 jsonl 顶层结构，确认 `permission-mode` / `file-history-snapshot` 行无 `timestamp`，`message.content` 既可能是字符串也可能是 list（含 `tool_use` / `tool_result`）。
2. 实现 `extract_linear_timeline.py`：用 pathlib + json 标准库；`flatten_content` 把 list 形态的 tool_use input（含 file_path 等字段）也压到可搜索文本，否则匹配率会从 ~25% 退化到 ~3%；`sanitize` 去 XML 标签、折叠空白、截断到 200 字。`JSONDecodeError` 仅 warning 跳过。
3. 用脚本生成两份 JSON 数据（42 / 118 条），再用渲染脚本写出两份 HTML。
4. HTML 复用 `index.html` 前 124 行的 `:root` 调色板与 `body / header / section / .cmd / .badge`，并新增 `.timeline / .meta / .file / .summary / .sources` 等局部样式。
5. `open -a "Google Chrome"` 弹出两份 HTML 预览。

## 关键设计与约束

- 脱敏：每条事件只保留 `ts / actor / 前 200 字 summary / 来源文件名`。XML/HTML 标签全部剥离，禁止输出完整 prompt。
- 数据源：6 份 jsonl 全部参与，时间戳跨度 2026-04-13 ~ 2026-04-14。
- 零第三方依赖；脚本 CLI 支持 `--glob` / `--keyword` / `--out`，便于后续 Team D 复用。
- 未触碰 `demo_codes/` 与 `.claude/settings.json`。

## 验证

| 命令 | 预期 | 实际 |
|------|------|------|
| `python3 insights-share/validation/tools/extract_linear_timeline.py --keyword proposal.md --out -` | 输出 ≥ 30 条事件 JSON，按 ts 升序 | 42 条，按 ts 升序 |
| `python3 insights-share/validation/tools/extract_linear_timeline.py --keyword validation.md --keyword 'validation/' --out -` | 输出 ≥ 50 条事件 | 118 条 |
| `ls insights-share/validation/reports/deliverables/*.html` | 2 个文件 | `proposal_linear.html` 21 KB / `validation_linear.html` 54 KB |
| `open -a "Google Chrome" <两个 html>` | 浏览器弹出 | 已弹出 |

## 给 Team D 的接口

- 复用脚本：`python3 insights-share/validation/tools/extract_linear_timeline.py --keyword <kw> --out <path.json>`
- 两份 HTML 已就位于 `insights-share/validation/reports/deliverables/`，可直接收编入最终证据 HTML。
