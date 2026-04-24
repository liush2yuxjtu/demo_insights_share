# insights-share plugin

demo_insights_share 团队内部 Claude Code plugin。当前主线是 **v0.6.1-m7 / M7_LATENCY_DEEP**。

> **权威设计文档**：[`proposal/proposal_rename_to_insights_share.md`](../../proposal/proposal_rename_to_insights_share.md)
>
> M5 = 深度重命名：`insights-wiki` → `insights-share`、`insights-share/plugin/` → `plugins/insights-share/`、
> skill / command / agent / statusline / cache 全系换名。数据模型与 daemon API 不变。
>
> 本 README 只做「怎么装、怎么验」的操作说明，**不覆盖**设计决策。任何语义歧义以设计文档为准。

## 目录结构

```text
plugins/insights-share/
├── .claude-plugin/
│   ├── plugin.json              # manifest（槽位声明）
│   └── marketplace.json         # 内网 registry 声明
├── agents/
│   ├── share-curator.md         # 管理员 CRUD / review agent
│   └── share-validator.md       # 发布前校验 agent
├── mcp/
│   └── wiki-server.json         # wiki daemon 的 typed tool 契约（含 public-keys；M6 改名候选）
├── skills/
│   ├── insights-share/          # 客户端 skill
│   └── insights-share-server/   # 服务端 skill
├── hooks/
│   └── user-prompt-submit.sh    # 迁移自 insights_prefetch.py，保持 today_count 口径
├── statusline/
│   └── insights_share_statusline.sh  # [share ✓ N/today]
├── commands/
│   ├── share-install.md         # /share-install
│   ├── share-search.md          # /share-search <query>
│   ├── share-publish.md         # /share-publish [--dry-run]
│   ├── share-review.md          # /share-review <topic|card>
│   └── share-diff.md            # /share-diff <topic>
├── scripts/
│   ├── self_check.sh            # 本地自检
│   └── publish_marketplace.py   # 生成发布摘要
└── README.md                    # 本文件
```

## 当前能力（M7）

- 两个 skill：`insights-share`、`insights-share-server`
- 一个 hook：`UserPromptSubmit`
- 一个 statusline badge：`[share ✓ N/today] / [share ⚠ stale] / [share 🔒 sig-fail]`
- 两个 agent：`share-curator`、`share-validator`
- 五条命令：`/share-install`、`/share-search`、`/share-publish`、`/share-review`、`/share-diff`
- 一个 MCP 契约：`mcp/wiki-server.json`（内部 tool 名 `wiki_*` 本轮不动；留 M6_MCP_RENAME）
- 一套逻辑 team namespace：通过 `team` 字段、API query 和本地安装配置隔离命中范围
- 一套 ed25519 卡片签名链路：daemon 写入时签名，读取时验签，缓存 manifest 聚合 `sig-fail`
- 一条 marketplace 发布摘要链路：`scripts/publish_marketplace.py --check/--output`
- 一套 bundle-local hook runtime：`scripts/insights_prefetch.py`、`scripts/session_start_full_fetch.py`、`scripts/insights_cache.py`、`scripts/today_count.py`

其中 `/share-diff` 专门对应 `proposal_conflict_design.md` 的**并列 Good/Bad 视图**
要求，只输出差异和适用场景，不替用户做最终裁决。

## 装机路径

M5 保留两条安装路径：本地 source 模式便于开发，marketplace 模式对应团队内网分发。

## 双仓说明（v0.6.0-m7 起）

从 `v0.6.0-m7` 开始，`insights-share` 采用 **dev 仓** + **plugin/publish 仓**
双仓分发：

| 仓 | GitHub 仓库 | 用途 |
|----|-------------|------|
| dev 仓 | `liush2yuxjtu/demo_insights_share` | 主开发仓；包含 proposal、demo_codes、validation、历史记录与完整工作树 |
| plugin / publish 仓 | `liush2yuxjtu/insights-share-plugin` | 轻量分发仓；只放 plugin 运行时需要的 `.claude-plugin/`、skills、commands、agents、hooks、statusline、mcp、scripts |

含义：

- 日常开发、设计、验证、`start.demo.sh`、proposal 迭代都在 **dev 仓**
- `claude plugin marketplace add` / `claude plugin install` 的推荐入口是
  **plugin / publish 仓**
- 当前这个仓库工作树默认 remote 仍可能只指向 dev 仓；更新 publish 仓需要显式同步到
  `liush2yuxjtu/insights-share-plugin`

推荐安装命令：

```bash
claude plugin marketplace add liush2yuxjtu/insights-share-plugin
claude plugin install insights-share@insights-share-plugin
```

### A. 本地 source / 本地 marketplace 模式（开发默认）

```bash
# 1. 启 daemon（管理员侧）
bash plugins/insights-share/skills/insights-share-server/scripts/start_server.sh &

# 2. 把本 plugin 目录作为本地 marketplace 加进 Claude Code
claude plugin marketplace add "$(pwd)/plugins/insights-share"
claude plugin install insights-share@insights-share

# 3. 在 Claude Code 里敲斜杠命令
/share-install --team team-a
/share-search postgres pool
/share-diff postgres-pool-exhaustion
/share-publish wiki_tree/database/postgres_pool.md --dry-run --team team-a
```

### B. marketplace 模式（当前 registry）

```bash
claude plugin marketplace add git+ssh://internal/insights-share.git
claude plugin install insights-share
```

### 从旧名升级

```bash
claude plugin uninstall insights-wiki   # 旧包
claude plugin install insights-share    # 新包
```

安装后应能看到：

- version: `0.6.1-m7`
- commands: `share-install/share-search/share-publish/share-review/share-diff`
- agents: `share-curator/share-validator`
- mcp: `wiki-server`（内部名，M6 改）
- statusline: fresh=`[share ✓ N/today]` / stale=`[share ⚠ stale]` / sig-fail=`[share 🔒 sig-fail]`
- hooks runtime: `scripts/insights_prefetch.py` / `scripts/session_start_full_fetch.py` 已随 plugin cache 一起安装，不依赖 dev repo checkout
- server runtime: `runtime/insights_cli.py` / `runtime/insightsd/` / `runtime/wiki_tree/` 已随 plugin cache 一起安装，不依赖 dev repo checkout 或 `demo_codes/.venv`

## 验证

| 验证项 | 命令 | 通过标准 |
|--------|------|---------|
| manifest 合法 | `python -c 'import json; json.load(open("plugins/insights-share/.claude-plugin/plugin.json"))'` | 无异常 |
| marketplace 与 manifest 对齐 | `python - <<'PY' ... PY` | version 与 milestone 对齐 |
| skill 完整 | `ls plugins/insights-share/skills/*/SKILL.md` | 两个 SKILL.md |
| hook 可执行 | `test -x plugins/insights-share/hooks/user-prompt-submit.sh && bash -n $_` | `SYNTAX OK` |
| server runtime 自包含 | `bash plugins/insights-share/scripts/self_check.sh` | `server runtime bundle: OK` 且 `start_server.sh/start_ui.sh: OK` |
| statusline 可执行 | `SHARE_STATUSLINE_NO_COLOR=1 bash plugins/insights-share/statusline/insights_share_statusline.sh` | 输出 `[share …]` / `[share ✓ N/today]` / `[share ⚠ stale]` / `[share 🔒 sig-fail]` |
| MCP 契约可解析 | `python -c 'import json; json.load(open("plugins/insights-share/mcp/wiki-server.json"))'` | 无异常 |
| M5 合同自检 | `bash plugins/insights-share/scripts/self_check.sh` | 五个 share-* 命令、两个 share-* agent、签名能力、发布脚本全 `OK` |
| 发布摘要校验 | `python plugins/insights-share/scripts/publish_marketplace.py --check` | 输出 `marketplace publish contract: OK` |
| today_count 口径 | 跑 `start.demo.sh` 前后对比 `~/.cache/insights-share/today_count.json` | 同一 prompt 集合计数一致 |

## 路线图

- 已完成：M1 `manifest + skills + hook + statusline + /share-install + /share-search`（历史名 /wiki-*）
- 已完成：M2 `share-curator + share-validator + /share-publish + /share-review + /share-diff`（历史名 wiki-*）
- 已完成：M3 `MCP wiki-server contract + team namespace + TTL/stale`
- 已完成：M4 `ed25519 卡片签名 + sig-fail 状态灯 + marketplace 发布摘要`
- 已完成：M5 `深度重命名 insights-wiki -> insights-share、plugins/<name>/ 布局`
- 未完成：M6_MCP_RENAME `MCP tool 名 wiki_* -> share_*`（留待独立阶段，避免破坏已缓存上下文）

## 不改动

- 仓库根目录只读 md：`proposal.md` / `README.md` / `validation.md` / `validation_AB.md`
- `docs/designs/user_design/` 整个目录
- `wiki_tree/` 磁盘结构与 `wiki_types.json` / `topics.json`（语义已与 plugin 名解耦）
- daemon HTTP 路径 `/topics` / `/insights` / `/healthz` / `/signing/public-keys` / `/search`
- MCP server 内部 tool 名 `wiki_*`（本轮不动，留 M6）
