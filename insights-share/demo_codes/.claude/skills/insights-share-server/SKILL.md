---
name: insights-wiki-server
description: 管理员专用：启动 LAN insightsd 守护进程（--start 默认）或打开 control dashboard kanban 做在线 CRUD（--ui）。触发词：启动 wiki 服务器 / 开 wiki / 打开 wiki 管理面板 / wiki kanban。仅分配给管理员。
allowed-tools: Bash, Read
origin: demo_insights_share Team A
---

# insights-wiki-server Skill

管理员专用 skill，负责 LAN insightsd 守护进程的启动与控制面板（kanban dashboard）入口。**只做 server 端**，不参与 insights-wiki 的静默回灌流程。

## 何时触发

仅在管理员显式请求时触发，常见触发语：

- 「启动 wiki 服务器」→ 默认走 `--start`
- 「开 wiki」/「打开 wiki」→ 默认走 `--start`
- 「打开 wiki 管理面板」/「wiki kanban」→ 走 `--ui`
- 「启动 insightsd 0.0.0.0:7821」→ 走 `--start`

非管理员（普通开发用户）的请求不应触发本 skill；普通用户该用 `insights-wiki` skill 做静默回灌。

## 两条入口

### `--start`（默认）

调用 `scripts/start_server.sh`，前台启动 daemon：

```bash
python insights_cli.py serve --host 0.0.0.0 --port 7821 --store-mode tree
```

启动后会在 stderr 打印 LAN IP，方便其它机器连接。

### `--ui`

调用 `scripts/start_ui.sh`，后台启动 daemon + 自动 `open -a "Google Chrome" http://<LAN_IP>:7821/` 弹出 kanban 控制面板：

- 顶栏：新增卡 / research / 关键词搜索
- 三列：全部卡 / 已触发 / 未触发
- 每张卡可编辑、删除、打标签

dashboard 走同源 fetch 调用 daemon 的 CRUD 路由，无需 CORS。

## 关闭方式

- 前台模式（`--start`）：Ctrl+C
- 后台模式（`--ui`）：`pkill -f "insights_cli.py serve"`

## 与 insights-wiki 的区别

| skill | 用户角色 | 功能 |
|-------|---------|------|
| `insights-wiki-server` | 管理员 | 启动 daemon + dashboard CRUD |
| `insights-wiki` | 普通开发者 | 静默回灌 LAN 卡片到 Claude 上下文 |

两个 skill 互不依赖，但共用同一个 LAN daemon。

## 关键约束

1. **必须 tree mode**：CRUD / edit / delete / research 路由只在 `--store-mode tree` 下可用
2. **必须 0.0.0.0**：监听地址不能写 127.0.0.1，否则其它机器连不上
3. **强制中文**：日志、报错都用中文
4. **不参与静默回灌**：本 skill 与 Stop hook、prefetch hook 完全无关

## 相关文件

- `scripts/start_server.sh` — `--start` 入口
- `scripts/start_ui.sh` — `--ui` 入口
- `insights-share/demo_codes/insightsd/server.py` — daemon 实现
- `insights-share/demo_codes/insightsd/dashboard.html` — kanban 前端
