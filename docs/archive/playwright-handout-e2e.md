# Playwright Handout E2E 归档

## 归档结论

Playwright handout 录屏/回放不再属于默认用户 E2E 验证路径。

当前用户验证主路径只保留：

| 层 | 入口 | 用途 |
|----|------|------|
| hero demo | `bash start.demo.sh` | PM 可见实机闭环 |
| demo driver | `bash insights-share/validation/start_demo_driver.sh` | 自动驾驶 `start.demo.sh` |
| tmux smoke | `bash insights-share/validation/run_start_tmux_smoke.sh` | `start.claude.sh` / `start.codex.sh` 实机启动验证 |
| 合同 / 汇总 | `bash insights-share/validation/run_all_validations.sh` | HTTP / CLI / plugin / runtime-store / adoption proof 合同与报告 |

## 为什么归档

浏览器层原本用于验证 handout runtime-web 页面是否能打开、录制 `user-flow.mp4`、并用 manifest 回放校验。

当前用户明确不需要浏览器 E2E；因此默认验证不再要求 Chromium、Playwright 视频转码或 handout 录屏产物。

## 历史入口

脚本保留在仓库中，作为历史审计或专项排查工具：

| 命令 | 历史用途 | 历史产物 |
|------|----------|----------|
| `cd insights-share/validation && npm run handout:record` | 起 daemon + Chromium 录完整 handout user-flow | `insights-share/validation/artifacts/handout/runs/<ts>/user-flow.mp4` |
| `cd insights-share/validation && npm run handout:verify` | 回放 latest manifest 并用退出码门控 | `insights-share/validation/artifacts/handout/latest.json` |

除非任务明确要求“浏览器 handout 录屏”“Playwright 回放”或“检查旧 user-flow.mp4”，不要把上述命令放回默认 E2E 步骤。
