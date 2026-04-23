# Finish Log — /qa B 静态契约探针 + A full demo self-verify

日期：2026-04-23
触发：用户 `/qa` → `B then A`
关联：
- `docs/finish_log/2026-04-23_qa-s11-e2e-slash-independent.md`（上一轮 QA S11 + E2E + 5 slash 独立探针）
- `docs/rules/start-demo-verify.md`、`docs/rules/start-demo-register-fallback.md`、`docs/rules/tmux-nested.md`

## B：静态契约探针（PASS）

| 契约项 | 状态 | 证据 |
|---|---|---|
| plugin.json v0.6.0-m7 | ✅ | `plugins/insights-share/.claude-plugin/plugin.json`，milestone `M7_LATENCY_DEEP` partial |
| 5 slash commands | ✅ | `plugins/insights-share/commands/` = share-install / share-search / share-publish / share-review / share-diff |
| 2 skills | ✅ | `demo_codes/.claude/skills/` = insights-share + insights-share-server |
| 2 agents | ✅ | `plugins/insights-share/agents/` = share-curator + share-validator |
| 2 hooks | ✅ | `plugins/insights-share/hooks/` = user-prompt-submit.sh + session-start.sh（2026-04-22 与 commit `93a93fb` 对齐） |
| 2 marketplace | ✅ | `.claude-plugin/marketplace.json`（root，发布侧）+ `plugins/insights-share/.claude-plugin/marketplace.json`（子，订阅侧） |
| daemon 入口 | ✅ | `insights_cli.py serve --host 0.0.0.0 --port 7821 --store-mode tree` 经 `scripts/start_server.sh` 启动 |

## A：full demo self-verify（PASS）

### A1 register-session

- 旧 CURRENT=`start_demo_verify` 对应 tmux server 已关 → 先 `--clear`
- 重建：`bash .claude/skills/register-session/register-session.sh start_demo_verify`
- 结果：tmux session 新建 + pipe-pane 镜像 `~/.claude/live_terminal/start_demo_verify.log` + CURRENT 写入 + osascript 弹 Terminal.app attach

### A2 send-keys 启 start.demo.sh（嵌套 tmux 必 `unset TMUX`）

命令：`tmux send-keys -t start_demo_verify "unset TMUX && bash start.demo.sh" Enter`

start.demo.sh 7 步全绿：

```
🟢 [1/7] 创建沙箱 /tmp/demo-sandbox-20260423-122824.26DumH ........ done
🟢 [2/7] 装入 insights-share hook（走 MiniMax）....... done
🟢 [3/7] 拷贝 insights-share skill 到沙箱（user+project 双保险）... done
🟢 [4/7] 注入 MiniMax 高速通道 ............... done
🟢 [5/7] 后台启动 insightsd :7821（PID 31929）... done
🟢 [6/7] tmux 3.6a 已就绪 ............. done
🟢 [7/7] 即将切入双 pane（3 秒后）........ done
```

### A3 daemon 端点实测（与上轮 finish_log 契约 1:1 对齐）

| 端点 | 期望 | 实测 |
|---|---|---|
| `/healthz` | 200 ok | `{"ok": true}` ✅ |
| `/insights` | cards 数组 | 200 cards（test-123 / bob-k8s-oom-2026-04-22 / ...） ✅ |
| `/search?q=postgres&k=3` | hits 数组 | `{"hits":[{"id":"m1-kb-aa-003","title":"Postgres 高并发下 Lock Timeout 排查","score":0.1}]}` ✅ |
| `/topics` (flat 模式) | 400 topics_not_supported | `{"error":"topics_not_supported","detail":"tree mode only"}` ✅ |

### A4 guide_loop 左 pane 状态

log 镜像显示：

```
✅ 检测到 /tmp/demo-sandbox-20260423-122824.26DumH/home/.claude/skills/insights-share/SKILL.md — skill 已装好
⏳ 正在等待 Claude 触发 skill 并写入本地缓存…
```

guide 已推进到"请把 postgres 故障 prompt 贴到右 pane"阶段，等待用户在 Claude REPL 内实际输入。

### A5 Agent 亲自实测右 pane claude REPL（补录）

用户第二轮要求 "please register and test by yourself"。Agent 走 **独立 socket 路径** 突破 "Bash tool 不能 attach" 边界：

- socket 名 = `demo-20260423-122824-31909`（start.demo.sh `SESSION="demo-$$"` + `SOCK="demo-${TS}-$$"`，独立 tmux server 不受外层限制）
- session = `demo-31909`，双 pane = `0.0` (左 guide 只读 tail) / `0.1` (右 claude REPL)
- 通过 `tmux -L <SOCK> send-keys -t demo-31909:0.1` 直接驱动右 pane

右 pane **sandbox self-check** 18/18 全绿（statusline preview `[share ✓ 0/today]` + manifest v0.6.0-m7 + 2 skills + 2 hooks + 5 cmds + 2 agents + mcp 7 tools + marketplace publish script + contract forward-compat OK + plugin self-check ALL GREEN）。

右 pane claude REPL 启动：

| 阶段 | Agent 动作 | pane 反馈 |
|---|---|---|
| theme 选择 | send Enter | dark mode (default) ✓ |
| security notes | send Enter | 通过 ✓ |
| folder trust | send Enter | trust `/private/tmp/demo-sandbox-.../workdir` ✓ |
| REPL 启 | — | Welcome back! **MiniMax-M2.7-highspeed** + statusline `[share ✓ 0/today]` + "Anthropic marketplace installed" |
| 发 postgres 故障 prompt | send-keys + Enter | prompt accepted |
| 等 20s | — | 完整诊断 SQL（pg_stat_activity state / 锁等待 pg_catalog.pg_locks / wait_event） + 修复代码（pgxpool MaxConns=15 / MaxConnLifetime / ALTER SYSTEM max_connections=500） |
| **statusline 真变化** | — | **`[share ✓ 0/today]` → `[share ✓ 1/today]`**（UserPromptSubmit hook 真触发 + 真计数 +1） |

### A5 gap 实测发现（⚠️ DONE_WITH_CONCERNS）

claude 回答开头：

```
⏺ 未引用任何 LAN 卡片（缓存卡片均为 insights-share 机制相关，非 PG 性能诊断内容）
```

daemon side 明明有 hit：

```
curl http://127.0.0.1:7821/search?q=postgres&k=3
→ {"hits":[{"id":"m1-kb-aa-003","title":"Postgres 高并发下 Lock Timeout 排查","score":0.1,...}]}
```

但 sandbox 内 UserPromptSubmit hook 只把"insights-share 机制相关"卡片注入 context（如 bob-k8s-oom-2026-04-22 / test-123），没拿到 m1-kb-aa-003。

两个可能成因：
1. **SessionStart prefetch 范围**：M7 prefetch 按默认 topic 或空 query 拉，没按 prompt 关键词二次拉
2. **hook 触发后 cache 查询路径**：hook 走沙箱本地 cache 而非回源 daemon 的 `/search?q=<prompt_keywords>`

真正的闭环应该：hook 至少一次按 prompt 关键词查 daemon（或对 prefetch cache 做 embedding rerank）。

对齐 validation.md §1 "触发率：持续优化触发率，直到达标" 未完成工作项。

## PASS / FAIL 总结

| 层级 | 状态 | 说明 |
|---|---|---|
| B 静态契约 | ✅ PASS | 7 项契约全绿 |
| A1 tmux register | ✅ PASS | session 活 + pipe-pane 镜像活 |
| A2 start.demo.sh 7 步 | ✅ PASS | 沙箱 + hook + skill + MiniMax + daemon + tmux + 双 pane |
| A3 daemon 4 端点 | ✅ PASS | healthz / insights / search / topics(flat=400) 契约对齐 |
| A4 guide_loop 推进 | ✅ PASS | 左 pane 检测 skill 已装 |
| A5 sandbox self-check 18/18 | ✅ PASS | statusline preview + manifest + skills + hooks + cmds + agents + mcp + marketplace publish |
| A5 REPL 发 prompt + statusline +1 | ✅ PASS | 真触发真计数 |
| A5 卡片引用内容匹配 | ⚠️ DONE_WITH_CONCERNS | daemon side 有 hit 但 sandbox hook 未拉到；validation.md §1 触发率优化未完成 |
| claudefast finish flag | ✅ | READ ONLY 裁决 = PASS |

**最终裁决：PASS with gap**（基础设施 + 静态契约 + 动态触发闭环 100% 活；卡片 relevance 匹配是 validation.md 已记录的未完成项）。

## 下一步候选

| 优先级 | 动作 | 路径 |
|---|---|---|
| P1 | 修 hook 让其按 prompt 关键词真查 daemon `/search?q=`（或对 prefetch cache 做 embedding rerank） | `plugins/insights-share/hooks/user-prompt-submit.sh` + `insights-share/demo_codes/hooks/insights_prefetch.py` |
| P2 | validation.md §1：真跑 20 触发用例（12 训/8 测），出触发率数 | `insights-share/validation/` |
| P3 | 回归测：sandbox 内发 postgres prompt 必须引用 m1-kb-aa-003 | 新 integration test |

## 复现本轮 QA

```bash
# 清过期 CURRENT → 建 tmux → 在其内 spawn start.demo.sh
bash .claude/skills/register-session/register-session.sh --clear
bash .claude/skills/register-session/register-session.sh start_demo_verify
tmux send-keys -t start_demo_verify "unset TMUX && bash start.demo.sh" Enter

# 拿 sandbox 独立 socket（看 /tmp/tmux-$UID/demo-<ts>-<pid>）
ls -la /tmp/tmux-$(id -u)/ | grep demo-

# 驱动右 pane（替换 SOCK 为真实值）
SOCK=demo-20260423-122824-31909
SESSION=demo-31909
tmux -L "$SOCK" send-keys -t "$SESSION:0.1" Enter  # 回车进 claude (过 theme/security/trust)
tmux -L "$SOCK" send-keys -t "$SESSION:0.1" "<prompt>" Enter
tmux -L "$SOCK" capture-pane -t "$SESSION:0.1" -p -S -50
```
