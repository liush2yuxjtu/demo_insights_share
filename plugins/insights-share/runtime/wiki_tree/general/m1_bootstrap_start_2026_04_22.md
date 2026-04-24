---
{
  "id": "m1-bootstrap-start-2026-04-22",
  "title": "start bootstrap: 全量扫描 proposal 再 self-verify 闭环",
  "author": "m1",
  "confidence": 0.88,
  "tags": ["start", "bootstrap", "proposal", "self-verify", "loop"],
  "status": "active",
  "applies_when": ["用户发送裸消息 start"],
  "do_not_apply_when": ["用户已指定具体 task", "用户已提供完整上下文说明跳过了 proposal 读取"],
  "topic_id": "execution-patterns",
  "label": "good",
  "label_note": "先读 proposal/INDEX.md + 全部 proposal_*.md，识别新增/未落地，按顺序进入 edit→test→find bugs→edit 闭环",
  "raw_log": null
}
---

# start bootstrap: 全量扫描 proposal 再 self-verify 闭环

> author: m1 · confidence: 0.88

## 触发条件

用户发送裸消息 `start`（无其他参数）。

## 强制流程

1. **读 proposal/INDEX.md** + 全部 proposal_*.md（含 CEO 级 plan）
2. **识别状态**：
   - `已落地` — 已在 code 中实现
   - `新增` — 前次 bootstrap 后新加的 proposal
   - `未落地` — 写了但还没做
3. **按顺序执行**：对每个新增/未落地 proposal，进入闭环：
   ```
   edit code → run code/test → find bugs → edit code
   ```
4. **self-verify**：每步用 agent-judge 双探针验证
5. **PASS/FAIL 收尾**：给出明确判定

## 最低证据标准

输出必须包含：
1. 四文件读取确认
2. proposal 状态清单（每条：已落地/新增/未落地）
3. 已跳过项
4. 实际 commit 列表
5. PASS/FAIL 收尾

## Applies when

- 用户发送裸消息 start

## Do NOT apply when

- 用户已指定具体 task
- 用户已提供完整上下文说明跳过了 proposal 读取
