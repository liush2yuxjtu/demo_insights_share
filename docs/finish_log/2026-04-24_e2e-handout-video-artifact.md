# 2026-04-24 E2E handout video artifact

## 完成内容

- 修复 `insights-share/validation/scripts/handout_record.mjs`：
  - `handout:record` 现在会确认 `user-flow.mp4` 真实存在且非空后才写 passed manifest。
  - 当 AVFoundation 整屏录制失败时，使用 Playwright `recordVideo` 生成兜底视频，并用 ffmpeg 转码为 `user-flow.mp4`。
  - 如果 ffmpeg 与 Playwright 兜底都失败，P4 会真实失败，不再留下指向缺失 mp4 的 passed manifest。
- 新增 `insights-share/validation/test_handout_record_artifact.py`，静态锁定 handout record 的视频产物合同。

## 验证

- `node --check insights-share/validation/scripts/handout_record.mjs`：PASS
- `bash insights-share/validation/run_contract_tests.sh insights-share/validation/test_handout_record_artifact.py insights-share/validation/test_run_all_validations.py`：4 passed
- `cd insights-share/validation && npm run handout:record`：PASS，latest `user-flow.mp4` 已落盘
- `codex exec "start e2e tests and show me results ONLY"`：PASS
  - 时间：2026-04-24 14:01:45
  - required：6/6 PASS
  - enabled：6/6 PASS
  - P1/P4/P5/P6/P7 均 PASS，P3/AP-1/P2 按本次 E2E 口径跳过

## 产物

- 汇总报告：`insights-share/validation/reports/final_report.html`
- 汇总 JSON：`insights-share/validation/reports/final_summary.json`
- handout record manifest：`insights-share/validation/artifacts/handout/latest.json`
- handout verify manifest：`insights-share/validation/artifacts/handout/verify-latest.json`
