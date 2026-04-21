# roleplan_agents

本目录存放**角色扮演 prompt**, 通过 `claudefast -p` 调起, 让 LLM 以特定角色视角回答, 并强制使用 `insights-share` plugin 命令。

## 角色列表

| role | 面向 | 主要用 plugin 命令 |
|------|------|-------------------|
| pm | 项目经理 | /share-search, /share-diff |
| oncall | SRE 当班 | /share-search, /share-review |
| tech-lead | 技术负责人 | /share-diff, /share-review |
| newbie | 新人 onboarding | /share-search |
| curator | Wiki 管理员 | /share-publish, /share-review, share-curator agent |
| validator | 发布前 QA | /share-publish --dry-run, share-validator agent |

## 快速开始

```bash
./launch.sh list
./launch.sh pm "我们要不要把 checkout 切到 connection pool?"
./launch.sh oncall "postgres 午高峰开始拒连, 已持续 8 分钟"
./launch.sh newbie "MiniMax agent SDK 怎么接入?"
```

## 它实际上做了什么

1. 读取 `prompt_<role>.md` 作为 system-level 角色 prompt
2. 把 user question 拼到文末
3. 通过 `zsh -ic "claudefast -p ..."` 交给 MiniMax 后端的 Claude CLI
4. CLI 在本 project 工作目录, 自动加载 `plugins/insights-share/` (若已装)
5. LLM 按 role prompt 中的强制工作流, 调 `/share-search`、`/share-diff` 等

## 扩展: 加新角色

1. 在本目录新建 `prompt_<newrole>.md`, 复用现有模板的结构:
   - frontmatter: role / audience / plugin / commands / summon
   - 强制工作流
   - 输出格式
   - 硬约束
2. 无需改 `launch.sh`, 自动发现

## 前置条件

- `claudefast` zsh function 已定义 (在 `~/.zshrc`)
- (可选) `insights-share` plugin 已装, 否则 agent 会降级并显式说明
