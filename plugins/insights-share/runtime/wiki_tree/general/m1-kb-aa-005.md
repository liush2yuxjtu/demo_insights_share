---
{
  "id": "m1-kb-aa-005",
  "title": "5. Claude Code CLI 命令约定",
  "author": "m1",
  "confidence": 0.85,
  "tags": [
    "knowledge-extraction",
    "session-analysis",
    "group_aa"
  ],
  "status": "active",
  "topic_id": "m1-kb-aa",
  "label": "good",
  "label_note": "\n### Shell 命令前缀\n- `!pwd` / `!ls -la` — 带有 `!` 前缀时表示执行 shell 命令\n\n### /export 命令\n- 将当前会话导出到指定 `.md` 文件：`/export <path>`\n\n### Session 结束\n- 输出 `Bye!` 表示会话正常结束\n\n### Permission Modes\n- `default` — 默认权限\n- `bypassPermissions` — 绕过权限限制\n\n### Entrypoints\n- `cli` — 标准命令行\n- `sdk-cli` — SDK CLI\n- `sdk-py` — Python SDK\n\n---",
  "applies_when": [],
  "do_not_apply_when": []
}
---

# 5. Claude Code CLI 命令约定

> author: m1 · confidence: 0.85


### Shell 命令前缀
- `!pwd` / `!ls -la` — 带有 `!` 前缀时表示执行 shell 命令

### /export 命令
- 将当前会话导出到指定 `.md` 文件：`/export <path>`

### Session 结束
- 输出 `Bye!` 表示会话正常结束

### Permission Modes
- `default` — 默认权限
- `bypassPermissions` — 绕过权限限制

### Entrypoints
- `cli` — 标准命令行
- `sdk-cli` — SDK CLI
- `sdk-py` — Python SDK

---
