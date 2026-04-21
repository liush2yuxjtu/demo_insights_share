# insights-share Statusline 装配

> 契约来源：[proposal/proposal_statusline.md](../proposal/proposal_statusline.md)
> 交付物：
> - `statusline/insights_share_statusline.sh`
> - `insights-share/wiki_daemon/today_count.py`
> - 本文档

## 原理

1. `today_count.py` 负责写计数到 `~/.cache/insights-share/today_count.json`，被 UserPromptSubmit 钩子每次命中卡片时调用。
2. `insights_wiki_statusline.sh` 每次 Claude Code 渲染 statusline 时执行：读计数、探活 daemon、查 skill 文件，输出一行 `[share ✓|…|✗ N/today]`。
3. 可选 `.in_flight` 标记文件由 hook 在 prefetch 开始时 `touch`，结束时 `rm`；statusline 读其 mtime < 3s 作为 `…` 态。

## 装配步骤

### 1. 安装 daemon（已装可跳过）

```bash
# 默认项目根目录执行
insights-share/demo_codes/.venv/bin/python \
  insights-share/demo_codes/insights_cli.py serve \
  --host 127.0.0.1 --port 7821 \
  --store ./wiki_tree --store-mode tree \
  > /tmp/insightsd.log 2>&1 &
```

### 2. 安装 statusline 脚本

```bash
# 项目仓库 clone 后脚本已就位
chmod +x statusline/insights_share_statusline.sh
```

### 3. 配置 Claude Code `settings.json`

编辑 `~/.claude/settings.json`（或项目级 `.claude/settings.json`）：

```json
{
  "statusLine": {
    "type": "command",
    "command": "/Users/m1/projects/demo_insights_share/statusline/insights_share_statusline.sh"
  }
}
```

如果已有 statusline 命令，用 wrapper 把 badge 追加到末尾：

```json
{
  "statusLine": {
    "type": "command",
    "command": "bash -c 'printf \"%s  \" \"$(cat)\"; /abs/path/statusline/insights_share_statusline.sh'"
  }
}
```

### 4. 把计数器挂到 UserPromptSubmit hook

在 `insights-share/demo_codes/hooks/insights_prefetch.py` 任意一次"卡片落盘"后追加：

```python
from insights_share.wiki_daemon.today_count import bump
bump(card_id=first_matched_card.get("id"))
```

或直接在独立 hook 里 shell 调用：

```bash
"/usr/bin/python3" insights-share/wiki_daemon/today_count.py bump --card-id "$CARD_ID"
```

### 5.（可选）in-flight flag

在 hook 启动时：

```python
from pathlib import Path
Path.home().joinpath(".cache/insights-share/.in_flight").touch()
```

在 hook 结束时：

```python
try:
    Path.home().joinpath(".cache/insights-share/.in_flight").unlink()
except FileNotFoundError:
    pass
```

## A/B 验证开关

A 侧录制时必须**完全禁用** statusline，避免 B 特征泄漏：

```bash
SHARE_STATUSLINE=off ~/path/to/statusline/insights_share_statusline.sh
# 输出为空串，退出码 0
```

推荐在 `examples/run_human_AB.sh` 的 A 录制段显式 export：

```bash
# A 段
export SHARE_STATUSLINE=off
# … 录制 A …
unset SHARE_STATUSLINE
# B 段正常
```

## 环境变量

| 变量 | 默认 | 作用 |
|------|------|------|
| `INSIGHTS_SHARE_URL` | `http://127.0.0.1:7821` | daemon base url |
| `SHARE_STATUSLINE` | *unset* | `off` 时输出空串，整条链路禁用 |
| `SHARE_STATUSLINE_NO_COLOR` | *unset* | 非空时禁用 ANSI 色 |

## 自检

```bash
# 走 off 开关（A 侧）
SHARE_STATUSLINE=off statusline/insights_share_statusline.sh; echo "(exit=$?)"

# 走正常渲染
SHARE_STATUSLINE_NO_COLOR=1 statusline/insights_share_statusline.sh

# 手工 bump 3 次，statusline 数字应递增
/usr/bin/python3 insights-share/wiki_daemon/today_count.py reset
for i in 1 2 3; do
  /usr/bin/python3 insights-share/wiki_daemon/today_count.py bump --card-id demo-$i
  SHARE_STATUSLINE_NO_COLOR=1 statusline/insights_share_statusline.sh
done
```

期望输出形如：

```
[share ✓ 1/today]
[share ✓ 2/today]
[share ✓ 3/today]
```

（`✓` 依赖 daemon 可达；若 daemon 未启动会退化为 `✗ 3/today`。）

## 故障诊断

| 症状 | 原因 | 修复 |
|------|------|------|
| 一直 `✗ 0/today` | daemon 没跑或端口不对 | `curl http://127.0.0.1:7821/healthz` 直接探活 |
| daemon up 但 `✗` | skill 未装 | `ls ~/.claude/skills/insights-share/SKILL.md` |
| 数字不增 | hook 没调 bump / A/B 开关被锁 off | `python3 today_count.py read` 看原始 record |
| 卡死 > 300ms | 网络抖动 | 60s TTL 缓存会在下次渲染用缓存 |
| A/B 验证漂移 | A 侧没 export `SHARE_STATUSLINE=off` | 检查 `examples/run_human_AB.sh` |

## 日切行为

- 本地时区 00:00 第一次 `bump` 时读取到旧 `date`，自动：
  - atomic rename 旧文件到 `today_count.json.bak`
  - 写入全新 `{date: 今天, count: 1}`
- statusline 在日切瞬间若读到空文件，显示 `0/today`，不会卡住。
