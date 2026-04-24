---
{
  "id": "m1-kb-ah-047",
  "title": "2. Error Patterns & Fixes",
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
  "label_note": "\n### pyenv 初始化死循环\n- **问题**: `python3` 触发 `_pyenv_lazy_init` 无限循环\n- **原因**: pyenv hook 递归\n- **修复**: 使用绝对路径 `/opt/homebrew/bin/python3` 或 `/usr/bin/python3`\n\n### PEP 668 pip 限制\n- **问题**: `pip install pytest` 失败 \"externally-managed-environment\"\n- **修复**: 改用 `unittest`（`python3 -m unittest discover`）替代 pytest\n\n### 相对路径 cwd 问题\n- **问题**: 插件运行时的 cwd 与预期不同，导致 evidence 文件路径错误\n- **修复**: 使用绝对路径或在子 shell 中运行并 cd 回正确目录\n\n### Screen Recording 权限缺失\n- **问题**: `could not create image from display`\n- **修复**: macOS",
  "applies_when": [],
  "do_not_apply_when": []
}
---

# 2. Error Patterns & Fixes

> author: m1 · confidence: 0.85


### pyenv 初始化死循环
- **问题**: `python3` 触发 `_pyenv_lazy_init` 无限循环
- **原因**: pyenv hook 递归
- **修复**: 使用绝对路径 `/opt/homebrew/bin/python3` 或 `/usr/bin/python3`

### PEP 668 pip 限制
- **问题**: `pip install pytest` 失败 "externally-managed-environment"
- **修复**: 改用 `unittest`（`python3 -m unittest discover`）替代 pytest

### 相对路径 cwd 问题
- **问题**: 插件运行时的 cwd 与预期不同，导致 evidence 文件路径错误
- **修复**: 使用绝对路径或在子 shell 中运行并 cd 回正确目录

### Screen Recording 权限缺失
- **问题**: `could not create image from display`
- **修复**: macOS
