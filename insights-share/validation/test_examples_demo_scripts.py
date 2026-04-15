from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RUN_HUMAN_AB = ROOT / "examples/run_human_AB.sh"
VALIDATE_COMMANDS = ROOT / "examples/validate_commands.sh"
PROJECT_CLAUDE_SETTINGS = ROOT / ".claude/settings.json"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_run_human_ab_uses_isolated_tmp_workspaces() -> None:
    script = _read(RUN_HUMAN_AB)

    assert 'DEMO_ENV_SRC="${REPO_ROOT}/insights-share/demo_codes/.env"' in script
    assert 'WORKSPACE_A="/tmp/demo_insights_A"' in script
    assert 'WORKSPACE_B="/tmp/demo_insights_B"' in script
    assert 'CLONE_DIR="${WORKSPACE_B}/isw-clone"' in script
    assert 'DAEMON_LOG="${WORKSPACE_B}/isd.log"' in script
    assert 'A_SETTINGS="${WORKSPACE_A}/.claude/settings.json"' in script
    assert 'B_SETTINGS="${WORKSPACE_B}/.claude/settings.json"' in script
    assert 'A_EXPORT="${WORKSPACE_A}/A_without.human.md"' in script
    assert 'B_EXPORT="${WORKSPACE_B}/B_with.human.md"' in script
    assert 'WAIT_TRUST_CONFIRM=4' in script
    assert '接受 trust prompt' in script
    assert "You've hit your limit" in script
    assert 'rsync -a --delete \\' in script
    assert 'ACTIVE_SETTINGS_DST="${HOME}/.claude/settings.json"' in script
    assert 'backup_active_settings' in script
    assert 'restore_active_settings' in script
    assert 'activate_settings "${A_SETTINGS}"' in script
    assert 'activate_settings "${B_SETTINGS}"' in script
    assert 'require_file "${DEMO_ENV_SRC}" "A/B 录制 .env"' in script
    assert 'require_file "${CLONE_DIR}/insights-share/demo_codes/.env" "B 轮 clone .env"' in script
    assert 'start_cmd="cd \\"${WORKSPACE_A}\\" && bash -lc \'set -a; source \\"${env_src}\\"; set +a; exec claude\'"' in script
    assert 'start_cmd="cd \\"${WORKSPACE_B}\\" && bash -lc \'set -a; source \\"${env_src}\\"; set +a; exec claude\'"' in script
    assert 'git clone --depth 1' not in script
    assert 'cp "${A_EXPORT}" "${EXAMPLES_DIR}/A_without.human.md"' in script
    assert 'cp "${B_EXPORT}" "${EXAMPLES_DIR}/B_with.human.md"' in script
    assert 'cd ${DEMO_CWD} && claude' not in script


def test_run_human_ab_explicitly_proves_pwd_and_skill_state() -> None:
    script = _read(RUN_HUMAN_AB)

    assert 'PROMPT_WITHOUT=' in script
    assert 'PROMPT_WITH=' in script
    assert '!pwd' in script
    assert '!ls -la ~/.claude/skills/' in script
    assert 'alice-pgpool-2026-04-10' in script


def test_run_human_ab_replays_current_fix_state_and_validates_exports() -> None:
    script = _read(RUN_HUMAN_AB)

    assert 'write_b_workspace_settings()' in script
    assert 'CLAUDE_CODE_ENABLE_AWAY_SUMMARY' in script
    assert 'insights_stop_hook.py' in script
    assert 'insights_prefetch.py >/dev/null 2>&1 &' in script
    assert 'defaultMode": "bypassPermissions"' in script
    assert '"skipDangerousModePermissionPrompt": true' in script
    assert 'PANE_STABLE_MIN_ELAPSED=120' in script
    assert 'PANE_STABLE_REQUIRED=2' in script
    assert 'pane 连续稳定，提前结束等待' in script
    assert 'Step 9: 校验导出内容' in script
    assert 'Stop hook error' in script
    assert 'Interrupted' in script
    assert 'Skill(insights-wiki)' in script
    assert 'A 轮导出被污染' in script
    assert 'B 轮导出未引用 alice-pgpool-2026-04-10' in script


def test_project_settings_disable_away_summary() -> None:
    settings = _read(PROJECT_CLAUDE_SETTINGS)

    assert '"plansDirectory": ".claude/plans"' in settings
    assert '"CLAUDE_CODE_ENABLE_AWAY_SUMMARY": "0"' in settings


def test_validate_commands_matches_current_three_step_demo() -> None:
    script = _read(VALIDATE_COMMANDS)

    assert '/tmp/demo_insights_A/A_without.log' in script
    assert '/tmp/demo_insights_B/isw-clone' in script
    assert '/tmp/demo_insights_B/B_with.log' in script
    assert '❌ git clone 失败，请检查 github 配置（ssh key / https token）后重试' in script
    assert '✅ Step 2a: clone 完成 → /tmp/demo_insights_B/isw-clone' in script
    assert '✅ Step 2b: B_with.log' in script
    assert 'grep -c alice-pgpool-2026-04-10 /tmp/demo_insights_A/A_without.log /tmp/demo_insights_B/B_with.log' in script
