from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RUN_HUMAN_AB = ROOT / "examples/run_human_AB.sh"
VALIDATE_COMMANDS = ROOT / "examples/validate_commands.sh"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_run_human_ab_uses_isolated_tmp_workspaces() -> None:
    script = _read(RUN_HUMAN_AB)

    assert 'WORKSPACE_A="/tmp/demo_insights_A"' in script
    assert 'WORKSPACE_B="/tmp/demo_insights_B"' in script
    assert 'CLONE_DIR="${WORKSPACE_B}/isw-clone"' in script
    assert 'DAEMON_LOG="${WORKSPACE_B}/isd.log"' in script
    assert 'A_EXPORT="${WORKSPACE_A}/A_without.human.md"' in script
    assert 'B_EXPORT="${WORKSPACE_B}/B_with.human.md"' in script
    assert 'start_cmd="cd \\"${WORKSPACE_A}\\" && claude"' in script
    assert 'start_cmd="cd \\"${WORKSPACE_B}\\" && claude"' in script
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


def test_validate_commands_matches_current_three_step_demo() -> None:
    script = _read(VALIDATE_COMMANDS)

    assert '/tmp/demo_insights_A/A_without.log' in script
    assert '/tmp/demo_insights_B/isw-clone' in script
    assert '/tmp/demo_insights_B/B_with.log' in script
    assert '❌ git clone 失败，请检查 github 配置（ssh key / https token）后重试' in script
    assert '✅ Step 2a: clone 完成 → /tmp/demo_insights_B/isw-clone' in script
    assert '✅ Step 2b: B_with.log' in script
    assert 'grep -c alice-pgpool-2026-04-10 /tmp/demo_insights_A/A_without.log /tmp/demo_insights_B/B_with.log' in script
