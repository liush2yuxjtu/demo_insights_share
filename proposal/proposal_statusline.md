# Proposal: Statusline 活跃度反馈

## 问题

insights-share 当前对用户/client **不可感知**：

- 注入缓存卡片走 silent background，成功或失败均无反馈
- 用户无法判断今天有没有真正命中过 wiki
- demo 场景里 PM 看不到"这套东西到底有没有在工作"
- bug 复盘时拿不到"今日触发次数"这条基础信号

## 目标

用 Claude Code statusline 持续展示 insights-share 工作状态 + 今日累计触发次数，给用户/client 一条**实时信任感信号**。

## 信号最小集

statusline 右侧常驻两段信息：

```
[share ✓ N/today]    insights-share 运行中，今天已触发 N 次
[share ✗ 0/today]    daemon/skill 未装或未命中任何 prompt
[share … N/today]    命中在途（fetch/verify 中）
```

三态对应:

| 状态 | 条件 | 含义 |
|------|------|------|
| `✓` | daemon reachable + today_count ≥ 1 | 已装 + 今天至少用过一次 |
| `✗` | daemon unreachable 或 skill 未安装 | 断链，整条闭环失效 |
| `…` | 当前 prompt 正在 prefetch / match | 进行中 |

## 计数口径

- 粒度: 单个 prompt 命中一次卡片 ≡ +1
- 口径: 任意卡片被 UserPromptSubmit 预热或 agent 引用均计入
- 重置: 本地时区自然日 0 点
- 存储: `~/.cache/insights-share/today_count.json`

```json
{
  "date": "2026-04-21",
  "count": 7,
  "last_card_id": "alice-pgpool-2026-04-10",
  "last_trigger_at": "2026-04-21T14:02:11+08:00"
}
```

## 数据源

statusline script 每次渲染读三处：

1. `~/.cache/insights-share/today_count.json` → today_count + last card
2. `curl -s --max-time 0.3 http://<wiki_host>:7821/health` → daemon 可达性
3. `ls ~/.claude/skills/insights-share/SKILL.md` → skill 安装性

三者任一失败 → `✗`。

## 约束

- 渲染耗时必须 < 100ms；daemon 探活用短超时 (300ms) + 本地缓存 (60s TTL)
- 计数写入走 append-only，避免 statusline 频繁读写锁
- 日切交接用原子 rename 落盘，不允许出现 `date != today && count != 0` 的残留
- A/B 验证场景下 A 侧强制走 `SHARE_STATUSLINE=off`，禁止泄漏 B 特征

## 交付物

1. `statusline/insights_share_statusline.sh` - bash 渲染脚本
2. `insights-share/wiki_daemon/today_count.py` - 计数写入器（UserPromptSubmit 钩子调用）
3. `docs/statusline_install.md` - 装配步骤
4. tmux 录屏证据：同一 session 连续 3 次 prompt，statusline 数字从 `N` → `N+1` → `N+2`

## 非目标

- 不做 per-card 命中率统计（留给后续 dashboard）
- 不做跨设备聚合
- 不改 insights-share 触发策略本身

## 预期输出

### 整行渲染

Claude Code statusline 右侧追加 wiki badge：

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ ~/projects/demo_insights_share  main*  claude-opus-4-7       [share ✓ 7/today] │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 三态 badge

```
[share ✓ 7/today]     daemon reachable + 今日已命中 7 次
[share … 7/today]     当前 prompt 正在 prefetch/match
[share ✗ 0/today]     daemon 断链 or skill 未装
```

### 日内递增（同一 session 连发 3 个 prompt）

```
prompt #1 发出   → [share … 0/today]
prompt #1 命中   → [share ✓ 1/today]
prompt #2 发出   → [share … 1/today]
prompt #2 命中   → [share ✓ 2/today]
prompt #3 发出   → [share … 2/today]
prompt #3 未命中 → [share ✓ 2/today]     # 不计数，但保持 ✓
```

### 日切（本地 00:00）

```
23:59 → [share ✓ 42/today]
00:00 → [share ✓ 0/today]                # 原子 rename 到 today_count.json.bak
```

### 故障降级

```
daemon 挂    → [share ✗ 7/today]         # 计数保留，仅标记断链
skill 未装   → [share ✗ 0/today]
探活超时     → [share ✗ 7/today]         # 300ms 内无响应即降级
```

### 配色（terminal 支持时）

```
✓  绿  (\033[32m)
…  黄  (\033[33m)
✗  红  (\033[31m)
数字  默认色，确保跨主题可读
```

### 宽度预算

badge 本体 ≤ 20 char，不抢占左侧 path / branch / model 段。
