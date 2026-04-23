# TODOS

> 本文件维护 `/plan-eng-review` 结果中 user 决策为 "添到 TODOS.md" 的条目，提交者是 m1。新增条目格式参考 `.claude/skills/review/TODOS-format.md`（若存在）。

---

## Open — ship-blocker

### [SB-1] start.demo.sh 主入口改走 `claude plugin install`

- **What**：Stage 2 + Stage 3 现在 `cp -R skill × 2` + `cp settings.json × 2`，改成 `HOME=$SANDBOX_HOME claude plugin install <local-tarball-path or LAN marketplace>`。delete 两份手动 cp 路径。
- **Why**：design doc `proposal/proposal_plugin_design.md:88,267` 明文要求 demo path 必含 `plugin install` + PM zero bash；codex outside voice (2026-04-23) 指出当前实现是绕开 shipping contract 的 dev-only 捷径；`/plan-eng-review` D2 override 落定。
- **Pros**：demo 路径与真实 yesterday-teammate install 路径同构；小鸭子机器验证自动覆盖；取消双脚本（start.clean.sh 不再需要）；未来 plugin install 断掉第一时间在 demo 崩出。
- **Cons**：需要 Stage 5 daemon 启动顺序微调（plugin install 可能提前触发 hook，daemon 未 up 会报错）；需要准备 local tarball 或 pin marketplace URL；dry-run seam 要同步改。
- **Context**：现 start.demo.sh:89-108 做的 cp-R 是沙箱时代 workaround；plugin marketplace（`plugins/insights-share/.claude-plugin/marketplace.json`）已就绪；`claude plugin install` 命令 CLI 已在 `~/.claude/CLAUDE.md` 文档化。
- **Depends on / blocked by**：需先 land `[SB-2] start.demo.sh --dry-run` 以便在不起 tmux 前验证；需先 land D5 白名单归档，否则 plugin install 后残留文件归档会漏。
- **Estimate**：human ~½ day / CC ~2h。
- **Source**：plan-eng-review 2026-04-23 m1-main, codex outside voice D2 override。

### [SB-2] start.demo.sh 新增 `--dry-run` seam

- **What**：start.demo.sh 支持 `DRY_RUN=1` 或 `--dry-run` flag，跳过 Stage 5 daemon 启动和 tmux attach，打印 7 stages 结果 + LEFT_SH + RIGHT_SH 内容 dump + cleanup 归档路径 plan。
- **Why**：start.claude.sh 和 start.codex.sh 已有 dry-run，start.demo.sh 独缺；codex 指出现存 `test_start_scripts.py` 只 grep 脆弱 sentinel 字符串，无法抓 heredoc quoting / pane 生成 / cat FEATURES.md / plugin install 路径 / strict-mode 回归；`/plan-eng-review` D6 override。
- **Pros**：test_start_scripts.py 可用 dry-run stdout 做 schema 断言；CI 可白盒验证 stage 顺序；未来 commit 改 start.demo.sh 第一时间知道 breakage。
- **Cons**：dry-run 必须每次跟 real run 保持一致；多分支 (minimax / subscription / daemon-reuse) 都要 dry-run 覆盖；`~700` 行 start_demo_driver.sh 的实现可参考但不能 blindly copy（start.demo.sh 更复杂）。
- **Context**：start_demo_driver.sh 的 `--dry-run` 实现（行 ~650+）是参考样板；test_start_scripts.py:84 的 `_run_dry` helper 可复用。
- **Depends on / blocked by**：无，可并行 SB-1 开工。
- **Estimate**：human ~2h / CC ~45min。
- **Source**：plan-eng-review 2026-04-23 m1-main, codex outside voice D6 override。

---

## Open — follow-up

### [FL-1] CI/pre-commit gate：改 start.demo.sh 或 FEATURES.md 自动跑 dry-run + test_start_scripts.py

- **What**：GitHub Actions workflow 或 pre-commit hook 监视 `start.demo.sh` / `FEATURES.md` / `insights-share/validation/test_start_scripts.py` 改动，自动跑 `DRY_RUN=1 bash start.demo.sh` + `pytest -x insights-share/validation/test_start_scripts.py`。失败 block PR。
- **Why**：第一次 FEATURES.md↔start.demo.sh drift（commit `5fb6ffb feat(demo): ... echo 6 CORE FEATURES checklist` vs `test_start_scripts.py:45` 断言 `5 个命令 + 2 个 agent`）在本轮 /plan-eng-review 才被发现，已潜伏 >= 2 次 commit。CI gate 能把 drift 发现时间从"下次人眼 review"压到"改了即爆"。
- **Pros**：drift 零潜伏；新人改 FEATURES.md 后立刻知道要同步；未来其他 contributors 不会绕过 test drift。
- **Cons**：CI 跑时间增加（dry-run <= 1s，pytest <= 2s，可忽略）；若 dry-run 本身 flaky 会 block 无关 PR。
- **Context**：等 [SB-2] dry-run 落成后才能做；现 CI workflow 存不存待查（未扫 `.github/workflows/`）。
- **Depends on / blocked by**：[SB-2] dry-run seam must land first.
- **Estimate**：human ~1h / CC ~20min。
- **Source**：plan-eng-review 2026-04-23 m1-main。

### [FL-2] corpus secret 自检升级为 start.demo.sh Stage 0

- **What**：在 start.demo.sh 预检之后、Stage 1 创建沙箱之前插入 Stage 0：grep `insights-share/demo_codes/wiki_tree/**/raw/` 查 `sk-*/ghp_*/Bearer */AKIA*` 等 secret pattern。命中则 die，提示用户先 scrub。
- **Why**：design doc F6 原方案靠用户手跑 grep（DM yesterday-teammate 前）；codex 指出 corpus 里已有 live-looking secret 痕迹；依赖人类记忆在 demo 前执行，可靠性低。`/plan-eng-review` TODO-3 user override 升级到自动化。
- **Pros**：忘不了；sponsor 打开 wiki 第一眼不会看到明文 secret；LAN 内部配 secret 泄漏风险降一档。
- **Cons**：每次跑 start.demo.sh 多 < 1s 的 grep 开销；false positive 会 block 合法 demo（例如用户在 raw log 里用了 placeholder 字符串形似 token）；die 消息要给清晰的 bypass 指引。
- **Context**：wiki_tree 258 张卡的 raw_log 字段目前直连存储；design doc `## Codex Outside Voice Revisions F6` 指向具体 grep pattern；沙箱逻辑已由 feedback_real_sandbox.md 严格约束。
- **Depends on / blocked by**：无，可在任何时间独立 land。
- **Estimate**：human ~½h / CC ~15min。
- **Source**：plan-eng-review 2026-04-23 m1-main, design doc F6 演进。

---

## Closed / Deferred

（本文件首次创建，暂无关闭项）
