---
{
  "id": "m1-kb-ah-039",
  "title": "Error Fixes",
  "author": "m1",
  "confidence": 0.85,
  "tags": [
    "knowledge-extraction",
    "session-analysis",
    "group_ah"
  ],
  "status": "active",
  "topic_id": "m1-kb-ah",
  "label": "good",
  "label_note": "\n### v1 证据造假根因\n`screenshot_taker.py` 失败路径把错误文本写入 `.png`：\n```python\nexcept Exception as e:\n    with open(filepath, 'w') as f:\n        f.write(f\"[ERROR] Screenshot failed: {e}\")\n```\n修复：失败时 `raise`，不写文件。\n\n### Shell 转义陷阱\n- `\\\\.png` 在单引号内被 bash 原样保留，grep 搜索字面 `\\` 字符导致 0 匹配\n- 修复：`\\.png`（单反斜杠）\n- `python` vs `python3`：sensor 命令需与运行环境匹配\n\n### pyenv lazy-init 循环\nzsh 非交互 shell 下 `pyenv init -` 有问题。用绝对路径 `python3` 或 `node`/`jq` 代替 Python 探针。\n\n### nullglob 下 ls 空展开\n```bash\nspecs=($(ls -t ./validation/v*_*.md ",
  "applies_when": [],
  "do_not_apply_when": []
}
---

# Error Fixes

> author: m1 · confidence: 0.85


### v1 证据造假根因
`screenshot_taker.py` 失败路径把错误文本写入 `.png`：
```python
except Exception as e:
    with open(filepath, 'w') as f:
        f.write(f"[ERROR] Screenshot failed: {e}")
```
修复：失败时 `raise`，不写文件。

### Shell 转义陷阱
- `\\.png` 在单引号内被 bash 原样保留，grep 搜索字面 `\` 字符导致 0 匹配
- 修复：`\.png`（单反斜杠）
- `python` vs `python3`：sensor 命令需与运行环境匹配

### pyenv lazy-init 循环
zsh 非交互 shell 下 `pyenv init -` 有问题。用绝对路径 `python3` 或 `node`/`jq` 代替 Python 探针。

### nullglob 下 ls 空展开
```bash
specs=($(ls -t ./validation/v*_*.md
