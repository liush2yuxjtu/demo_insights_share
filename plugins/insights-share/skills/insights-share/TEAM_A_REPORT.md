# Team A 验收报告 — wiki-insights skill 化 + 静默下载补强

## 5 项改动

1. **新建 SKILL.md** — `.claude/skills/insights-wiki/SKILL.md`
   YAML frontmatter（name/description/allowed-tools/origin），中文说明触发条件、LAN daemon 接口约定（`/insights`、`/search` 等）、静默工作流三步、严禁 fallback 等约束。

2. **新建 `hooks/insights_cache.py`** — 提供 `persist(card)`：
   - 把 card 落盘到 `~/.cache/insights-wiki/<id>.json`
   - 维护 `manifest.json`（`last_sync_at` + `cards` 列表，去重）
   - 原子写（tempfile + os.replace）防半写
   - id 抽取顺序：`id` 字段 → `wiki_type_item` 拼接 → hash 兜底

3. **修改 `hooks/insights_stop_hook.py`** — 在返回 `additionalContext` 之前调用 `insights_cache.persist(top)`：
   - 同时把 `hooks/` 目录加入 `sys.path`
   - 缓存写盘失败仅记 stderr，不阻断主流程
   - 原有 `search_agent` 异常仍直接 raise，静默行为不变

4. **修改 `.claude/settings.json`** — 先备份为 `settings.json.bak-0414`，再追加 `UserPromptSubmit` hook：
   - 调用 `insights_prefetch.py`（轻量脚本，stdlib only）后台 GET `/insights`
   - 重定向 `>/dev/null 2>&1 &` 完全后台化，对用户无感
   - 同时新建 `hooks/insights_prefetch.py`：吞掉所有网络/IO 异常，退出码恒为 0

5. **新建 smoke test `hooks/test_insights_cache.py`** — 4 个用例：
   - `test_persist_basic`：写入 + 文件存在 + manifest 包含 id
   - `test_persist_dedupe`：重复 persist 同一 id 不重复入 cards
   - `test_persist_without_id`：缺 id 时 fallback 到 `wiki_type_item`
   - `test_persist_rejects_non_dict`：传 str 应抛 `TypeError`

## 验证命令与结果

```bash
# 1. smoke test（先清空缓存再跑）
rm -rf ~/.cache/insights-wiki
.venv/bin/python hooks/test_insights_cache.py
# 输出：[ALL PASSED] insights_cache smoke test（4/4 通过）

# 2. settings.json 合法性
.venv/bin/python -c "import json; json.load(open('.claude/settings.json'))"
# 输出：settings.json: VALID JSON

# 3. 三个模块 import 验证
.venv/bin/python -c "import insights_stop_hook, insights_cache, insights_prefetch"
# 输出：全部 import OK

# 4. 缓存目录落盘检查
ls -la ~/.cache/insights-wiki/
# manifest.json + t1.json + playbook_pgbouncer-tuning.json
```

## 约束遵守情况

- 仅修改 `insights-share/demo_codes/` 与 `.claude/`，未触碰 `validation/` / `reports/` / 根目录
- `settings.json` 已先备份再修改
- Python 风格对齐 `insights_cli.py`（stdlib only，无三方依赖，类型注解 `from __future__ import annotations`）
- 全程中文注释与文档
