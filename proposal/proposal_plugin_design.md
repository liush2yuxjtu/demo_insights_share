# Proposal: Plugin 化设计

## 问题

当前 `insights-wiki` 能力分散在多个独立部件：

- 两个 skill（`insights-wiki-server` + `insights-wiki`）靠手工拷贝到 `.claude/skills/`
- `wiki_daemon/prefetch_hook` 需手动写入 settings.json 的 hooks 段
- statusline `[wiki ✓ N/today]` 需另行注册到 statusline 命令
- 启动入口散落在 `start.demo.sh` / alias `demo` / 手跑 daemon
- 管理员 CRUD/审核流程没有封装，PM 演示需要开发者在旁边敲 bash
- 没有统一卸载、版本、签名、marketplace 分发路径

单 skill 模型无法承载「一条命令完成安装 + 钩子注册 + statusline + MCP + agent + 命令集」的交付形态。

## 目标

将 `insights-wiki` 整体封装为 Claude Code plugin：

- 一次 `claude plugin install` 完成 skill + hook + statusline + MCP + agent + slash 命令的注册
- PM 演示面零 bash，所有操作走 slash 命令
- 保留现有 topic-中心 Good/Bad 并列数据模型（见 `proposal_conflict_design.md`）不改
- 保留现有 statusline 三态契约（见 `proposal_statusline.md`）不改
- 兼容现 `start.demo.sh` self-verify 口径，迁移后 today_count 计数语义不变

## 总览

| 维度 | 现 skill 形态 | plugin 形态 |
|------|--------------|-------------|
| 分发 | 手工 cp / git subtree | `.claude-plugin/marketplace.json` + `claude plugin install git+ssh://internal/insights-wiki` |
| 注册 | 手写 settings.json hooks / statusline | plugin manifest 声明，CLI 自动注册 |
| 升级 | 拉仓库、手拷 | `claude plugin upgrade insights-wiki` |
| 卸载 | 人肉清理 | `claude plugin uninstall` |
| 版本 | 无 | `version` 字段 + `VERSION` 文件对齐 |
| 签名 | 无 | 卡片 ed25519 签名，防 wiki 内容 prompt injection |

## Plugin 槽位映射

| 槽位 | 内容 | 说明 |
|------|------|------|
| `skills/insights-wiki/` | 现客户端 skill | 零改动，直接搬 |
| `skills/insights-wiki-server/` | 现服务端 skill | 零改动，直接搬 |
| `commands/wiki-install.md` | `/wiki-install` | 替代 `--install` flag，PM 敲斜杠 |
| `commands/wiki-search.md` | `/wiki-search <topic>` | 查询 topic 下 Good/Bad 并列 |
| `commands/wiki-publish.md` | `/wiki-publish` | 新建卡片，走 `insight-validator` agent 校验 |
| `commands/wiki-review.md` | `/wiki-review` | 调用 `wiki-curator` agent 打开看板 |
| `commands/wiki-diff.md` | `/wiki diff <topic>` | 映射 `proposal_conflict_design.md` 的 topic Good/Bad 并列视图 |
| `hooks/user-prompt-submit.sh` | 预取卡片 | 迁移 `wiki_daemon/prefetch_hook.py` |
| `hooks/post-tool-use.sh` | 累加 today_count | 保持 `~/.cache/insights-wiki/today_count.json` 口径 |
| `hooks/session-start.sh` | 静默拉取 wiki 最新索引 | 对应 proposal 需求 4「SILENT-IN-BACKGROUND」 |
| `agents/wiki-curator.md` | 管理员看板 CRUD | 对应 proposal 需求 6「administrators can CRUD」 |
| `agents/insight-validator.md` | 发布前验证 insight 合法性 | 对应 proposal 需求 5「快速比对并验证」 |
| `mcp/wiki-server.json` | MCP server 声明 | 取代裸 HTTP 7821，AGENT 侧用 typed tool |
| `statusline/insights_wiki_statusline.sh` | `[wiki ✓ N/today]` | 现实现直接塞入 plugin `statusline` 槽 |
| `.claude-plugin/plugin.json` | manifest | name/version/author/entry 声明 |
| `.claude-plugin/marketplace.json` | 内网 marketplace 索引 | 支持 `claude plugin install` 源地址 |

## 额外能力

| 能力 | 价值 | 落点 |
|------|------|------|
| `--dry-run` 模式 | PM 演示零风险 | 所有 `/wiki-publish` 支持 `--dry-run` flag |
| 团队命名空间 | 解 proposal 需求「他人 insights 次优」| 卡片路径 `wiki_tree/<team>/<topic>/` |
| 卡片 TTL + stale 徽章 | 信任信号衰减可见 | statusline 新增态 `[wiki ⚠ stale]` |
| 事件日志 JSON 导出 | 接 `validation_AB.md` A/B 度量 | `~/.cache/insights-wiki/events/*.jsonl` |
| 离线缓存兜底 | LAN 掉线不崩 | `wiki-server` MCP 增加 cache-first 开关 |
| ed25519 卡片签名 | 防 wiki 内容注入恶意指令 | 发布时签，加载时验，验证失败走降级路径 |
| `/wiki diff topic` | Good/Bad 并列直接成视图 | 复用 conflict_design 数据模型 |

## Statusline 态扩展

| 态 | 条件 | 含义 |
|----|------|------|
| `[wiki ✓ N/today]` | daemon 可达 + today_count ≥ 1 | 现有，不改 |
| `[wiki ✗ 0/today]` | daemon 不可达 | 现有，不改 |
| `[wiki … N/today]` | prefetch 中 | 现有，不改 |
| `[wiki ⚠ stale]` | 最近命中卡片 TTL 过期 | plugin 新增 |
| `[wiki 🔒 sig-fail]` | 卡片签名校验失败 | plugin 新增 |

## MVP 范围

MVP 只交付让「PM 零 bash 跑完 demo」的最小集：

1. `.claude-plugin/plugin.json` + `.claude-plugin/marketplace.json`
2. 搬运两 skill 到 `skills/`，零改
3. `hooks/user-prompt-submit.sh` 迁 `prefetch_hook`
4. `statusline/` 槽塞入现脚本
5. `/wiki-install` + `/wiki-search` 两条最小命令
6. `start.demo.sh` 增加 `plugin install` 步骤，self-verify 保持 today_count 绿

其余（MCP / agents / diff / stale / 签名 / namespace）放 M2+。

## 迁移路径

| 阶段 | 动作 | 验证 |
|------|------|------|
| M0 | 现状保持，proposal 落地 | `start.demo.sh` 跑通 |
| M1 | MVP：manifest + skills + prefetch hook + statusline + 2 命令 | `claude plugin install` + `start.demo.sh` 双路可跑 |
| M2 | 加 agents + 剩余命令 | `/wiki-publish` / `/wiki-review` 走 agent 校验 |
| M3 | 加 MCP + 团队 namespace + TTL/stale | statusline 新态可见 |
| M4 | 加签名 + marketplace 发布到内网 git registry | `claude plugin upgrade` 走通 |

## 迭代推进 For-loop

下面这段不是运行时代码，而是实现阶段的**推进契约**。作用是把本设计文档中的
milestone 变成可重复执行的闭环：读设计 → 列交付项 → 实现 → 四门自检 →
agent-judge 判决 → 进入下一轮或停止。

### 原版伪码

```python
# ---- 常量 ----
DESIGN_DOC = "proposal/proposal_plugin_design.md"
MILESTONES = ["M1_MVP", "M2_AGENTS", "M3_MCP_NAMESPACE_TTL", "M4_SIGN_MARKETPLACE"]
MAX_RETRY_PER_MILESTONE = 3
DEMO_SURFACE = "start.demo.sh"

# ---- 每轮契约 ----
def iteration(milestone: str) -> Verdict:
    # 1. 载入 design doc 对应节
    spec = load_section(DESIGN_DOC, milestone)
    assert spec is not None, f"design doc 缺 {milestone} 节，停"

    # 2. 列 milestone 所有交付项（来自 "Plugin 槽位映射" + "MVP 范围" + "迁移路径"）
    deliverables = parse_deliverables(spec)

    # 3. 实现
    for d in deliverables:
        implement(d)
        atomic_commit(scope=d.single_concern)

    # 4. self-verify 四门
    gates = [
        gate_design_alignment(spec, deliverables),
        gate_start_demo_green(DEMO_SURFACE),
        gate_today_count_parity(),
        gate_claude_md_format(),
    ]
    for g in gates:
        if g.status != "PASS":
            return Verdict(FAIL, reason=g.reason, gate=g.name)

    # 5. agent-judge 双探针
    probe   = claudefast_probe(f"读 {DESIGN_DOC} {milestone} 节，交付是否齐？")
    verdict = claudefast_judge(probe_output=probe)
    return verdict

# ---- 主 for-loop ----
def run():
    for milestone in MILESTONES:
        retries = 0
        while True:
            v = iteration(milestone)
            if v.verdict == "PASS":
                log(f"[{milestone}] PASS 进下一轮")
                break
            if v.verdict == "REFINE" and retries < MAX_RETRY_PER_MILESTONE:
                retries += 1
                log(f"[{milestone}] REFINE #{retries}: {v.reason}")
                continue
            escalate_to_claude_p(milestone, v)
            abort(f"[{milestone}] 未通过，停止推进")
    final_report()
```

### 执行解释

| 环节 | 约束 |
|------|------|
| `load_section()` | milestone 在本设计文档里必须有专属定义；没有就停止，不允许"边做边猜" |
| `parse_deliverables()` | 只从本文档显式列出的槽位、MVP 范围、迁移路径中抽取，不额外扩 scope |
| `atomic_commit()` | 对齐项目规则：每个 deliverable 按单一关注点立即提交 |
| `gate_design_alignment()` | 实物文件、命名、命令、agent、hook、statusline 必须与本文档一致 |
| `gate_start_demo_green()` | `start.demo.sh` 是 human-last-visible surface，新增 feature 后必须可跑 |
| `gate_today_count_parity()` | 任何 hook / statusline / plugin 包装改动都不得破坏 `today_count` 口径 |
| `gate_claude_md_format()` | 仅当本轮同时修改 `CLAUDE.md` / `AGENTS.md` 时启用；纯 proposal 更新记为 `N/A` |
| `claudefast_probe + judge` | 用 agent-judge 判断"交付是否真的齐"，而不是靠 grep 文件名收尾 |

### 当前进度标注（2026-04-21 仓库快照）

```python
# ---- 当前快照 ----
DESIGN_DOC = "proposal/proposal_plugin_design.md"
MILESTONES = [
    "M1_MVP",                 # PASS
    "M2_AGENTS",              # REFINE（当前所在轮）
    "M3_MCP_NAMESPACE_TTL",   # PENDING
    "M4_SIGN_MARKETPLACE",    # PENDING
]

def snapshot_verdict(milestone: str) -> str:
    if milestone == "M1_MVP":
        return "PASS"
    if milestone == "M2_AGENTS":
        return "REFINE"
    return "PENDING"

def snapshot_reason(milestone: str) -> str:
    if milestone == "M1_MVP":
        return "manifest / marketplace / skills / hook / statusline / /wiki-install / /wiki-search 已落地"
    if milestone == "M2_AGENTS":
        return "plugin.json 已切到 0.2.0-m2，/wiki-publish + /wiki-review + 两个 agent 已在仓库，但 wiki-diff 未落地，部分元数据仍停在 M1"
    if milestone == "M3_MCP_NAMESPACE_TTL":
        return "缺 mcp/wiki-server.json、team namespace、TTL/stale 状态扩展"
    if milestone == "M4_SIGN_MARKETPLACE":
        return "缺 ed25519 签名链路与 marketplace 发布对齐"
    return "UNKNOWN"
```

### 里程碑快照表

| milestone | 当前判定 | 仓库证据 | 结论 |
|-----------|----------|----------|------|
| `M1_MVP` | `PASS` | 已有 `.claude-plugin/plugin.json`、`.claude-plugin/marketplace.json`、两份 skill、`hooks/user-prompt-submit.sh`、`statusline/insights_wiki_statusline.sh`、`/wiki-install`、`/wiki-search`；`start.demo.sh` 已调用 `plugin/scripts/self_check.sh` | 可以视为已过本轮，进入下一轮 |
| `M2_AGENTS` | `REFINE` | `plugin.json` 版本为 `0.2.0-m2`，`milestones.current=M2_AGENTS`；`/wiki-publish`、`/wiki-review`、`wiki-curator`、`insight-validator` 均已存在 | 已进入 M2，但仍未齐套；当前 loop 若执行到此，应停在 `REFINE` 而不是宣告 `PASS` |
| `M3_MCP_NAMESPACE_TTL` | `PENDING` | 仓库中暂无 `mcp/wiki-server.json`，也没有 team namespace、`[wiki ⚠ stale]`、TTL 处理链路 | 不应提前进入实现循环 |
| `M4_SIGN_MARKETPLACE` | `PENDING` | 仓库中暂无 ed25519 签名/验签链路；`marketplace.json` 仍写 `0.1.0-m1` | 不应提前进入实现循环 |

### 当前 M2 的 refine 点

当前仓库若按本 for-loop 继续推进，`M2_AGENTS` 这一轮至少还要补齐下面几项，才适合再次跑
agent-judge：

1. `commands/wiki-diff.md` 仍缺，和"Plugin 槽位映射"未对齐。
2. `insights-share/plugin/README.md` 仍以 "M1 MVP" 为主叙述，和仓库中已存在的 M2 实物不一致。
3. `.claude-plugin/marketplace.json` 仍停在 `0.1.0-m1`，未与 `plugin.json` 的 `0.2.0-m2` 对齐。
4. 若本轮要宣告 `M2_AGENTS PASS`，应补跑一次 `start.demo.sh` 与 today_count 对账，避免只靠文件存在判定通过。

## 风险与约束

| 风险 | 对策 |
|------|------|
| Hook 迁移导致 `today_count` 口径漂 | MVP 阶段 `start.demo.sh` self-verify 对比 plugin 前后计数必须一致 |
| `--install` flag 语义变成 `claude plugin install` | 同步更新 `proposal.md` 需求 9.2 表述，走独立 PR，不动根目录只读 md |
| 根目录 md 只读 | plugin 说明落 `insights-share/plugin/README.md`，不回写根 |
| CLAUDE.md 新增索引行 | 按 `meta-self-verify.md` 跑 agent-judge 状态灯循环 |
| plugin 热改难 | 开发期保留 skill 目录双路径，plugin 走 release 构建 |
| tmux 嵌套跑 plugin 安装 | 遵守 `tmux-nested.md`，用 `TMUX= tmux ...` |

## 与既有 proposal 对齐

| 既有 proposal | 关系 |
|---------------|------|
| `proposal_conflict_design.md` | 数据模型权威；plugin 所有命令/agent/MCP 必须遵守 topic-中心 Good/Bad 并列，不合并不挑最优 |
| `proposal_wiki_card.md` | 磁盘形态；plugin 命名空间扩展 `wiki_tree/<team>/<topic>/` 向后兼容无 team 的路径 |
| `proposal_statusline.md` | 三态契约保留；plugin 新增 `stale` / `sig-fail` 两态为增量 |

## 验证

- `start.demo.sh` 增加 plugin install 步骤后仍全绿
- `today_count` 迁移前后同一 prompt 集合计数一致
- `claude plugin uninstall insights-wiki` 执行后 settings.json / statusline / hooks / skills 清理干净无残留
- PM 演示脚本全程只敲 slash 命令，零 bash
