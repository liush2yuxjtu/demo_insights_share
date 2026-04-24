# insights-share — 核心功能清单（canonical feature manifest）

> 本文件是 `claudefast -p "what are the main features of this projects ?"` 的**标准答案源**。
> `start.demo.sh` 右 pane self-check 会原样 echo 本文件用作实机证据。
> 任何 feature 增删必须同步更新本文件 + proposal/INDEX.md + CLAUDE.md 索引表。

---

## 1. Topic 中心 Good/Bad 并列

- 同一 Topic 下多人多场景决策并列展示，不合并、不挑最优、不做冲突检测
- `label=good` = 此场景下**选了**此方案（采纳决策）
- `label=bad`  = 此场景下**拒绝了**此方案（避免决策）
- 两者全部 `status=active` 并列渲染；消费方凭 `applies_when` 自行匹配场景
- 权威设计：[proposal/proposal_conflict_design.md](proposal/proposal_conflict_design.md)
- 存储形态：`insights-share/demo_codes/wiki_tree/{wiki_type}/{slug}.md`（tree 模式）

## 2. Statusline 实时反馈（5 态徽章）

Claude Code 状态栏常驻 `[share <icon> N/today]` 徽章：

| 态 | 条件 | 含义 |
|----|------|------|
| `✓` | daemon 可达 + today_count ≥ 1 | 正常命中 |
| `✗` | daemon 断链或 skill 未装 | 失效 |
| `…` | prompt prefetch / match 中 | 进行中 |
| `⚠ stale` | 最近命中卡片 TTL 过期 | M3 新增 |
| `🔒 sig-fail` | 卡片 ed25519 签名校验失败 | M4 新增 |

- 渲染脚本：`plugins/insights-share/statusline/insights_share_statusline.sh`
- 计数存储：`~/.cache/insights-share/today_count.json`
- 设计：[proposal/proposal_statusline.md](proposal/proposal_statusline.md)

## 3. Claude Code Plugin 封装

- 一条 `claude plugin install` 完成 skill + hook + statusline + MCP + agent + slash 命令的注册
- MVP 演示面**零 bash**，全部走 slash 命令
- manifest：`plugins/insights-share/.claude-plugin/plugin.json`（当前 `0.6.1-m7`）
- 内网 marketplace：`.claude-plugin/marketplace.json`
- 升级 / 卸载：`claude plugin upgrade|uninstall insights-share`
- 设计：[proposal/proposal_plugin_design.md](proposal/proposal_plugin_design.md)
- 命名迁移：[proposal/proposal_rename_to_insights_share.md](proposal/proposal_rename_to_insights_share.md)

## 4. 核心 Slash 命令（5 条）

| 命令 | 作用 | 落点 |
|------|------|------|
| `/share-install` | 安装 + 连服 + 自检 | `plugins/insights-share/commands/share-install.md` |
| `/share-search <topic>` | 查 topic 下 Good/Bad 并列 | `commands/share-search.md` |
| `/share-publish` | 发布新卡片（走 share-validator agent 校验） | `commands/share-publish.md` |
| `/share-review` | 管理员看板 CRUD（走 share-curator agent） | `commands/share-review.md` |
| `/share-diff <topic>` | 并列决策图谱视图 | `commands/share-diff.md` |

配套 agent：
- `agents/share-validator.md` — 发布前合法性校验
- `agents/share-curator.md`  — 管理员 CRUD 协调

## 5. 安全与分发

- **ed25519 卡片签名**：发布时签、加载时验，失败走 `[share 🔒 sig-fail]` 降级
- **Team namespace**：卡片路径 `wiki_tree/<team>/<topic>/`，向后兼容无 team
- **TTL + stale 徽章**：卡片过期后状态栏显示 `[share ⚠ stale]`，信任衰减可见
- **内网 marketplace**：LAN 7821 `insightsd` 守护进程 + `publish_marketplace.py`
- **双仓分发（v0.6.0-m7）**：dev 仓（全量）+ plugin 仓（精简 108K），`claude plugin install` 走 plugin 仓
- **离线 cache-first 兜底**：LAN 掉线不崩
- 发布脚本：`plugins/insights-share/scripts/publish_marketplace.py`

## 6. 数据模型（Topic / Example Schema）

每条 Example 必有：

| 字段 | 作用 |
|------|------|
| `id` | `{author}-{slug}-{date}` 全局唯一 |
| `topic_id` | 所属 Topic |
| `author` | 上传者 |
| `label` | `good` / `bad` |
| `label_override` / `label_override_by` / `label_override_at` | 管理员可覆盖，不改原 label |
| `summary` | 方案一句话 |
| `applies_when` | **场景刻画**：本决策适用的场景条件（核心字段） |
| `do_not_apply_when` | **场景排除**：本决策不适用的场景 |
| `raw_log_type` | `export` / `jsonl` |
| `raw_log` | 完整原始日志（明文存储，管理员**不可修改**） |
| `raw_log_path` | jsonl 来源的原始文件路径 |

- Schema 速查：[proposal/proposal_wiki_card.md](proposal/proposal_wiki_card.md)
- API：`POST /topics` / `POST /topics/{id}/examples` / `POST /topics/{id}/examples/{eid}/relabel` / `GET /topics?q=` / `GET /topics/{id}/examples?label=good|bad`

---

## 验证入口

| 验证 | 命令 |
|------|------|
| 整体功能自检 | `bash start.demo.sh`（right pane 会 echo 本文件）|
| Plugin 签名 / 布局自检 | `bash plugins/insights-share/scripts/self_check.sh` |
| A/B 导出门禁 | `bash insights-share/examples/run_human_AB.sh` → 对比 examples/A_without.human.md vs B_with.human.md |
| 触发率验证 | `insights-share/validation/trigger_rate.py`（train f1 ≥ 0.67，test f1 ≥ 0.75）|
| Probe 自检 | `claudefast -p "what are the main features of this projects ? "` 应覆盖以上 6 项全部 |
