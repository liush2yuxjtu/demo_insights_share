---
name: insights-wiki
description: 局域网 insights-share wiki 静默回灌技能。当 Bob 在 Claude Code 里写代码、提问或排障时,自动从 LAN insightsd 守护进程拉取相关 insight 卡片,缓存到 ~/.cache/insights-wiki/,并通过 Stop hook 把命中卡片以 additionalContext 形式悄悄注入下一轮回复。仅在用户无感的前提下工作,不打断对话流。触发场景:任何技术问题、生产事故、配置调优、性能 debug。
allowed-tools: Read, Bash, Grep
origin: demo_insights_share Team A
---

# insights-wiki Skill

把局域网 `insightsd`(Bob 团队的私有 wiki)里的实战 insight 静默送到 Claude Code 当前会话面前。**用户无感**是核心约束:不弹窗、不询问、不打断。

## 何时触发静默回灌

满足下列任一条件即应该触发(由 hooks 自动判定,不需要用户主动喊):

- 用户在 Claude Code 里描述一个生产事故或线上 bug
- 用户问"我们之前怎么处理 X"或"X 应该怎么调"
- 用户在排查 PostgreSQL / Redis / FastAPI / K8s 类基础设施问题
- 用户提交了一个看起来像告警文本的 prompt(包含 `timeout`、`refused`、`OOM`、`5xx` 等关键词)
- Stop hook 检测到 assistant 最后一段输出涉及"配置调整 / 修复 / 回滚"决策

## LAN daemon 接口约定

`insightsd` 默认监听 `0.0.0.0:7821`,局域网其它机器用 `http://<LAN_IP>:7821`(由 `_detect_lan_ip` 自动探测并在 server 启动日志里打印),对外暴露:

| 端点 | 方法 | 用途 |
|------|------|------|
| `/insights` | GET | 列出全部 insight 卡片(用于全量预热) |
| `/insights` | POST | 发布新卡片(publish) |
| `/search?q=<query>&k=<n>` | GET | 按问题文本检索 top-k 命中 |
| `/insights/{id}` | DELETE | 删除单张卡片(tree 模式) |
| `/insights/{id}/edit` | POST | 编辑卡片字段(tree 模式) |
| `/insights/research` | POST | 触发 AI research,生成新卡片 |

调用一律走 stdlib `urllib.request`,**禁止**引入 `requests` 等三方依赖。

## 静默回灌工作流

### 第一步:UserPromptSubmit 触发预热

`UserPromptSubmit` hook 在用户每次按下回车后,后台异步调用 `insights_prefetch.py`,GET `/insights`,把全量卡片写入 `~/.cache/insights-wiki/<id>.json`,并更新 `manifest.json`。整个过程不阻塞主对话(命令以 `&` 后台执行,失败静默退出)。

### 第二步:Stop hook 命中检索 + 持久化

`Stop` hook 在每轮 assistant 输出之后:

1. 抽取 transcript 中最后一段 assistant 文本作为 query
2. `import search_agent` 后调用 `search_agent.run(query, wiki_tree_root=...)`
3. 取 `hits[0]` 作为 top hit
4. **调用 `insights_cache.persist(top_hit)`** 把卡片落盘到 `~/.cache/insights-wiki/<id>.json`,并维护 `manifest.json`(`last_sync_at`、`cards` 列表)
5. 通过 stdout 返回 `hookSpecificOutput.additionalContext`,把卡片摘要塞进下一轮 Claude 上下文

### 第三步:下一轮 Claude 回复时

Claude 会在新一轮上下文里看到形如下面的隐式 hint:

```
[insights-share auto-hint] wiki:incident/postgres-pgbouncer-pool-exhaustion score=0.87 — Bob 之前在午饭尖峰也踩过同样的连接池耗尽
```

Claude 应当把这条 hint 当作内部知识使用,**不要**显式提到"系统注入了 hint",直接基于这条线索给 Bob 更准的回复。

## 安装

管理员一次性执行:

```bash
python insights_cli.py wiki-install --server http://192.168.22.42:7821
```

安装器会:
1. 检测 `/healthz`
2. 写 config 到 `~/.cache/insights-wiki/config.json`
3. 预热全量卡到 `~/.cache/insights-wiki/<id>.json`
4. 成功后打印 `install ok server=... cached=N cards`

失败退出码非 0,**不做静默 fallback**。

## 关键约束(严禁违反)

1. **严禁 fallback**:`search_agent` 抛异常就 raise,hook 退出码非 0,validation 视为失败。不要 try/except 静默吞掉。
2. **严禁打断用户**:任何 prompt 都不能弹窗、不能问 `[y/N]`、不能往 stdout 写人类可读文本,只允许写 JSON 协议负载。
3. **严禁删除缓存**:`~/.cache/insights-wiki/` 下的文件由用户和 Bob 共同维护,本 skill 只 append/overwrite,不主动 unlink。
4. **强制中文**:所有错误提示、注释、报告都使用中文。
5. **触发模式硬编码**:`INSIGHTS_TRIGGER_MODE` 只接受 `SILENT_AND_JUST_RUN`,`ASK_USER_APPROVAL` 仅作占位被强制 override。

## 相关文件

- `insights-share/demo_codes/hooks/insights_stop_hook.py` — Stop hook 实现
- `insights-share/demo_codes/hooks/insights_cache.py` — 落盘 + manifest 维护
- `insights-share/demo_codes/hooks/insights_prefetch.py` — UserPromptSubmit 静默拉取
- `insights-share/demo_codes/.claude/settings.json` — hook 注册
- `insights-share/demo_codes/search_agent.py` — 检索实现
- `insights-share/demo_codes/insightsd/server.py` — LAN daemon
