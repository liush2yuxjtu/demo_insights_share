# Meta Self-Verify: CLAUDE.md 修改必跑 Agent-Judge 状态灯

## 规则

每次编辑 `CLAUDE.md`（新增 / 修改 / 删除规则）后，必须跑 **agent-judge 双探针循环**，由另一个 agent 评判响应，而不是硬编码关键词匹配。收敛后才算改动收尾。

## 两档探针

| 档位 | 命令 | 成本 | 可靠性 | 用途 |
|------|------|------|--------|------|
| fast | `claudefast -p "<q>"` | 低 | 中 | loop 内反复跑 probe + judge |
| reliable | `claude -p "<q>"` | 高 | 高 | fast 循环连续失败时最后托底 |

原则: **能 fast 就 fast；只有 fast 收敛不了才升级 reliable**。

## 探针 A：状态灯 probe

```
claudefast -p "what would happen if we say to claude code CLI in this project 'start'"
```

## 探针 B：agent-judge

拿到 A 的响应后，交给独立 claudefast 实例当裁判：

```
claudefast -p "
你是规则落地裁判。请判断下面这段响应是否体现了 CLAUDE.md 里 'start bootstrap 指令' 规则的意图（bootstrap 读四文件 + proposal/INDEX.md + 全量扫描全部 proposal + 识别新增/未落地 proposal + 只对这些项逐条实现 + self-verify + PASS/FAIL 收尾）。

响应:
<<<
{probe_response}
>>>

只输出合法 JSON，schema:
{
  \"verdict\": \"PASS\" | \"REFINE\" | \"FAIL\",
  \"reason\": \"一句话说明\",
  \"suggested_patch\": \"若 REFINE，给出 CLAUDE.md 行改动建议；否则空串\"
}
"
```

## 三种判决

| verdict | 动作 |
|---------|------|
| `PASS` | 收尾，写 log，结束 |
| `REFINE` | 按 `suggested_patch` 改 CLAUDE.md → 原子 commit → 下一轮 fast 循环 |
| `FAIL` | 跳出 fast 循环，直接升级 reliable 档位跑一次托底评判 |

## 升级策略

- fast loop 最多 `MAX_FAST = 5` 轮
- 连续 2 轮 `REFINE` 但 `verdict` 未进展（suggested_patch 相似 / hits 不增）→ 判定停滞，强制升级 reliable
- reliable 档位只跑 **一次** `claude -p` 判决，结果作为最终裁决
- reliable 仍判 `FAIL` → 上抛用户，不得沉默收尾

## 为什么用 agent-judge 而不是 grep 关键词

- 规则措辞会演进，硬编码 `["bootstrap", "proposal"]` 这类 list 会随规则改名而腐烂
- CLI 响应可能用同义词（"引导" / "启动" / "读文档后实现"），关键词匹配误判 FAIL
- agent-judge 读原始意图，容忍措辞漂移，精度高于 substring match
- 成本差距由两档探针吸收：95% 场景 claudefast 已够，保留 claude -p 做 tie-breaker

## 状态灯存档

每一轮写一行到 `insights-share/validation/reports/meta_verify.log`：

```
[ISO8601] [CLAUDE.md short-hash] [tier=fast|reliable] [iter=N] [verdict] [reason]
```

PASS / FAIL 终局各单独落一条 `--- terminal ---` 分隔符。

## 非目标

- 不替代人工 code review
- 不判规则"设计得好不好"，只判"CLI 推理路径有没有真正吃到这条规则"
- 不强制 100% 通过 gate，允许用户 `--override` 跳过（必须写 log reason）
