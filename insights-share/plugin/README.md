# insights-wiki plugin

demo_insights_share 团队内部 Claude Code plugin。当前已交付 **M4_SIGN_MARKETPLACE**。

> **权威设计文档**：[`proposal/proposal_plugin_design.md`](../../proposal/proposal_plugin_design.md)
>
> 本 README 只做「怎么装、怎么验」的操作说明，**不覆盖**设计决策。任何语义歧义以设计文档为准。

## 目录结构

```text
insights-share/plugin/
├── .claude-plugin/
│   ├── plugin.json              # manifest（槽位声明）
│   └── marketplace.json         # 内网 registry 声明
├── agents/
│   ├── wiki-curator.md          # 管理员 CRUD / review agent
│   └── insight-validator.md     # 发布前校验 agent
├── mcp/
│   └── wiki-server.json         # wiki daemon 的 typed tool 契约（含 public-keys）
├── skills/
│   ├── insights-wiki/           # 客户端 skill（零改搬运）
│   └── insights-wiki-server/    # 服务端 skill（零改搬运）
├── hooks/
│   └── user-prompt-submit.sh    # 迁移自 insights_prefetch.py，保持 today_count 口径
├── statusline/
│   └── insights_wiki_statusline.sh  # [wiki ✓ N/today]
├── commands/
│   ├── wiki-install.md          # /wiki-install
│   ├── wiki-search.md           # /wiki-search <query>
│   ├── wiki-publish.md          # /wiki-publish [--dry-run]
│   ├── wiki-review.md           # /wiki-review <topic|card>
│   └── wiki-diff.md             # /wiki-diff <topic>
├── scripts/
│   ├── self_check.sh            # 本地自检
│   └── publish_marketplace.py   # 生成 M4 发布摘要
└── README.md                    # 本文件
```

## 当前能力（M4）

- 两个 skill：`insights-wiki`、`insights-wiki-server`
- 一个 hook：`UserPromptSubmit`
- 一个 statusline badge：`[wiki ✓ N/today] / [wiki ⚠ stale] / [wiki 🔒 sig-fail]`
- 两个 agent：`wiki-curator`、`insight-validator`
- 五条命令：`/wiki-install`、`/wiki-search`、`/wiki-publish`、`/wiki-review`、`/wiki-diff`
- 一个 MCP 契约：`mcp/wiki-server.json`
- 一套逻辑 team namespace：通过 `team` 字段、API query 和本地安装配置隔离命中范围
- 一套 ed25519 卡片签名链路：daemon 写入时签名，读取时验签，缓存 manifest 聚合 `sig-fail`
- 一条 marketplace 发布摘要链路：`scripts/publish_marketplace.py --check/--output`

其中 `/wiki-diff` 专门对应 `proposal_conflict_design.md` 的**并列 Good/Bad 视图**
要求，只输出差异和适用场景，不替用户做最终裁决。

## 装机路径

M4 仍保留两条安装路径：本地 source 模式便于开发，marketplace 模式对应团队内网分发。

### A. 本地 source 模式（开发默认）

```bash
# 1. 启 daemon（管理员侧）
./insights-share/demo_codes/.venv/bin/python \
    ./insights-share/demo_codes/insights_cli.py serve \
    --host 0.0.0.0 --port 7821 --store wiki.json --store-mode flat &

# 2. 把本 plugin 目录挂入 Claude Code（任选其一）
#    - 软链到 user-level：ln -s $(pwd)/insights-share/plugin ~/.claude/plugins/insights-wiki
#    - 或直接跑 start.demo.sh（会做 plugin 自检）

# 3. 在 Claude Code 里敲斜杠命令
/wiki-install --team team-a
/wiki-search postgres pool
/wiki-diff postgres-pool-exhaustion
/wiki-publish wiki_tree/database/postgres_pool.md --dry-run --team team-a
```

### B. marketplace 模式（当前 registry）

```bash
claude plugin marketplace add git+ssh://internal/insights-share.git
claude plugin install insights-wiki
```

安装后应能看到：

- version: `0.4.0-m4`
- commands: `wiki-install/wiki-search/wiki-publish/wiki-review/wiki-diff`
- agents: `wiki-curator/insight-validator`
- mcp: `wiki-server`
- statusline: fresh=`[wiki ✓ N/today]` / stale=`[wiki ⚠ stale]` / sig-fail=`[wiki 🔒 sig-fail]`

## 验证

| 验证项 | 命令 | 通过标准 |
|--------|------|---------|
| manifest 合法 | `python -c 'import json; json.load(open("insights-share/plugin/.claude-plugin/plugin.json"))'` | 无异常 |
| marketplace 与 manifest 对齐 | `python - <<'PY' ... PY` | version 与 milestone 对齐 |
| skill 完整 | `ls insights-share/plugin/skills/*/SKILL.md` | 两个 SKILL.md |
| hook 可执行 | `test -x insights-share/plugin/hooks/user-prompt-submit.sh && bash -n $_` | `SYNTAX OK` |
| statusline 可执行 | `WIKI_STATUSLINE_NO_COLOR=1 bash insights-share/plugin/statusline/insights_wiki_statusline.sh` | 输出 `[wiki …]` / `[wiki ✓ N/today]` / `[wiki ⚠ stale]` / `[wiki 🔒 sig-fail]` |
| MCP 契约可解析 | `python -c 'import json; json.load(open("insights-share/plugin/mcp/wiki-server.json"))'` | 无异常 |
| M4 合同自检 | `bash insights-share/plugin/scripts/self_check.sh` | 五个命令、两个 agent、签名能力、发布脚本全 `OK` |
| 发布摘要校验 | `python insights-share/plugin/scripts/publish_marketplace.py --check` | 输出 `marketplace publish contract: OK` |
| today_count 口径 | 跑 `start.demo.sh` 前后对比 `~/.cache/insights-wiki/today_count.json` | 同一 prompt 集合计数一致 |

## 路线图

- 已完成：M1 `manifest + skills + hook + statusline + /wiki-install + /wiki-search`
- 已完成：M2 `wiki-curator + insight-validator + /wiki-publish + /wiki-review + /wiki-diff`
- 已完成：M3 `MCP wiki-server contract + team namespace + TTL/stale`
- 已完成：M4 `ed25519 卡片签名 + sig-fail 状态灯 + marketplace 发布摘要`

## 不改动

- 仓库根目录只读 md：`proposal.md` / `README.md` / `validation.md` / `validation_AB.md`
- `docs/designs/user_design/` 整个目录
- 既有 `insights-share/demo_codes/.claude/skills/`（开发期双路径并存，不动源）
