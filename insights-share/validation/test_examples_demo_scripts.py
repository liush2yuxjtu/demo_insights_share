from __future__ import annotations

from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[2]
RUN_HUMAN_AB = ROOT / "examples/run_human_AB.sh"
VALIDATE_COMMANDS = ROOT / "examples/validate_commands.sh"
PROJECT_CLAUDE_SETTINGS = ROOT / ".claude/settings.json"
A_EXPORT = ROOT / "examples/A_without.human.md"
B_EXPORT = ROOT / "examples/B_with.human.md"

COMMON_PROMPT = (
    "请严格按顺序执行三步。第一步：运行 !pwd 打印当前工作目录。"
    "第二步：运行 !ls -la ~/.claude/skills/ 展示已安装的 skill 列表；"
    "如果 ~/.claude/skills/insights-wiki/SKILL.md 存在，再运行 "
    "!head -40 ~/.claude/skills/insights-wiki/SKILL.md 读取前 40 行；"
    "如果 ~/.cache/insights-wiki/manifest.json 存在，再运行 "
    "!cat ~/.cache/insights-wiki/manifest.json 查看缓存卡片 ID；"
    "若上述文件不存在也要明确说明该事实。"
    "第三步：回答 — 我们的 checkout API 正在超时，postgres 在午餐高峰拒绝新连接"
    "（English restate: Our checkout API is timing out, postgres is rejecting "
    "new connections during the lunch spike），"
    "应该如何诊断与修复？请给出可执行的 SQL 与代码片段。"
    "如果第二步发现 ~/.cache/insights-wiki 中有相关卡片，请先读取与当前问题最相关的缓存卡片再作答，"
    "并明确引用卡片 ID；若缓存不存在或未命中，请明确写“未引用任何 LAN 卡片”。"
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _extract_single_quoted_shell_var(script: str, name: str) -> str:
    match = re.search(rf"^{name}='([^']*)'$", script, re.MULTILINE)
    assert match, f"missing shell variable: {name}"
    return match.group(1)


def _extract_first_export_prompt(path: Path) -> str:
    prompt_lines: list[str] = []
    capture = False

    for raw_line in _read(path).splitlines():
        if raw_line.startswith("❯ "):
            capture = True
            prompt_lines.append(raw_line.removeprefix("❯ ").strip())
            continue
        if capture:
            if raw_line.startswith("⏺ "):
                break
            prompt_lines.append(re.sub(r"^[ \t]{2,}", "", raw_line))

    assert prompt_lines, f"failed to extract first prompt from {path}"
    return re.sub(r"\s+", " ", " ".join(prompt_lines)).strip()


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
    assert 'CACHE_DIR="${HOME}/.cache/insights-wiki"' in script
    assert 'backup_active_cache' in script
    assert 'restore_active_cache' in script
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
    prompt = _extract_single_quoted_shell_var(script, "COMMON_PROMPT")

    assert "PROMPT_WITHOUT=" not in script
    assert "PROMPT_WITH=" not in script
    assert prompt == COMMON_PROMPT
    assert 'run_tmux_human without "${COMMON_PROMPT}" "${A_EXPORT}" "${A_SNAPSHOT}"' in script
    assert 'run_tmux_human with "${COMMON_PROMPT}" "${B_EXPORT}" "${B_SNAPSHOT}"' in script
    assert "!pwd" in prompt
    assert "!ls -la ~/.claude/skills/" in prompt
    assert "!head -40 ~/.claude/skills/insights-wiki/SKILL.md" in prompt
    assert "!cat ~/.cache/insights-wiki/manifest.json" in prompt
    assert "若上述文件不存在也要明确说明该事实" in prompt
    assert "English restate: Our checkout API is timing out, postgres is rejecting new connections during the lunch spike" in prompt
    assert "如果第二步发现 ~/.cache/insights-wiki 中有相关卡片" in prompt
    assert "未引用任何 LAN 卡片" in prompt


def test_human_ab_exports_share_the_exact_same_prompt() -> None:
    a_prompt = _extract_first_export_prompt(A_EXPORT)
    b_prompt = _extract_first_export_prompt(B_EXPORT)

    assert a_prompt == COMMON_PROMPT, f"A export prompt drifted:\n{a_prompt}"
    assert b_prompt == COMMON_PROMPT, f"B export prompt drifted:\n{b_prompt}"
    assert a_prompt == b_prompt, f"A/B prompts differ:\nA: {a_prompt}\nB: {b_prompt}"


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
    assert 'Step 9: 校验导出 prompt 与 COMMON_PROMPT' in script
    assert 'Step 10: 校验导出内容' in script
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
