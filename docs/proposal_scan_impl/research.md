# Proposal 扫描研究

## Architecture

- `proposal/`：权威设计输入，当前核心是 `proposal_conflict_design.md`、`proposal_wiki_card.md`、`proposal_statusline.md`、`proposal_plugin_design.md`
- `insights-share/demo_codes/insightsd/`：daemon、HTTP API、store 与 runtime
- `insights-share/demo_codes/insights_cli.py`：CLI 入口，负责 publish/list/solve/topic 操作
- `insights-share/demo_codes/hooks/insights_prefetch.py`：UserPromptSubmit 静默预取与缓存注入
- `insights-share/plugin/`：plugin 分发表面，包括 manifest、commands、agents、hook、statusline、自检脚本
- `start.demo.sh`：人类最终可见的 demo surface

## Data Flow

- 用户安装 plugin 后，`wiki-install` 把 server/team 配置写入 `~/.cache/insights-wiki/config.json`
- `UserPromptSubmit` hook 读取配置，按 `team` 过滤调用 daemon `/insights`
- 命中的卡片写入本地缓存 `~/.cache/insights-wiki/*.json` 与 `manifest.json`
- `today_count.json` 维护日内命中数，statusline 同时读 `today_count.json`、`manifest.json`、daemon health 与 skill 安装态
- CLI / HTTP API 通过 `team` query 和 card/topic `team` 字段实现逻辑 namespace

## Patterns And Conventions

- 数据模型保持 Topic 中心、Good/Bad 并列共存，不做冲突检测
- `validation.md` 的 4 层 wiki 结构是硬门禁，因此 team namespace 不能直接破坏磁盘层级
- plugin 自检走 `insights-share/plugin/scripts/self_check.sh`
- 可验证的新规则必须落到脚本 gate、测试或 demo surface，而不是只写文档

## Dependencies

- Python stdlib：HTTP、JSON、文件系统操作
- repo 内 `.venv`：pytest 回归验证
- shell 脚本：statusline、自检、start driver

## Potential Impact Areas

- `TreeInsightStore`：topic/card/team 过滤与兼容旧数据的默认行为
- HTTP API：`/insights`、`/search`、`/topics`、`/topics/{id}/examples`
- CLI：team 配置解析、query 组装、publish/install 默认行为
- statusline：stale 逻辑不能破坏现有 `✓ / … / ✗` 判定
- plugin 元数据：manifest、marketplace、README、自检、release 打包清单必须同步

## Edge Cases

- 旧 topic / card 没有 `team` 字段时必须继续可读，默认视作 shared
- 同一个 `topic_id` 需要允许在不同 team 下并存
- `manifest.json` 缺失或损坏时 statusline 不能报错，只能回退成非 stale
- `team` 只做逻辑 namespace，不能破坏 validation #4 的磁盘结构

## Lessons From Last Run

- proposal 自身存在“team namespace”与“4 层 wiki 结构”之间的张力，本轮采用逻辑 namespace 避免打穿验证门禁
- plugin 文档与实际实现容易漂移，必须把 README、自检脚本、start demo 文案和测试一起更新
