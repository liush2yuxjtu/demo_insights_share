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

### 用户端残留项（Agent 边界外）

- 右 pane Claude REPL 内实际触发 skill 并看到 manifest/缓存 + statusline `[share ✓ N/today]` 递增：**需用户 attach `tmux attach -t start_demo_verify` 后手动执行**。
- 这与 2026-04-23 上轮 finish_log S11 条目一致（"tmux 双 pane attach + F12 退出 ⏸️ Bash tool 不能 attach"）。

## PASS / FAIL 总结

| 层级 | 状态 | 说明 |
|---|---|---|
| B 静态契约 | ✅ PASS | 7 项契约全绿，与 commit trail `93a93fb…958e6ac` 对齐 |
| A1 tmux register | ✅ PASS | session 活 + pipe-pane 镜像活 |
| A2 start.demo.sh 7 步 | ✅ PASS | 沙箱 + hook + skill + MiniMax + daemon + tmux + 双 pane 全绿 |
| A3 daemon 4 端点 | ✅ PASS | healthz / insights / search / topics(flat=400) 全对齐契约 |
| A4 guide_loop 推进 | ✅ PASS | 左 pane 检测 skill 已装 + 等 user 触发 |
| A5 用户 REPL 真触发 | ⏸️ | Agent 不能 attach，需用户手动 tmux attach 验证 |

**最终裁决：PASS**（Agent 可验证范围全绿；A5 交用户）。

## 后续操作指引

1. 用户要真看 demo：在任何 Terminal 里 `tmux attach -t start_demo_verify`（macOS Terminal 窗口已弹出）
2. 双 pane 内按 guide 指示在右 pane Claude REPL 输入 postgres 故障 prompt
3. F12 退出 demo，触发 start.demo.sh 的 trap cleanup（`rm -rf /tmp/demo-sandbox-*`）
4. 如需复现这次 QA：`bash .claude/skills/register-session/register-session.sh start_demo_verify && tmux send-keys -t start_demo_verify "unset TMUX && bash start.demo.sh" Enter`
