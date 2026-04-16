# A/B Demo 资产修复计划

## Context

`examples/A_without.human.md`、`examples/B_with.human.md` 是 insights-wiki A/B 对照演示的核心资产，用于向观众证明 "装 skill vs 不装 skill" 的效果差异。最近验证发现三个互相独立的缺陷，如不修复会让演示失去说服力：

1. **A 组污染**：`A_without.human.md` 实际录制的是 WITH 会话（skill 被加载、`alice-pgpool-2026-04-10` 被引用、prompt 是 WITH 版本），与文件名和 A 轮预期完全相反。`A_without.md`（claude -p 导出）是干净的，但 human 版污染会导致 GitHub Pages index.html 链接展示错误素材。

2. **Stop hook JSON schema 错误**：`insights_stop_hook.py:140-151` 输出 `{hookSpecificOutput: {hookEventName: "Stop", additionalContext: ...}}`，但 Claude Code Stop hook schema 不允许 `additionalContext` 字段（仅 `UserPromptSubmit` 和 `PostToolUse` 合法）。B 组录屏里出现醒目的 `Stop hook error: JSON validation failed` 红字，观众会误以为整个 skill 坏了。

3. **B 组被截断**：`B_with.human.md:156` 显示 `⎿ Interrupted`，原因是 `run_human_AB.sh` 的 `WAIT_ANSWER=150s` 固定等待太短，Opus 思考 88 秒 + 生成大段 SQL 超过了该窗口，随后 `/export` 打断了正在生成的内容。

预期产出：A/B 两份 human 录屏内容正确、无红字错误、完整结束，并通过 `grep -c alice-pgpool-2026-04-10` 明确区分（A=0，B≥1）。

---

## 修复方案

### Fix 1 — Stop hook 去掉非法 `additionalContext`

**文件**：`insights-share/demo_codes/hooks/insights_stop_hook.py`

**改动**：删除第 140-151 行的 `payload = {...}` 与 `sys.stdout.write(json.dumps(payload))`。

**保留**：第 129-133 行的 `insights_cache.persist(top)` 写盘逻辑不变 —— 下一轮的 hint 注入由 `UserPromptSubmit` 事件注册的 `insights_prefetch.py`（settings.json:14-24）从 `~/.cache/insights-wiki/` 读取缓存并注入，这是架构里本来就有的正确路径。Stop hook 只负责"搜索+落盘缓存"即可。

**为何不走"改注册到 UserPromptSubmit"方案**：`UserPromptSubmit` 事件点已被 `insights_prefetch.py` 占用，两个脚本共用同一个事件会互相覆盖 `additionalContext`；此外 Stop hook 的语义是"Claude 刚说完话"，改到 UserPromptSubmit 会错过 assistant last-turn 文本。

### Fix 2 — `run_human_AB.sh` 强化 A 轮净室隔离

**文件**：`examples/run_human_AB.sh`

**改动 2a**：在 `prepare_workspace_a()` 函数体内（第 70-75 行）追加显式清理，作为 `backup_active_skills` 的冗余保险：

```
rm -rf "${SKILL_DST}" "${SKILL_SERVER_DST}"
```

然后加一条断言：若 `ls ~/.claude/skills/insights-wiki*` 仍能找到条目则 `exit 7`。

**改动 2b**：把 `WAIT_ANSWER=150` 改为 `WAIT_ANSWER=240`（Line 36），给 Opus 充足生成时间，避免 `/export` 截断。

**改动 2c**（可选加固）：在 Step 5 循环里加入 "pane 稳定检测"——用 `tmux capture-pane -p` 每 10s 采样一次，若连续两次 diff 为空则判定 Claude 已停止生成，提前跳出等待。纯 `sleep` fallback 保留。

### Fix 3 — 重新录制 A/B 资产

**前置条件**：Fix 1 + Fix 2 已落地。

**步骤**：
1. 确认 `~/.claude/skills/` 下不存在 `insights-wiki*` 任何残留
2. `bash examples/run_human_AB.sh`
3. 脚本会自动：备份 → 清空 → A 轮（WITHOUT）→ 清空 → clone → 装 skill → 启 daemon → B 轮（WITH）→ 恢复备份
4. 产物落到 `/tmp/demo_insights_A/A_without.human.md` 和 `/tmp/demo_insights_B/B_with.human.md`，脚本最后 cp 回 `examples/`

---

## 关键文件清单

| 路径 | 角色 | 改动 |
|------|------|------|
| `insights-share/demo_codes/hooks/insights_stop_hook.py` | Stop hook 脚本 | 删除第 140-151 行 payload 输出 |
| `insights-share/demo_codes/.claude/settings.json` | hook 注册 | 不动（架构正确） |
| `insights-share/demo_codes/hooks/insights_prefetch.py` | UserPromptSubmit hook | 不动（已负责 hint 注入） |
| `examples/run_human_AB.sh` | A/B 录制脚本 | 加显式 rm + 改 WAIT_ANSWER |
| `examples/A_without.human.md` | A 录屏资产 | 由脚本重新生成 |
| `examples/B_with.human.md` | B 录屏资产 | 由脚本重新生成 |

## 不需改动的文件

- `examples/A_without.md` / `B_with.md`（claude -p 导出，已正确）
- `examples/validate_commands.sh`（逻辑正确）
- `insights-share/validation/test_examples_demo_scripts.py` / `test_ab_demo_plan.py`（当前 7/7 全过）

---

## 验证方案

### 单元验证（改完脚本后立即跑）

```bash
cd /Users/m1/projects/demo_insights_share
python3 -m pytest insights-share/validation/test_examples_demo_scripts.py \
                  insights-share/validation/test_ab_demo_plan.py -v
```

预期：7 passed（与现状保持）。

### Stop hook 手工验证

```bash
cd insights-share/demo_codes
echo '{"transcript_path":"/tmp/nonexistent.jsonl"}' | \
  .venv/bin/python hooks/insights_stop_hook.py
echo "exit=$?"
```

预期：exit=0，stdout 为空（不再输出非法 JSON），stderr 有 debug 日志。

### 内容级 A/B 差异验证（录制完成后）

```bash
# A 轮应零引用
grep -c alice-pgpool-2026-04-10 examples/A_without.human.md
# 预期：0

# B 轮应多次引用
grep -c alice-pgpool-2026-04-10 examples/B_with.human.md
# 预期：≥ 1

# A 轮不应出现 Skill(insights-wiki) 加载痕迹
grep -c "Skill(insights-wiki)" examples/A_without.human.md
# 预期：0

# B 轮不应出现 Stop hook 红字错误
grep -c "Stop hook error" examples/B_with.human.md
# 预期：0

# B 轮不应被截断
grep -c "Interrupted" examples/B_with.human.md
# 预期：0
```

### 端到端演示复现

```bash
bash examples/validate_commands.sh   # 按三步执行
# 最后一步 grep -c 应输出：
#   A_without.log:0
#   B_with.log:<N>   (N ≥ 1)
```

---

## 执行顺序

1. Fix 1（改 insights_stop_hook.py）
2. Fix 2（改 run_human_AB.sh）
3. 跑单元测试确认 7/7
4. 手工验证 Stop hook 退出码与 stdout
5. 执行 Fix 3 重新录制
6. 跑内容级 grep 验证
7. 打开 `examples/index.html` 在浏览器确认页面引用的新素材展示正确
