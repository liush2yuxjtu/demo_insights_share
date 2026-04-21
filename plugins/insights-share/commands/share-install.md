---
name: share-install
description: 安装 insights-share plugin 到当前 Claude Code，并验证安装。替代旧 --install flag。
allowed-tools: Bash, Read
---

# /share-install

一键安装 insights-share plugin 到当前 Claude Code 环境，并做装后自检。

## 做什么

1. 确认 daemon `http://127.0.0.1:7821` 可达；不可达则提示先开 `insights-share-server`
2. 校验 plugin manifest（`.claude-plugin/plugin.json`）结构合法
3. 校验 skill 目录存在：`skills/insights-share` 与 `skills/insights-share-server`
4. 校验 hook wrapper 可执行：`hooks/user-prompt-submit.sh`
5. 校验 statusline 脚本可执行：`statusline/insights_share_statusline.sh`
6. 触发一次 statusline 预览，打印 `[share ✓|✗|…]` 当前态
7. 打印 today_count 当前值（迁移前后对账基线）
8. 打印一段 PM 友好的"装好啦"摘要

## 不做什么

- 不在用户无感时自动启动 daemon（daemon 管理走 `insights-share-server`）
- 不修改任何位于仓库根目录的只读 md
- 不把 plugin manifest 写入真实 `~/.claude/`（仅做校验，实际安装由 `claude plugin install` 命令驱动）

## 和 M2+ 的边界

M1 只负责"校验装好了"。M2 引入 `share-validator` agent 后，本命令会追加发布前 dry-run 校验流；M4 引入 ed25519 签名后追加签名校验。

## 参考

- proposal/proposal_plugin_design.md §"MVP 范围" 第 5 行
- proposal/proposal_plugin_design.md §"迁移路径" M1 行
