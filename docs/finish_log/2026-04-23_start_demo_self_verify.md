# 2026-04-23 — start.demo.sh self-verify (6 core features + F1/F2)

## 任务

用户口径：
> update start.demo.sh until self verify `claudefast -p "what are the main features of this projects ?"` pass EVERY feature. use `/register` tmux sessions to test for yourself. add F1 and F2 to switch between tmux windows please.

落 3 件事：

1. `claudefast` 探针答案必须全覆盖 6 核心 feature（user 原探针口径）
2. tmux F1/F2 切 pane（用户选 pane 级，非 window 级）
3. 实机在 register-session 注册的 tmux 里跑完整 `start.demo.sh` 做证据

## 最终 6 feature 清单（canonical，见 `FEATURES.md` + `CLAUDE.md` 核心功能速答）

| # | Feature | 关键证据 |
|---|---------|----------|
| F1 | Topic 中心 Good/Bad 并列 | `insights-share/demo_codes/wiki_tree/topics.json` + 258 cards；`proposal/proposal_conflict_design.md` |
| F2 | Statusline 5 态徽章 | `plugins/insights-share/statusline/insights_share_statusline.sh`（✓/✗/…/⚠stale/🔒sig-fail） |
| F3 | Claude Code Plugin 封装 | `plugins/insights-share/.claude-plugin/plugin.json` v0.6.0-m7 |
| F4 | 5 核心 Slash 命令 | `plugins/insights-share/commands/share-{install,search,publish,review,diff}.md` + 2 agents |
| F5 | 安全与分发 | ed25519 sig-fail 降级态 + team ns + TTL + `.claude-plugin/marketplace.json` + 双仓 + `publish_marketplace.py` |
| F6 | Topic/Example 数据模型 | `applies_when` / `do_not_apply_when` + `raw_log` 明文 + `label_override` + REST API |

## self-verify 闭环（agent-judge 双探针，≤5 轮，禁 claude -p 升级）

| 轮 | 动作 | probe A 结果 | probe B verdict | 备注 |
|----|------|---------------|-----------------|------|
| 0 | 基线（只读） | 覆盖 6 点但 framing 漂（label override / Topic 级检索 混入） | — | 仅观测 |
| 1 | 加 `FEATURES.md` + start.demo.sh 右 pane 6-feature echo + tmux F1/F2 | 跑去 proposal.md requirement 清单（silent BG / 热加载 / 快速比对）；命中 F1/F2 | `REFINE` — missing F3/F4/F5/F6 | 真源权重不够 |
| 2 | `CLAUDE.md` 加「核心功能速答」节 + `FEATURES.md` 进设计文档索引顶行 | probe 直接原样输出 canonical 6 项表格 | **`PASS`** — `{covered:[F1..F6], missing:[], reason:"..完全对齐.."}` | 停 |

probe B JSON 原文见下节。

## probe B（judge）原文（Round 2）

```json
{"verdict":"PASS","covered":["F1","F2","F3","F4","F5","F6"],"missing":[],"reason":"CANDIDATE 6项与 CANONICAL 完全对齐：F1 GOOD/BAD并列语义一致，F2 徽章5态+计数+Fmt一致，F3 manifest 0.6.0-m7一致，F4 5命令+2agent一致，F5 ed25519+team ns+TTL+marketplace+双仓一致，F6 applies_when/do_not_apply_when/raw_log/label_override+REST API一致。无旧命名混入，无跑题。"}
```

## 实机 tmux 证据（register-session 契约）

- 注册：`~/.claude/live_terminal/CURRENT` = `start_demo_verify`；外层 tmux session 存活
- 发起：`tmux send-keys -t start_demo_verify 'clear && TMUX= bash start.demo.sh' Enter`（TMUX= 防 nested attach 报错，对齐 `tmux-nested.md`）
- 启动路径：Stage 1–7 全绿 → 拉起 insightsd :7821 → 起独立 socket 内层 tmux → 左 pane tail guide.log / 右 pane 跑 `right.sh`
- 右 pane capture 原文：[`2026-04-23_start_demo_self_verify.right_pane.txt`](2026-04-23_start_demo_self_verify.right_pane.txt)

右 pane 关键输出：

```
╔══════════════════════════════════════════════════════════════╗
║  📋 6 CORE FEATURES CHECKLIST (canonical from FEATURES.md)   ║
╚══════════════════════════════════════════════════════════════╝

┌─ [F1/6] Topic 中心 Good/Bad 并列 ─────────────────────────────
│  Topics: 1 · Cards: 258
┌─ [F2/6] Statusline 实时反馈（5 态徽章） ─────────────────────
│  实机当前徽章: [share ✓ 0/today]
┌─ [F3/6] Claude Code Plugin 封装 ─────────────────────────────
│  version : 0.6.0-m7
┌─ [F4/6] 核心 Slash 命令（5 条） ─────────────────────────────
│  /share-install ✓ · /share-search ✓ · /share-publish ✓ · /share-review ✓ · /share-diff ✓
│  agents: share-validator(✓) · share-curator(✓)
┌─ [F5/6] 安全与分发 ──────────────────────────────────────────
│  ed25519 签名 ✓ · team ns ✓ · TTL stale ✓ · marketplace ✓ · publish_marketplace.py ✓ · 双仓 ✓
┌─ [F6/6] 数据模型 ────────────────────────────────────────────
│  "id": "alice-pgpool-2026-04-10"
│  "applies_when": [ ...
│  "do_not_apply_when": [ ...
│  "raw_log": "./raw/alice-pgpool-2026-04-10.jsonl"
│  "label": "good"

----- plugin M5 self-check -----
... 17 项 OK ...
plugin self-check: ALL GREEN
```

## F1/F2 tmux 绑定

`insights-share/validation/tmux.noob.conf`：

```
# F1 = 左 pane（讲解），F2 = 右 pane（Claude）
# root key table (-n)，不需要 prefix，直接敲一次 F1/F2 即切
bind-key -n F1 select-pane -L
bind-key -n F2 select-pane -R
```

状态栏提示同步：`鼠标/F1=左pane  F2=右pane  │  F12 = 退出整个 demo`。

## 变更 commit 列表（本次原子序列）

| hash | 内容 |
|------|------|
| `1a433f8` | feat(tmux): F1/F2 root-key pane switch for start.demo.sh |
| `1e02fb4` | docs(features): canonical 6-feature manifest for claudefast probe（新增 FEATURES.md） |
| `5fb6ffb` | feat(demo): start.demo.sh right pane echo 6 CORE FEATURES checklist |
| `11eff02` | docs(claude-md): add 核心功能速答 + FEATURES.md 索引行 |

## 验证收尾

- [x] probe A Round 2 输出 6/6 feature 全覆盖
- [x] probe B（judge）JSON verdict = `PASS` (6/6 covered)
- [x] 实机外层 tmux（`start_demo_verify`）内跑完 `start.demo.sh`；右 pane 6/6 feature 全 ✓
- [x] plugin self_check.sh 17 项 ALL GREEN
- [x] F1/F2 pane 切换绑定落 `tmux.noob.conf`
- [x] 原子 commit 按单一关注点分 4 条
- [ ] finish-flag `claudefast -p "READ ONLY ..."` 复核（下一步）
