# Implementation Report

## Executive Summary

- 本轮扫描了全部 proposal，并把仍未落地的 M3 能力集中实现到 runtime 与 plugin 表面
- 实现结果分成两部分：
  - 逻辑 `team` namespace：store、HTTP API、CLI、hook 均可按 team 过滤
  - plugin M3 契约：`statusline stale`、`mcp/wiki-server.json`、manifest/marketplace/README/self-check/start demo 对齐
- 为避免破坏 `validation.md` 的 4 层 wiki 门禁，本轮没有改磁盘目录层级，而是把 team 做成逻辑 namespace

## Files Modified

- `insights-share/demo_codes/insightsd/store.py`
- `insights-share/demo_codes/insightsd/server.py`
- `insights-share/demo_codes/insights_cli.py`
- `insights-share/demo_codes/hooks/insights_prefetch.py`
- `insights-share/plugin/statusline/insights_wiki_statusline.sh`
- `statusline/insights_wiki_statusline.sh`
- `insights-share/plugin/.claude-plugin/plugin.json`
- `insights-share/plugin/.claude-plugin/marketplace.json`
- `insights-share/plugin/scripts/self_check.sh`
- `insights-share/plugin/mcp/wiki-server.json`
- `insights-share/plugin/README.md`
- `insights-share/plugin/commands/wiki-publish.md`
- `insights-share/plugin/commands/wiki-review.md`
- `insights-share/plugin/commands/wiki-diff.md`
- `insights-share/plugin/commands/wiki-search.md`
- `insights-share/plugin/agents/wiki-curator.md`
- `insights-share/plugin/agents/insight-validator.md`
- `start.demo.sh`
- `insights-share/validation/test_topic_store.py`
- `insights-share/validation/test_topic_api.py`
- `insights-share/validation/test_plugin_contract.py`
- `insights-share/validation/test_start_scripts.py`
- `insights-share/validation/test_release_package.py`
- `insights-share/validation/test_statusline.py`

## Implementation Metrics

- Atomic commits: 2
- Runtime / API / hook 相关回归：20 tests passed
- Plugin / statusline / release / start script 相关回归：16 tests passed
- Combined regression: 36 tests passed
- Plugin contract self-check: PASS
- `start.claude.sh --dry-run`: PASS

## Code Statistics

- 新增 runtime 行为：
  - `team` 字段兼容旧数据并支持 topic/card 查询过滤
  - 安装配置可写入并回读 `team`
  - hook 读取 team 配置后只拉对应 namespace 的卡片
- 新增 plugin 行为：
  - `statusline` 支持 `[wiki ⚠ stale]`
  - M3 manifest / marketplace 版本对齐到 `0.3.0-m3`
  - 新增 `mcp/wiki-server.json` 作为 typed tool contract
- 新增测试：
  - `test_statusline.py`
  - team namespace 的 store / API 覆盖

## Visualizations

```text
proposal/*
   │
   ├── plugin_design(M3)
   │        │
   │        ├── runtime: store / server / cli / hook
   │        ├── plugin: manifest / self_check / mcp / statusline
   │        └── validation: pytest / release / start driver
   │
   └── statusline
            │
            └── today_count.json + manifest.json -> badge
```

## Key Decisions

- team namespace 采用逻辑隔离，不改 `wiki_tree/{wiki_type}/{slug}.md` 结构
- stale 采用 `manifest.json.last_sync_at` + TTL 判定，不新增额外状态文件
- MCP 先以 contract file 落地，保持现有 plugin 分发路径稳定

## Residual Risks

- `/wiki-search` 的离线 fallback 仍未落地，本轮文档已改成明确说明不在范围内
- `mcp/wiki-server.json` 当前是契约文件，不是完整独立进程型 MCP server
- 未跑完整交互式 `start.demo.sh`，仅完成 `start.claude.sh --dry-run` 与 plugin 自检
