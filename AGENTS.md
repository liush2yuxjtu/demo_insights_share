# AGENTS.md

仅索引 E2E 相关入口。规则总表见 [CLAUDE.md](CLAUDE.md)。

## E2E 分层

| 层 | 作用 | 入口 | 产物 |
|----|------|------|------|
| Playwright 录屏层 | `insights_cli.py serve` + chromium 录完整 user-flow | [insights-share/validation/scripts/handout_record.mjs](insights-share/validation/scripts/handout_record.mjs) | `insights-share/validation/artifacts/handout/runs/<ts>/user-flow.mp4` |
| Playwright 回放校验 | 回放录屏、比对 manifest | [insights-share/validation/scripts/handout_verify.mjs](insights-share/validation/scripts/handout_verify.mjs) | 退出码 + `artifacts/handout/latest.json` |
| tmux smoke 层 | `start.demo.sh` / `start.{claude,codex}.sh` 在 register-session 下全流程实机 debug | [insights-share/validation/run_start_tmux_smoke.sh](insights-share/validation/run_start_tmux_smoke.sh) | `insights-share/validation/reports/deliverables/tmux_*_smoke.txt` |
| tmux driver | start.demo.sh 自动驾驶脚本 | [insights-share/validation/start_demo_driver.sh](insights-share/validation/start_demo_driver.sh) | stdout + reports |
| pytest 集成层 | HTTP / CLI / handout / plugin / runtime-store 行为契约 | [insights-share/validation/run_all_validations.sh](insights-share/validation/run_all_validations.sh) | `insights-share/validation/reports/final_report.html` |

## Playwright 入口

| 命令 | 作用 |
|------|------|
| `cd insights-share/validation && npm run handout:record` | 起 daemon + 录屏，生成 mp4/console.log/manifest |
| `cd insights-share/validation && npm run handout:verify` | 回放 latest run，门控退出码 |

## tmux smoke 入口

| 命令 | 作用 |
|------|------|
| `.claude/skills/register-session/register-session.sh <name>` | 先注册实机 tmux session（live-terminal 契约） |
| `bash start.demo.sh` | human-last-visible surface；feature 新增必跑 |
| `bash insights-share/validation/run_start_tmux_smoke.sh` | 批量扫 start.claude.sh / start.codex.sh smoke |
| `bash insights-share/validation/start_demo_driver.sh` | start.demo.sh 自动驾驶 |

## pytest 入口

| 测试文件 | 覆盖面 |
|----------|--------|
| [test_cli_api.py](insights-share/validation/test_cli_api.py) | `insights_cli.py` HTTP + CLI |
| [test_handout_api.py](insights-share/validation/test_handout_api.py) | handout / runtime-web 握手 |
| [test_preview_api.py](insights-share/validation/test_preview_api.py) | standalone preview |
| [test_topic_api.py](insights-share/validation/test_topic_api.py) | Topic Good/Bad 并列 API |
| [test_topic_store.py](insights-share/validation/test_topic_store.py) | wiki_tree Topic 存储 |
| [test_runtime_store.py](insights-share/validation/test_runtime_store.py) | runtime 状态机 |
| [test_plugin_contract.py](insights-share/validation/test_plugin_contract.py) | plugin 契约 |
| [test_start_scripts.py](insights-share/validation/test_start_scripts.py) | start.*.sh 合约 |
| [test_statusline.py](insights-share/validation/test_statusline.py) | statusline 徽章 |
| [test_standalone_page.py](insights-share/validation/test_standalone_page.py) | 静态导出页 |
| [test_ab_demo_plan.py](insights-share/validation/test_ab_demo_plan.py) | A/B demo plan |
| [test_examples_demo_scripts.py](insights-share/validation/test_examples_demo_scripts.py) | `examples/` 脚本回归 |
| [test_release_package.py](insights-share/validation/test_release_package.py) | release 打包契约 |
| `run_all_validations.sh` | 汇总 Phase 0–5 产物 → `reports/final_report.html` |

## 辅助 smoke 脚本

| 脚本 | 用途 |
|------|------|
| [phase2_bob_session.sh](insights-share/validation/phase2_bob_session.sh) | Phase 2 Bob 会话回放 |
| [phase3_crud.sh](insights-share/validation/phase3_crud.sh) | Phase 3 wiki CRUD |
| [tmux_with_without.sh](insights-share/validation/tmux_with_without.sh) | with/without 对照实验 |
| [server_host_demo.sh](insights-share/validation/server_host_demo.sh) | server-host demo |
| [wiki_upload_demo.sh](insights-share/validation/wiki_upload_demo.sh) | wiki 上传 demo |
| [guide_loop.sh](insights-share/validation/guide_loop.sh) | Guide 引导循环 |

## 约束

| 约束 | 来源 |
|------|------|
| 实机测试日志走 `~/.claude/live_terminal/` 契约 | [docs/rules/live-terminal.md](docs/rules/live-terminal.md) |
| tmux 嵌套必 `unset TMUX` | [docs/rules/tmux-nested.md](docs/rules/tmux-nested.md) |
| feature 必在 start.demo.sh self-verify | [docs/rules/start-demo-verify.md](docs/rules/start-demo-verify.md) |
| start.demo.sh 缺 session 必走 register-session | [docs/rules/start-demo-register-fallback.md](docs/rules/start-demo-register-fallback.md) |
