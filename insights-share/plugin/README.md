# insights-wiki plugin

demo_insights_share 团队内部 Claude Code plugin。M1 MVP。

> **权威设计文档**：[`proposal/proposal_plugin_design.md`](../../proposal/proposal_plugin_design.md)
>
> 本 README 只做「怎么装、怎么验」的操作说明，**不覆盖**设计决策。任何语义歧义以设计文档为准。

## 目录结构

```
insights-share/plugin/
├── .claude-plugin/
│   ├── plugin.json         # manifest（槽位声明）
│   └── marketplace.json    # 内网 registry 声明
├── skills/
│   ├── insights-wiki/      # 客户端 skill（零改搬运）
│   └── insights-wiki-server/  # 服务端 skill（零改搬运）
├── hooks/
│   └── user-prompt-submit.sh  # 迁移自 insights_prefetch.py，保持 today_count 口径
├── statusline/
│   └── insights_wiki_statusline.sh  # [wiki ✓ N/today]
├── commands/
│   ├── wiki-install.md     # /wiki-install
│   └── wiki-search.md      # /wiki-search <query>
└── README.md               # 本文件
```

## M1 装机路径

M1 阶段不强依赖 `claude plugin install` CLI（若 CLI 已支持则一条命令完事）。本地开发/演示两条路径并存：

### A. 本地 source 模式（M1 默认）

```bash
# 1. 启 daemon（管理员侧）
./insights-share/demo_codes/.venv/bin/python \
    ./insights-share/demo_codes/insights_cli.py serve \
    --host 0.0.0.0 --port 7821 --store wiki.json --store-mode flat &

# 2. 把本 plugin 目录挂入 Claude Code（任选其一）
#    - 软链到 user-level：ln -s $(pwd)/insights-share/plugin ~/.claude/plugins/insights-wiki
#    - 或直接跑 start.demo.sh（M1 自动做装机自检）

# 3. 在 Claude Code 里敲斜杠命令
/wiki-install
/wiki-search postgres pool
```

### B. marketplace 模式（M4 目标）

```bash
claude plugin marketplace add git+ssh://internal/insights-share.git
claude plugin install insights-wiki
```

## 验证

| 验证项 | 命令 | 通过标准 |
|--------|------|---------|
| manifest 合法 | `python -c 'import json; json.load(open("insights-share/plugin/.claude-plugin/plugin.json"))'` | 无异常 |
| skill 完整 | `ls insights-share/plugin/skills/*/SKILL.md` | 两个 SKILL.md |
| hook 可执行 | `test -x insights-share/plugin/hooks/user-prompt-submit.sh && bash -n $_` | `SYNTAX OK` |
| statusline 可执行 | `WIKI_STATUSLINE_NO_COLOR=1 bash insights-share/plugin/statusline/insights_wiki_statusline.sh` | 输出 `[wiki …]` |
| today_count 口径 | 跑 `start.demo.sh` 前后对比 `~/.cache/insights-wiki/today_count.json` | 同一 prompt 集合计数一致 |

## 非目标（M2+ 再谈）

- MCP wiki-server
- `wiki-curator` / `insight-validator` agent
- `/wiki-publish` / `/wiki-review` / `/wiki-diff`
- 团队 namespace（`wiki_tree/<team>/…`）
- TTL + stale 徽章
- ed25519 卡片签名
- marketplace 发布到内网 git registry

## 不改动

- 仓库根目录只读 md：`proposal.md` / `README.md` / `validation.md` / `validation_AB.md`
- `docs/designs/user_design/` 整个目录
- 既有 `insights-share/demo_codes/.claude/skills/`（M1 双路径并存，不动源）
