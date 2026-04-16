# 修复计划：消除 B 侧首次 prompt 的缓存竞态

## Context

**问题**：`run_human_AB.sh` 的 B 侧在 `UserPromptSubmit` hook 里用 `&` 后台运行
`insights_prefetch.py`（从 daemon 拉卡片写到 `~/.cache/insights-wiki/manifest.json`）。
但此时 Claude 已经开始处理 COMMON_PROMPT，当模型执行到第二步
`!cat ~/.cache/insights-wiki/manifest.json` 时，prefetch 可能还没完成，导致：

- manifest.json 不存在 → 模型写"未引用任何 LAN 卡片"
- B 侧 `alice-pgpool-2026-04-10` 计数 = 0 → `run_tmux_human` Step 10 以 exit 11 报错

`insights_stop_hook.py`（Stop hook）只在 Claude **回复结束后**才执行，第一轮 prompt
时它还没跑，所以 manifest 不存在不是 Stop hook 的问题——是 prefetch 的竞态。

**解决思路**：在 `prepare_workspace_b()` 里，daemon 健康检查通过后，**同步运行一次
prefetch** 来预热缓存，保证 manifest.json 在 Claude 会话启动前已落盘。
hook 里的 `&` 保持不变（为后续轮次服务）。

---

## 改动 1：`examples/run_human_AB.sh`

**位置**：`prepare_workspace_b()` 函数末尾，紧接 daemon 健康检查之后（`exit 3` 那行后面）。

**添加以下代码块**（约 6 行）：

```bash
log "B 轮前置：同步预热缓存（消除 UserPromptSubmit & 竞态）"
"${PYTHON_BIN}" "${CLONE_DIR}/insights-share/demo_codes/hooks/insights_prefetch.py"
if [ ! -f "${CACHE_DIR}/manifest.json" ]; then
  log "✗ B 轮缓存预热失败：${CACHE_DIR}/manifest.json 未生成"
  exit 18
fi
log "B 轮前置：✓ 缓存预热完成：$(cat "${CACHE_DIR}/manifest.json")"
```

**不改动**：
- `UserPromptSubmit` hook 里的 `insights_prefetch.py >/dev/null 2>&1 &`（后台仍保留，用于后续轮次）
- COMMON_PROMPT.txt（测试强制校验文本一致性，不能改）
- A 侧逻辑（净室隔离不受影响）

---

## 改动 2：`insights-share/validation/test_examples_demo_scripts.py`

**位置**：`test_run_human_ab_replays_current_fix_state_and_validates_exports` 函数末尾。

**添加两行断言**：

```python
assert '同步预热缓存' in script
assert 'B 轮缓存预热失败' in script
```

---

## 影响范围

| 文件 | 变更类型 | 风险 |
|------|---------|------|
| `examples/run_human_AB.sh` | 在 `prepare_workspace_b()` 末尾追加 6 行 | 低：不改变 A 侧 / 不改 hook / 不改 COMMON_PROMPT |
| `insights-share/validation/test_examples_demo_scripts.py` | 追加 2 行断言 | 低：只添加新断言，不修改现有断言 |

---

## 验证方法

1. 运行测试套件：
   ```bash
   cd /Users/m1/projects/demo_insights_share
   python -m pytest insights-share/validation/test_examples_demo_scripts.py -v
   ```
   期望：所有测试 PASS，包括新增的 `同步预热缓存` 和 `B 轮缓存预热失败` 断言。

2. 检查 `run_human_AB.sh` 中预热代码位置正确：
   ```bash
   grep -n "同步预热缓存\|B 轮缓存预热失败\|exit 18" examples/run_human_AB.sh
   ```
   期望：三行都出现在 `prepare_workspace_b` 函数范围内（行号 296～327 之间）。

3. 完整 A/B 录制验证（需要 daemon + env）：
   ```bash
   bash examples/run_human_AB.sh
   ```
   期望：B 侧 `alice_count >= 1`，A/B prompt equality gate PASS。
