# self-verify-loop plan

- task: 基于 judge REFINE verdict，修订 upload_plan.md 的 6 处 gap
- project: demo_insights_share
- branch: main
- generated: 2026-04-22T13:23:40+08:00
- N budget: 3
- mode: plan-only（未执行）

## 原 verdict 摘要

judge 命中 8 项 covered，6 项 missing：
- CRITICAL: daemon 启动路径相对/绝对不统一
- CRITICAL: extract_lessons.py 输出 scenario/decision，daemon 需要 title/label，build_card() 缺 transform
- MEDIUM: --store-mode 参数值未验
- MEDIUM: judge probe prompt 缺 5 项检查清单
- LOW: daemon already-running 检查缺失
- LOW: MIN_ASSISTANT_CHARS=80 与 plan 丢弃条件(<50字)不一致

## pseudo for-loop

```
for i in 1..N:
    # iter 1: 修订 upload_plan.md，合并全部 6 处 gap
    artifact_v1 = edit upload_plan.md:
        - 统一 daemon 启动命令为绝对路径 /Users/m1/projects/demo_insights_share/insights-share/demo_codes
        - build_card() 输出 daemon 兼容格式（title←scenario截60字、label←decision、confidence=0.4）
        - 验证 --store-mode tree 参数（查 server.py）
        - judge probe prompt 写入"检查 5 项：输入/输出/规则/步骤/安全"
        - 添加 daemon already-running 检查（查 /tmp/insightsd.pid 或 curl 健康探测）
        - extract_lessons.py MIN_ASSISTANT_CHARS 改为 50（与 plan 一致）

    verdict = judge(task, artifact_v1, prior_verdicts=[])
    if "ship" in verdict → break
    carry (artifact_v1, verdict) forward

    # iter 2: 若仍 REFINE，针对性补硬缺失
    artifact_v2 = apply remaining critical fixes identified in verdict
    verdict = judge(task, artifact_v2, prior_verdicts=[verdict])
    if "ship" in verdict → break

return (artifact_v2, verdict, trace)
```

## 本次裁判切入点（自由文本）

**审什么**：
1. 6 处 gap 是否全部被修订到（路径统一、transform 步骤存在、probe prompt 含 5 项、already-running 检查存在、MIN_CHARS 修正）
2. plan 其他部分（Mapper、pre-topic 注册脚本、G1-G5 gate）是否因此引入新矛盾
3. 修订后 plan 是否可执行——步骤顺序是否产生新的前置依赖

**怎么判 ship**：
- 裁判说"no blockers"或"ready to execute" → 停
- 裁判列出仍需修复的具体项 → 下一轮针对性改
- 裁判说"FAIL" → 说明灾难性错误，需大改

## 已知待修复项清单

| # | 优先级 | 问题 | 修复方向 |
|---|--------|------|----------|
| 1 | CRITICAL | daemon 启动路径不一致 | 统一为 /Users/m1/projects/demo_insights_share/insights-share/demo_codes |
| 2 | CRITICAL | build_card() 缺 title/label transform | 新增 transform 步骤，或在 build_card() 输出 daemon 格式 |
| 3 | MEDIUM | --store-mode tree 未验 | 查 server.py，确认 tree 是合法值 |
| 4 | MEDIUM | judge probe prompt 缺 5 项清单 | 将 5 项检查内容写入 probe prompt 模板 |
| 5 | LOW | daemon already-running 缺失 | 启动前检查 /tmp/insightsd.pid 或 curl 健康探测 |
| 6 | LOW | MIN_ASSISTANT_CHARS=80 vs plan<50 | extract_lessons.py 改为 50 或 plan 注明 80 |
