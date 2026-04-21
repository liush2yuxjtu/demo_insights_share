# Proposal 扫描计划

## Overview

本轮目标是扫描全部 proposal，与仓库现状对账，并把仍缺失的 M3 能力落地到运行时、plugin 契约和验证层。

## Phases

### Phase 1: Proposal 对账

- [x] 读取四个必读文件与 `proposal/INDEX.md`
- [x] 确认当前缺口集中在 `M3_MCP_NAMESPACE_TTL`
- [x] 识别设计冲突：team namespace 不能破坏 `validation.md` 的 4 层结构

### Phase 2: Runtime 实现

- [x] 在 store / server / CLI / hook 中加入逻辑 `team` namespace
- [x] 保持旧卡片与旧 topic 无 `team` 字段时的兼容行为
- [x] 为 store 与 API 补 team 过滤测试

### Phase 3: Plugin 契约与状态反馈

- [x] 在 statusline 中加入 `stale` 判定
- [x] 新增 `plugin/mcp/wiki-server.json`
- [x] 同步 plugin manifest / marketplace / README / self_check / start.demo
- [x] 新增 statusline 与 plugin contract 回归测试

### Phase 4: 验证与留档

- [x] 跑相关 pytest 组合回归
- [x] 跑 plugin 自检脚本
- [x] 跑 `start.claude.sh --dry-run`
- [x] 生成本轮 research / report / review / harness 工件

## Tasks

- [x] 实现 `TreeInsightStore.list_topics/list_examples/search` 的 `team` 过滤
- [x] 实现 `/insights`、`/search`、`/topics`、`/topics/{id}/examples` 的 `team` query
- [x] 实现 CLI 的 `--team` 与本地安装配置解析
- [x] 让 `insights_prefetch.py` 读取 team 配置
- [x] 实现 statusline `⚠ stale`
- [x] 更新 plugin M3 元数据与文档

## Code Snippets

```text
GET /search?q=<query>&k=3&team=<name>
GET /topics?team=<name>
GET /topics/{topic_id}/examples?label=good&team=<name>
POST /insights   # card JSON 内允许携带 team 字段
```

## Files To Modify

- `insights-share/demo_codes/insightsd/store.py`
- `insights-share/demo_codes/insightsd/server.py`
- `insights-share/demo_codes/insights_cli.py`
- `insights-share/demo_codes/hooks/insights_prefetch.py`
- `insights-share/plugin/statusline/insights_wiki_statusline.sh`
- `statusline/insights_wiki_statusline.sh`
- `insights-share/plugin/.claude-plugin/plugin.json`
- `insights-share/plugin/.claude-plugin/marketplace.json`
- `insights-share/plugin/scripts/self_check.sh`
- `insights-share/plugin/README.md`
- `start.demo.sh`
- `insights-share/validation/test_topic_store.py`
- `insights-share/validation/test_topic_api.py`
- `insights-share/validation/test_plugin_contract.py`
- `insights-share/validation/test_start_scripts.py`
- `insights-share/validation/test_release_package.py`
- `insights-share/validation/test_statusline.py`

## Reference Implementations

- `proposal/proposal_plugin_design.md` 中的 M3 定义
- 现有 `today_count.json` 与 `manifest.json` 缓存契约
- 现有 `plugin/scripts/self_check.sh` 的 M2 形态

## Post-Hook Expectations

- `review.md` 应确认 plan 中所有 checkbox 已完成
- `review.md` 应指出本轮采用“逻辑 team namespace”而不是改磁盘结构
- `harness.md` 应从 `~/.claude` 历史中总结可复用的 gate / report / hook 模式
