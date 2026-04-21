# insights-wiki plugin

demo_insights_share 团队内部 Claude Code plugin。当前已交付 **M2_AGENTS**，下一轮是
`M3_MCP_NAMESPACE_TTL`。

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
└── README.md                    # 本文件
```

## 当前能力（M2）

- 两个 skill：`insights-wiki`、`insights-wiki-server`
- 一个 hook：`UserPromptSubmit`
- 一个 statusline badge：`[wiki ✓ N/today]`
- 两个 agent：`wiki-curator`、`insight-validator`
- 五条命令：`/wiki-install`、`/wiki-search`、`/wiki-publish`、`/wiki-review`、`/wiki-diff`

其中 `/wiki-diff` 专门对应 `proposal_conflict_design.md` 的**并列 Good/Bad 视图**
要求，只输出差异和适用场景，不替用户做最终裁决。

## 装机路径

M2 仍保留两条安装路径：本地 source 模式便于开发，marketplace 模式对应团队内网分发。

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
/wiki-install
/wiki-search postgres pool
/wiki-diff postgres-pool-exhaustion
/wiki-publish wiki_tree/database/postgres_pool.md --dry-run
```

### B. marketplace 模式（当前 registry）

```bash
claude plugin marketplace add git+ssh://internal/insights-share.git
claude plugin install insights-wiki
```

安装后应能看到：

- version: `0.2.0-m2`
- commands: `wiki-install/wiki-search/wiki-publish/wiki-review/wiki-diff`
- agents: `wiki-curator/insight-validator`

## 验证

| 验证项 | 命令 | 通过标准 |
|--------|------|---------|
| manifest 合法 | `python -c 'import json; json.load(open("insights-share/plugin/.claude-plugin/plugin.json"))'` | 无异常 |
| marketplace 与 manifest 对齐 | `python - <<'PY' ... PY` | version 与 milestone 对齐 |
| skill 完整 | `ls insights-share/plugin/skills/*/SKILL.md` | 两个 SKILL.md |
| hook 可执行 | `test -x insights-share/plugin/hooks/user-prompt-submit.sh && bash -n $_` | `SYNTAX OK` |
| statusline 可执行 | `WIKI_STATUSLINE_NO_COLOR=1 bash insights-share/plugin/statusline/insights_wiki_statusline.sh` | 输出 `[wiki …]` |
| M2 合同自检 | `bash insights-share/plugin/scripts/self_check.sh` | 五个命令、两个 agent 全 `OK` |
| today_count 口径 | 跑 `start.demo.sh` 前后对比 `~/.cache/insights-wiki/today_count.json` | 同一 prompt 集合计数一致 |

## 路线图

- 已完成：M1 `manifest + skills + hook + statusline + /wiki-install + /wiki-search`
- 已完成：M2 `wiki-curator + insight-validator + /wiki-publish + /wiki-review + /wiki-diff`
- 下一轮：M3 `MCP wiki-server + team namespace + TTL/stale`
- 后续：M4 `ed25519 签名 + marketplace 发布链路`

## 非目标（M3/M4 再谈）

- MCP wiki-server
- 团队 namespace（`wiki_tree/<team>/…`）
- TTL + stale 徽章
- ed25519 卡片签名
- marketplace 发布到内网 git registry

## 不改动

- 仓库根目录只读 md：`proposal.md` / `README.md` / `validation.md` / `validation_AB.md`
- `docs/designs/user_design/` 整个目录
- 既有 `insights-share/demo_codes/.claude/skills/`（开发期双路径并存，不动源）
