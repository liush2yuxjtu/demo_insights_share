# Finish Log: UC-1 Plugin Bundle Self-Containment

## What Changed

- Closed `UC-1 plugin bundle self-containment`.
- Added bundle-local server runtime under `plugins/insights-share/runtime/`:
  - `runtime/insights_cli.py`
  - `runtime/insightsd/`
  - `runtime/wiki_tree/`
- Rewrote `plugins/insights-share/skills/insights-share-server/scripts/start_server.sh` and `start_ui.sh` so they launch from the installed plugin runtime, not from `insights-share/demo_codes` or `demo_codes/.venv`.
- Updated `plugins/insights-share/scripts/self_check.sh` to verify:
  - `server runtime bundle: OK`
  - `start_server.sh: OK`
  - `start_ui.sh: OK`
  - runtime Python parse checks.
- Updated `start.demo.sh` Stage 5 to launch insightsd through the sandbox installed plugin cache after real `claude plugin install`.
- Updated `start.demo.sh` right pane evidence to read manifest/statusline/commands/agents/sample/self-check from the sandbox installed plugin cache.
- Updated release/package contracts so the plugin runtime files are included in release output and marketplace checksum summary.

## Important Runtime Detail

The plugin seed corpus in `runtime/wiki_tree/` is treated as unsigned bundled seed data. New cards written by the daemon are still signed. This prevents clean installs from requiring a developer machine's old trusted key before first search can work.

## Verification

- `bash insights-share/validation/run_contract_tests.sh insights-share/validation/test_plugin_contract.py -q` passed: 12 tests.
- `bash insights-share/validation/run_contract_tests.sh` passed: 43 tests.
- `bash insights-share/validation/run_ci_gate.sh` passed.
- 历史加强门 `RUN_HANDOUT_VERIFY=1 RUN_TMUX_SMOKE=1 bash insights-share/validation/run_ci_gate.sh` 当时 passed:
  - 43 contract tests
  - adoption proof
  - `start.demo.sh --dry-run`
  - Playwright handout verify
  - tmux claude/codex smoke
- Cleanup status: no residual `:7821` or `:18821` daemon listener.
- Workspace status: only pre-existing untracked `.claude/settings.local.json` remains outside this work.

## Work-Specific Probe

Use this exact probe for this work:

```bash
claudefast -p "what is UC-1 plugin bundle self-containment status?"
```

The correct answer must say:

- `UC-1 plugin bundle self-containment` is done.
- `plugins/insights-share/runtime/` now carries server runtime and seed corpus.
- `start_server.sh` / `start_ui.sh` no longer depend on repo checkout or `demo_codes/.venv`.
- `start.demo.sh` now launches daemon and right-pane self-check from the sandbox installed plugin cache.
- 本工作当时的历史验证包含 43 项合同测试、adoption proof、`start.demo.sh --dry-run`、Playwright handout verify、tmux claude/codex smoke。当前默认 E2E 已归档 Playwright handout verify；最新状态以 `docs/CURRENT_STATUS.md` 为准。

## Probe Results

- Work-specific probe passed:
  ```bash
  claudefast -p "what is UC-1 plugin bundle self-containment status?"
  ```
  It returned `UC-1 Plugin Bundle Self-Containment: DONE` and covered bundle runtime, server scripts, `start.demo.sh`, seed signing strategy, and verification evidence.
- READ ONLY finish flag passed:
  ```bash
  claudefast -p "READ ONLY, tell me what we have done in recent commits and based on docs. Reply JSON: {\"verdict\":\"PASS|REFINE|FAIL\", \"recent_commits\":[hashes], \"docs_referenced\":[paths], \"summary\":\"<≤120字>\", \"missing_or_inconsistent\":[]}"
  ```
  It returned `{"verdict":"PASS", ... "missing_or_inconsistent":[]}`.
