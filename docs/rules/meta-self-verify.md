# Meta Self-Verify: CLAUDE.md 修改必跑状态灯

## 规则

每次编辑 `CLAUDE.md`（新增规则 / 修改规则 / 删除规则）后，必须立即跑一条 `claudefast` 探针作为**状态灯**，确认新规则已被 CLI 实际采纳，再判定改动是否收尾。

## 触发条件

- 任何对 `CLAUDE.md` 的 Write / Edit 操作完成后
- 任何对 `docs/rules/*.md` 的改动若直接被 `CLAUDE.md` 索引，也跑一次

## 状态灯命令

```bash
claudefast -p "what would happen if we say to claude code CLI in this project 'start'"
```

## 判定

| 响应特征 | 状态 | 含义 |
|---------|------|------|
| 提到 bootstrap / 读 proposal.md / 读 proposal/INDEX.md / self-verify / 按 proposal 实现 | `PASS` | CLAUDE.md 已被正确加载并生效 |
| 回答 "start 不是内置命令" / 当普通消息处理 / 只列出 start_*.txt 文件 | `FAIL` | 规则未落地，需 debug 索引或文件路径 |
| 部分关键词命中 (<3 个) | `PARTIAL` | 规则生效但描述不够硬，需 refine 措辞 |

## 失败处理

`FAIL` / `PARTIAL` → 走调试循环：

1. 检查 `CLAUDE.md` 表格行语法（符合 `claude-md-format.md`）
2. 检查 `docs/rules/<file>.md` 链接是否 404
3. 检查规则描述是否含关键触发词 (`start` / `bootstrap` / `proposal`)
4. refine 措辞 → 重新 Edit → 再跑状态灯，直到 `PASS`
5. 连续 5 次失败 → 上抛给用户，不得沉默收尾

## 状态灯输出存档

每次跑完把响应追加到 `insights-share/validation/reports/meta_verify.log`（append-only），字段：

```
[ISO8601 timestamp] [CLAUDE.md hash] [PASS|PARTIAL|FAIL] [hits/total]
<response 前 200 字>
---
```

## 为什么

CLAUDE.md 是 agent 行为的唯一声明入口。光写不验 = 把规则留在磁盘上但从没进过 CLI 的实际推理路径。状态灯把"规则是否被 CLI 读到"变成**可观测信号**，消除"我以为加了但没生效"这类静默失败。

## 非目标

- 不测试规则"对不对"，只测试"有没有被 CLI 读到并理解"
- 不替代人工 code review
- 不要求 100% 自动化过 gate，允许人工 override（override 必须写日志 reason）
