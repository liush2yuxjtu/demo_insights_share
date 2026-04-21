# Proposal: 重命名 plugin 为 `insights-share`

> 作者：demo_insights_share Team A
> 日期：2026-04-21
> 状态：草稿
> 关联：[proposal_plugin_design.md](proposal_plugin_design.md)（M1–M4 已全部落地）

---

## 目标

- plugin 命名：`insights-wiki` → `insights-share`
- marketplace 命名：`insights-share internal` → `insights-share`
- 物理目录：`insights-share/plugin/` → `plugins/insights-share/`（对齐官方主流布局：https://code.claude.com/docs/en/plugin-marketplaces）
- skill / command / cache / statusline 徽章均随之改名（**深度重命名**）

目的：

1. 让 plugin 与仓库整体品牌统一（"insights-share"）
2. 与官方 `plugins/<name>/` 布局对齐，多 plugin 共存时更自然
3. 移除 `wiki` 历史命名残留，缩短心智映射

非目标：

- 不改业务逻辑、不改数据模型（`proposal_conflict_design.md` 保持权威）
- 不改 daemon API 路径（`/topics`, `/insights` 等保持）
- 不改 `wiki_tree/` 磁盘结构（见 `proposal_wiki_card.md`）

---

## Rename Matrix

| 维度 | 当前 | 目标 |
|------|------|------|
| plugin `name`（`.claude-plugin/plugin.json`） | `insights-wiki` | `insights-share` |
| plugin 版本 | `0.4.0-m4` | `0.5.0-m5` |
| marketplace `name` | `insights-share internal` | `insights-share` |
| marketplace 入口 source subdir | `insights-share/plugin` | `plugins/insights-share` |
| 物理目录 | `insights-share/plugin/` | `plugins/insights-share/` |
| skill 客户端目录 | `skills/insights-wiki/` | `skills/insights-share/` |
| skill 服务端目录 | `skills/insights-wiki-server/` | `skills/insights-share-server/` |
| command 文件 | `commands/wiki-{install,search,publish,review,diff}.md` | `commands/share-{install,search,publish,review,diff}.md` |
| command slash | `/wiki-install` 等 | `/share-install` 等（或 `/insights-share:share-install` 带命名空间） |
| agent 文件名 | `agents/wiki-curator.md`, `agents/insight-validator.md` | `agents/share-curator.md`, `agents/share-validator.md` |
| hook 脚本 | `hooks/user-prompt-submit.sh`（文件名保留） | 内容中对 `insights-wiki` / 缓存路径替换 |
| statusline 脚本 | `statusline/insights_wiki_statusline.sh` | `statusline/insights_share_statusline.sh` |
| statusline 徽章 | `[wiki ✓ N/today]` `[wiki ⚠ stale]` `[wiki 🔒 sig-fail]` | `[share ✓ N/today]` `[share ⚠ stale]` `[share 🔒 sig-fail]` |
| 本地缓存目录 | `~/.cache/insights-wiki/` | `~/.cache/insights-share/` |
| today_count 文件 | `~/.cache/insights-wiki/today_count.json` | `~/.cache/insights-share/today_count.json` |
| daemon 源目录中的 skill | `insights-share/demo_codes/.claude/skills/insights-wiki/` | `insights-share/demo_codes/.claude/skills/insights-share/` |
| daemon 源目录的 server skill | `.../insights-wiki-server/` | `.../insights-share-server/` |

保留不变：

- 根仓库名 `demo_insights_share`
- `wiki_tree/` 目录结构 + `wiki_types.json` + `topics.json`
- daemon HTTP 路径 `/topics`, `/insights`, `/healthz`, `/signing/public-keys`, `/search`
- MCP server 内部 tool 名称（`wiki_health`, `wiki_search`, `wiki_topics`, `wiki_examples`, `wiki_publish`, `wiki_relabel`, `wiki_public_keys`）
  - 注：改这些会强制所有已缓存的 MCP 调用上下文失效；M5 暂不动，若后续要改走 M6_MCP_RENAME 独立阶段

---

## 受影响文件清单（实物盘点）

| 类别 | 文件（相对仓库根） |
|------|---------------------|
| manifest | `insights-share/plugin/.claude-plugin/plugin.json`、`.../marketplace.json` |
| 5 commands | `insights-share/plugin/commands/wiki-{install,search,publish,review,diff}.md` |
| 2 agents | `insights-share/plugin/agents/{wiki-curator,insight-validator}.md` |
| hook | `insights-share/plugin/hooks/user-prompt-submit.sh` |
| statusline | `insights-share/plugin/statusline/insights_wiki_statusline.sh` |
| skills（plugin 内） | `insights-share/plugin/skills/insights-wiki/SKILL.md`、`.../insights-wiki-server/SKILL.md`、`.../insights-wiki-server/scripts/*.sh` |
| plugin 辅助脚本 | `insights-share/plugin/scripts/self_check.sh`、`.../publish_marketplace.py` |
| plugin README | `insights-share/plugin/README.md` |
| 源 skill | `insights-share/demo_codes/.claude/skills/insights-wiki/**`、`.../insights-wiki-server/**` |
| daemon hooks | `insights-share/demo_codes/hooks/insights_prefetch.py`、`.../insights_cache.py`、`.../insights_stop_hook.py` |
| daemon CLI | `insights-share/demo_codes/insights_cli.py` |
| today_count | `insights-share/wiki_daemon/today_count.py` |
| signing | `insights-share/demo_codes/insightsd/signing.py`、`.../store.py` |
| 测试 | `insights-share/validation/test_plugin_contract.py`、`test_topic_api.py`、`test_statusline.py`、`test_examples_demo_scripts.py` |
| demo 入口 | `start.demo.sh`（`SKILL_NAME` 常量 + `insights-share/plugin/` 路径 + statusline 文件名） |
| proposal | `proposal/proposal_plugin_design.md`（更新 milestones + 路径），`proposal/proposal_statusline.md`（badge 文案） |
| 索引 | `proposal/INDEX.md`、`CLAUDE.md` 设计文档索引 |
| 不动的根只读 md | `proposal.md`、`README.md`、`validation.md`、`validation_AB.md`（按项目规则不修改） |
| 不动的 user_design 目录 | `docs/designs/user_design/`（只读） |

---

## 迁移阶段：`M5_RENAME`

引入新 milestone，**不合并到 M4**，单独跑一遍 for-loop 契约（见 `proposal_plugin_design.md` 的
"迭代推进 For-loop" 节）。

### 子步骤（按原子 commit 划分，每步一个单一关注点）

1. **准备**：生成新目录骨架 `plugins/insights-share/`（空壳 + manifest stub `0.5.0-m5` 占位）
2. **物理迁移**：`git mv insights-share/plugin/* plugins/insights-share/`
3. **skill 目录 rename**：`git mv skills/insights-wiki skills/insights-share`、同理 server
4. **command 文件 rename**：`wiki-*.md → share-*.md`，内容改 slash 名与描述
5. **agent 文件 rename**：`wiki-curator → share-curator`，`insight-validator → share-validator`
6. **hook 内容替换**：`insights-wiki` → `insights-share`，缓存路径 `~/.cache/insights-wiki` → `~/.cache/insights-share`
7. **statusline 文件 rename + 徽章文案**：`wiki` → `share`
8. **manifest 字段对齐**：`name`, `version`, `milestones.current=M5_RENAME`, `completed+=[M5_RENAME]`
9. **marketplace.json 对齐**：`name=insights-share`, `source subdir=plugins/insights-share`, version `0.5.0-m5`
10. **plugin README rewrite**：路径、命令名、badge、安装路径示例全替换
11. **scripts/self_check.sh 重写断言**：
    - 命令清单改 `share-{install,search,publish,review,diff}`
    - agent 改 `share-curator`、`share-validator`
    - 版本断言 `0.5.0-m5`、milestone `M5_RENAME`
    - 目录引用 `plugins/insights-share`
12. **publish_marketplace.py 更新**：校验新路径 + 新版本
13. **源 skill 目录 rename**：`demo_codes/.claude/skills/insights-wiki{,-server}` → `insights-share{,-server}`
14. **daemon hooks / CLI / today_count.py / signing.py 内容替换**：`insights-wiki` 字符串 → `insights-share`
15. **测试文件更新**：断言新路径、新命令、新版本、新 badge
16. **start.demo.sh 更新**：
    - `SKILL_NAME="insights-share"`
    - 所有 `insights-share/plugin/` → `plugins/insights-share/`
    - statusline 路径 → `plugins/insights-share/statusline/insights_share_statusline.sh`
    - self-check 调用路径更新
    - sandbox cache 路径 `~/.cache/insights-share`
17. **proposal_plugin_design.md 更新**：
    - 添加 M5_RENAME 到 `MILESTONES` 列表
    - 当前进度快照改为 `M5_RENAME = PASS`（落地后）
    - 槽位映射表路径改 `plugins/insights-share/`
18. **proposal_statusline.md 更新**：徽章文案 `[share ✓ N/today]`
19. **proposal/INDEX.md + CLAUDE.md 索引表更新**：新增本 proposal 一行
20. **agent-judge 双探针**：按 `meta-self-verify` 规则跑 PASS/REFINE/FAIL
21. **实机验证**：在 m2test tmux 里跑 `start.demo.sh`，self-check 全绿 + statusline 显示 `[share ✓ 0/today]`

每一步立即 `git commit`，不合并。

---

## 验证门禁（M5_RENAME 版）

继承原 for-loop 四门，**新增两门**：

| 门 | 通过标准 |
|----|----------|
| `gate_design_alignment` | 所有实物路径、命名与本 proposal Rename Matrix 对齐 |
| `gate_start_demo_green` | `start.demo.sh` 在 m2test tmux 里跑，self-check `ALL GREEN`，statusline 显示 `[share ✓ 0/today]` |
| `gate_today_count_parity` | 同一 prompt 集合，改名前 `~/.cache/insights-wiki/today_count.json` 与改名后 `~/.cache/insights-share/today_count.json` 计数一致（需保留一次对比脚本） |
| `gate_claude_md_format` | `CLAUDE.md` 索引新增一行，格式合规 |
| **`gate_no_wiki_leak`（新）** | 全仓 `grep -rn "insights-wiki" --exclude-dir=.git --exclude-dir=.claude/worktrees --exclude-dir=insights-share/validation/reports` 零命中（除本 proposal 的 Rename Matrix 表） |
| **`gate_marketplace_subdir`（新）** | `marketplace.json.plugins[0].source` 的 `subdir` 指向 `plugins/insights-share` 且 `plugin.json` 存在 |

---

## 回滚路径

单条 `git revert <commit-range>` 即可完整还原 M4 状态，因为每步都是独立 commit。

如需部分回滚（例如只回命令 slash 名、保留目录迁移），按本 proposal 子步骤编号逆向 `git revert <step-N>`。

---

## 风险 & 对策

| 风险 | 对策 |
|------|------|
| `today_count` 计数口径断裂 | 过渡期保留双读（先读新路径，miss 则读旧路径）；一个 demo 周期后移除旧读 |
| 已发出的 B_with export 引用 `insights-wiki` / `alice-pgpool-2026-04-10` | `examples/` 下历史资产为冻结证据，不回写；本次改动不动 `examples/`；后续新录 A/B 才切换 |
| 外部已装 plugin 用户升级 | `claude plugin uninstall insights-wiki` + `claude plugin install insights-share`，README 提供一条迁移命令 |
| MCP tool 名 `wiki_*` 与 plugin 名不再同族 | 本轮不改；留 M6_MCP_RENAME |
| `wiki_tree/` 目录名保留为 `wiki_tree` 可能让新用户困惑 | M5 不动，文档补一条"目录名 wiki_tree 为历史命名，语义已与 plugin 名解耦" |
| tmux-nested 规则里的 `start.demo.sh L148~L227` 注释漂 | M5 顺手修正注释 + `tm() { TMUX= tmux -L "$SOCK" "$@"; }` |
| worktrees 下的旧副本（`.claude/worktrees/minimax0416_dev/**`） | 不在本次迁移范围；worktree 生命周期独立 |

---

## 与既有 proposal 的关系

| proposal | 关系 |
|----------|------|
| `proposal_conflict_design.md` | 数据模型不变；rename 只改外层封装命名 |
| `proposal_wiki_card.md` | 磁盘形态不变；`wiki_tree/` 目录名保留 |
| `proposal_statusline.md` | 徽章文案从 `wiki` → `share`；三态契约保留，M3 增态 `⚠ stale` / M4 增态 `🔒 sig-fail` 同步文案 |
| `proposal_plugin_design.md` | 新增 M5_RENAME 里程碑；槽位映射表路径全部替换为 `plugins/insights-share/` |

---

## 预期最终形态

```
demo_insights_share/
├── proposal/
│   └── proposal_rename_to_insights_share.md   ← 本文件
├── plugins/
│   └── insights-share/
│       ├── .claude-plugin/
│       │   ├── plugin.json                    name=insights-share v0.5.0-m5
│       │   └── marketplace.json               name=insights-share
│       ├── skills/
│       │   ├── insights-share/SKILL.md
│       │   └── insights-share-server/SKILL.md
│       ├── commands/
│       │   ├── share-install.md
│       │   ├── share-search.md
│       │   ├── share-publish.md
│       │   ├── share-review.md
│       │   └── share-diff.md
│       ├── agents/
│       │   ├── share-curator.md
│       │   └── share-validator.md
│       ├── hooks/user-prompt-submit.sh
│       ├── statusline/insights_share_statusline.sh
│       ├── mcp/wiki-server.json               ← 文件名暂不动（见 M6）
│       ├── scripts/{self_check.sh,publish_marketplace.py}
│       └── README.md
├── insights-share/
│   ├── demo_codes/.claude/skills/
│   │   ├── insights-share/**
│   │   └── insights-share-server/**
│   ├── demo_codes/hooks/**（字符串替换 insights-wiki → insights-share）
│   └── validation/test_plugin_contract.py（断言新名）
├── start.demo.sh                              SKILL_NAME=insights-share + plugins/insights-share 路径
└── CLAUDE.md                                  新增一行索引本 proposal
```

安装命令示例（文档中展示）：

```bash
claude plugin marketplace add git+ssh://internal/insights-share.git
claude plugin install insights-share
```

statusline 示例：

```
┌────────────────────────────────────────────────────────────┐
│ ~/projects/demo_insights_share  main*  claude-opus-4-7     [share ✓ 7/today] │
└────────────────────────────────────────────────────────────┘
```
