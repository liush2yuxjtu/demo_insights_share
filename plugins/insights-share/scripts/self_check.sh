#!/usr/bin/env bash
# plugin M5 self-check :: 在 start.demo.sh 的 sandbox self-check 段被调用。
# 设计依据：proposal/proposal_rename_to_insights_share.md §"验证门禁"。
# 输出契约：每行一个组件一条 "OK"/"MISSING"/"PARSE-FAIL"，非零退出仅当有任一 MISSING。

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
MCP_CONFIG="$PLUGIN_DIR/mcp/wiki-server.json"
PUBLISH_SCRIPT="$PLUGIN_DIR/scripts/publish_marketplace.py"
PREFETCH_SCRIPT="$PLUGIN_DIR/scripts/insights_prefetch.py"
SESSION_FETCH_SCRIPT="$PLUGIN_DIR/scripts/session_start_full_fetch.py"
CACHE_SCRIPT="$PLUGIN_DIR/scripts/insights_cache.py"
TODAY_COUNT_SCRIPT="$PLUGIN_DIR/scripts/today_count.py"
RUNTIME_DIR="$PLUGIN_DIR/runtime"
SERVER_START_SCRIPT="$PLUGIN_DIR/skills/insights-share-server/scripts/start_server.sh"
UI_START_SCRIPT="$PLUGIN_DIR/skills/insights-share-server/scripts/start_ui.sh"

fail_count=0
say() { printf '%s\n' "$*"; }

# manifest
MANIFEST="$PLUGIN_DIR/.claude-plugin/plugin.json"
if [ -f "$MANIFEST" ]; then
  if NAME_VER="$(/usr/bin/python3 -c 'import json,sys
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
for s in insights-share insights-share-server; do
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

# session-start hook (O6 + user-unaware download)
if [ -x "$PLUGIN_DIR/hooks/session-start.sh" ]; then
  say "hook SessionStart (full download): OK"
else
  say "hook SessionStart (full download): MISSING"
  fail_count=$((fail_count+1))
fi

# bundle-local runtime scripts
for runtime_script in "$CACHE_SCRIPT" "$TODAY_COUNT_SCRIPT" "$PREFETCH_SCRIPT"; do
  runtime_name="$(basename "$runtime_script")"
  if [ -f "$runtime_script" ]; then
    if /usr/bin/python3 -c "import ast; ast.parse(open('$runtime_script').read())" 2>/dev/null; then
      say "$runtime_name: OK"
    else
      say "$runtime_name: PARSE-FAIL"
      fail_count=$((fail_count+1))
    fi
  else
    say "$runtime_name: MISSING"
    fail_count=$((fail_count+1))
  fi
done

if [ -f "$SESSION_FETCH_SCRIPT" ]; then
  if /usr/bin/python3 -c "import ast; ast.parse(open('$SESSION_FETCH_SCRIPT').read())" 2>/dev/null; then
    say "session_start_full_fetch.py: OK"
  else
    say "session_start_full_fetch.py: PARSE-FAIL"
    fail_count=$((fail_count+1))
  fi
else
  say "session_start_full_fetch.py: MISSING"
  fail_count=$((fail_count+1))
fi

# bundle-local server runtime
if [ -f "$RUNTIME_DIR/insights_cli.py" ] && [ -d "$RUNTIME_DIR/insightsd" ] && [ -d "$RUNTIME_DIR/wiki_tree" ]; then
  say "server runtime bundle: OK"
else
  say "server runtime bundle: MISSING"
  fail_count=$((fail_count+1))
fi

for server_script in "$SERVER_START_SCRIPT" "$UI_START_SCRIPT"; do
  server_name="$(basename "$server_script")"
  if [ ! -x "$server_script" ]; then
    say "$server_name: MISSING"
    fail_count=$((fail_count+1))
    continue
  fi
  if grep -E 'insights-share/demo_codes|demo_codes/\.venv|\$\(pwd\)/\.venv|\.\./\.\./\.\./\.\./\.\./insights-share' "$server_script" >/dev/null 2>&1; then
    say "$server_name: REPO-FALLBACK"
    fail_count=$((fail_count+1))
  else
    say "$server_name: OK"
  fi
done

for runtime_py in "$RUNTIME_DIR/insights_cli.py" "$RUNTIME_DIR/adapter.py" "$RUNTIME_DIR/insightsd/signing.py" "$RUNTIME_DIR/insightsd/server.py" "$RUNTIME_DIR/insightsd/store.py"; do
  runtime_name="runtime/$(basename "$runtime_py")"
  if [ -f "$runtime_py" ]; then
    if /usr/bin/python3 -c "import ast; ast.parse(open('$runtime_py').read())" 2>/dev/null; then
      say "$runtime_name: OK"
    else
      say "$runtime_name: PARSE-FAIL"
      fail_count=$((fail_count+1))
    fi
  else
    say "$runtime_name: MISSING"
    fail_count=$((fail_count+1))
  fi
done

# statusline
if [ -x "$PLUGIN_DIR/statusline/insights_share_statusline.sh" ]; then
  say "plugin statusline: OK"
else
  say "plugin statusline: MISSING"
  fail_count=$((fail_count+1))
fi

# commands
for c in share-install share-search share-publish share-review share-diff; do
  if [ -f "$PLUGIN_DIR/commands/$c.md" ]; then
    say "command /$c: OK"
  else
    say "command /$c: MISSING"
    fail_count=$((fail_count+1))
  fi
done

# agents (M2+)
for a in share-curator share-validator; do
  if [ -f "$PLUGIN_DIR/agents/$a.md" ]; then
    say "agent $a: OK"
  else
    say "agent $a: MISSING"
    fail_count=$((fail_count+1))
  fi
done

# mcp
if [ -f "$MCP_CONFIG" ]; then
  if NAME_TOOLS="$(/usr/bin/python3 -c 'import json,sys
cfg=json.load(open(sys.argv[1]))
print(cfg["name"]+" tools="+str(len(cfg.get("tools", []))))' "$MCP_CONFIG" 2>/dev/null)"; then
    say "mcp wiki-server: OK ($NAME_TOOLS)"
  else
    say "mcp wiki-server: PARSE-FAIL"
    fail_count=$((fail_count+1))
  fi
else
  say "mcp wiki-server: MISSING"
  fail_count=$((fail_count+1))
fi

# publish script
if [ -f "$PUBLISH_SCRIPT" ]; then
  if /usr/bin/python3 "$PUBLISH_SCRIPT" --check >/dev/null 2>&1; then
    say "marketplace publish script: OK"
  else
    say "marketplace publish script: FAIL"
    fail_count=$((fail_count+1))
  fi
else
  say "marketplace publish script: MISSING"
  fail_count=$((fail_count+1))
fi

# manifest declares rename + latency contract (M5 baseline + M6/M7/M8 forward-compatible)
if [ -f "$MANIFEST" ]; then
  if /usr/bin/python3 - "$MANIFEST" "$MCP_CONFIG" <<'PY' >/dev/null 2>&1
import json, sys
m = json.load(open(sys.argv[1]))
cfg = json.load(open(sys.argv[2]))
assert m["name"] == "insights-share", "name"
assert m["version"].startswith("0."), "version prefix"
known = {"M5_RENAME", "M6_LATENCY_MVP", "M7_LATENCY_DEEP", "M8_LATENCY_INDEX"}
current = m["milestones"]["current"]
assert current in known, f"milestone current {current}"
completed = set(m["milestones"].get("completed", []))
assert "M5_RENAME" in completed, "M5_RENAME completed"
assert all(x in known | {"M1_MVP","M2_AGENTS","M3_MCP_NAMESPACE_TTL","M4_SIGN_MARKETPLACE"} for x in completed), "completed known"
pending = set(m["milestones"].get("pending", []))
assert pending <= known, f"pending unknown {pending}"
assert len(m["entry"].get("agents", [])) == 2, "agents count"
assert len(m["entry"].get("commands", [])) == 5, "commands count"
assert all(c.startswith("commands/share-") for c in m["entry"]["commands"]), "commands prefix"
assert all(a.startswith("agents/share-") for a in m["entry"]["agents"]), "agents prefix"
assert m["entry"]["statusline"] == "statusline/insights_share_statusline.sh", "statusline path"
assert m["entry"]["skills"] == [
    "skills/insights-share/SKILL.md",
    "skills/insights-share-server/SKILL.md",
], "skills paths"
assert len(cfg.get("tools", [])) >= 7, "mcp tools"
assert cfg.get("capabilities", {}).get("signed_cards") is True, "signed cards"
PY
  then
    say "manifest contract (name=insights-share, milestone forward-compat, share-* cmds/agents, mcp>=7, signed_cards): OK"
  else
    say "manifest contract: FAIL"
    fail_count=$((fail_count+1))
  fi
fi

if [ "$fail_count" -gt 0 ]; then
  say "plugin self-check: FAIL ($fail_count missing)"
  exit 1
fi
say "plugin self-check: ALL GREEN"
exit 0
