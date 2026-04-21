#!/usr/bin/env bash
# plugin M1 self-check :: 在 start.demo.sh 的 sandbox self-check 段被调用。
# 设计依据：proposal/proposal_plugin_design.md §"验证" 节。
# 输出契约：每行一个组件一条 "OK"/"MISSING"/"PARSE-FAIL"，非零退出仅当有任一 MISSING。

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

fail_count=0
say() { printf '%s\n' "$*"; }

# manifest
MANIFEST="$PLUGIN_DIR/.claude-plugin/plugin.json"
if [ -f "$MANIFEST" ]; then
  if NAME_VER="$(python3 -c 'import json,sys
m=json.load(open(sys.argv[1]))
print(m["name"]+" v"+m["version"])' "$MANIFEST" 2>/dev/null)"; then
    say "manifest: OK ($NAME_VER)"
  else
    say "manifest: PARSE-FAIL"
    fail_count=$((fail_count+1))
  fi
else
  say "manifest: MISSING"
  fail_count=$((fail_count+1))
fi

# marketplace
if [ -f "$PLUGIN_DIR/.claude-plugin/marketplace.json" ]; then
  say "marketplace: OK"
else
  say "marketplace: MISSING"
  fail_count=$((fail_count+1))
fi

# skills
for s in insights-wiki insights-wiki-server; do
  if [ -f "$PLUGIN_DIR/skills/$s/SKILL.md" ]; then
    say "skill $s: OK"
  else
    say "skill $s: MISSING"
    fail_count=$((fail_count+1))
  fi
done

# hook
if [ -x "$PLUGIN_DIR/hooks/user-prompt-submit.sh" ]; then
  say "hook UserPromptSubmit: OK"
else
  say "hook UserPromptSubmit: MISSING"
  fail_count=$((fail_count+1))
fi

# statusline
if [ -x "$PLUGIN_DIR/statusline/insights_wiki_statusline.sh" ]; then
  say "plugin statusline: OK"
else
  say "plugin statusline: MISSING"
  fail_count=$((fail_count+1))
fi

# commands
for c in wiki-install wiki-search wiki-publish wiki-review; do
  if [ -f "$PLUGIN_DIR/commands/$c.md" ]; then
    say "command /$c: OK"
  else
    say "command /$c: MISSING"
    fail_count=$((fail_count+1))
  fi
done

# agents (M2+)
for a in wiki-curator insight-validator; do
  if [ -f "$PLUGIN_DIR/agents/$a.md" ]; then
    say "agent $a: OK"
  else
    say "agent $a: MISSING"
    fail_count=$((fail_count+1))
  fi
done

# manifest declares agents + 4 commands (M2 contract)
if [ -f "$MANIFEST" ]; then
  if /usr/bin/python3 - "$MANIFEST" <<'PY' >/dev/null 2>&1
import json, sys
m = json.load(open(sys.argv[1]))
assert len(m["entry"].get("agents", [])) == 2, "agents count"
assert len(m["entry"].get("commands", [])) == 4, "commands count"
PY
  then
    say "manifest M2 contract (agents=2, commands=4): OK"
  else
    say "manifest M2 contract: FAIL"
    fail_count=$((fail_count+1))
  fi
fi

if [ "$fail_count" -gt 0 ]; then
  say "plugin self-check: FAIL ($fail_count missing)"
  exit 1
fi
say "plugin self-check: ALL GREEN"
exit 0
