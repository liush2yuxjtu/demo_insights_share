---
name: share-install
description: 安装 insights-share plugin 到当前 Claude Code，并验证安装。替代旧 --install flag。
allowed-tools: Bash, Read
---

# /share-install

把 insights-share plugin 真正安装到当前 Claude Code 环境，并做装后自检。

## 做什么

1. 校验 plugin manifest（`.claude-plugin/plugin.json`）结构合法
2. 运行 `claude plugin marketplace add <当前 plugin 目录>`，若 marketplace 已存在则复用
3. 运行 `claude plugin install insights-share@insights-share`
4. 校验已安装 plugin cache、skills、hook wrapper、statusline、commands、agents、MCP 契约
5. 触发一次 statusline 预览，打印 `[share ✓|✗|…]` 当前态
6. 打印 today_count 当前值（迁移前后对账基线）
7. 打印一段 PM 友好的“装好啦”摘要

## 不做什么

- 不在用户无感时自动启动 daemon（daemon 管理走 `insights-share-server`）
- 不修改任何位于仓库根目录的只读 md
- 不自动启动 daemon（daemon 管理走 `insights-share-server` 或单独 `insights_cli.py serve`）

## 和 M2+ 的边界

M1 最初只负责“校验装好了”。当前 contract 已升级为“真安装 + 校验装好了”。M2 引入 `share-validator` agent 后，本命令会追加发布前 dry-run 校验流；M4 引入 ed25519 签名后追加签名校验。

## 参考

- proposal/proposal_plugin_design.md §"MVP 范围" 第 5 行
- proposal/proposal_plugin_design.md §"迁移路径" M1 行
