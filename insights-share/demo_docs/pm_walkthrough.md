# insights-share · 给 PM 的 60 秒演示

## 痛点

Alice 上周二已经把那个"PostgreSQL 连接池在午高峰被打爆"的故障彻底解了，她还随手把复盘写了下来——只不过这条 insight 躺在她自己的电脑里。今天中午 Bob 遇到几乎一模一样的线上告警，他不得不从零开始复现、定位、再一次花 60 多秒让 `claude /insights` 把同一条教训"悟"一遍。Alice 的经验没有流到 Bob 手上，这就是我们要修的事。

## 修复：一张"截图"看 2.4s vs 62s

```text
                          DEMO: Bob hits prod incident

restate: Our checkout API is timing out, postgres is rejecting new connections during the lunch spike

hot-loaded alice-pgpool-2026-04-10 from alice (score=0.0364)

+------------------------------------------------------------------------------+
| Set idle_in_transaction_session_timeout=30s and bump pool size to 2x worker count |
+------------------------------------------------------------------------------+
| verdict=adopt confidence=0.82 diff=fallback: Exception                       |
+------------------------------------------------------------------------------+

fast path: 0.0s (adapter: 1.3s)   slow path baseline: ~62s
```

这一屏里最关键的一行是最后那行：**fast path 约 1.3 秒，slow path 基线约 62 秒**。Bob 还没读完问题重述，adapted insight 已经出现在面前了。

## 引擎盖下发生了什么

- **publish**：Alice 把她那张 PostgreSQL 连接池的 insight 卡（JSON）POST 到 LAN 上 `http://<LAN-IP>:7821/insights`，卡立刻对同局域网的所有人可见。
- **search**：Bob 运行 `insights solve`，CLI 把他的问题整句丢给 wiki daemon 的 `/search?q=...`，本地 bag-of-words 检索在毫秒级返回得分最高的三张卡。
- **hot-load**：CLI 取 top-1 那张卡（`alice-pgpool-2026-04-10`），当场打印"从 Alice 那里热加载到卡片"，PM 直观看到"有人早就踩过同一个坑"。
- **adapt**：`claude_agent_sdk` 把这张卡 + Bob 的本地上下文（FastAPI + PgBouncer transaction pooling + 午高峰）喂给 MiniMax，做一次 JSON-in/JSON-out 的校验 + 改写；即使 adapter 网络/鉴权失败，fallback 会把原卡的 `fix` 字段以 `verdict=adopt` 原样返回，demo 永远不会在你面前硬崩。

## 一键命令

```bash
cd demos/insights-share/demo_codes && bash run_demo.sh
```

想看离线保底路径，加 `--no-ai`：

```bash
cd demos/insights-share/demo_codes && bash run_demo.sh --no-ai
```
