---
{
  "id": "m1-sandbox-home-2026-04-22",
  "title": "沙箱脚本必须 export HOME=$SANDBOX_HOME",
  "author": "m1",
  "confidence": 0.95,
  "tags": ["sandbox", "HOME", "symlink", "security", "沙箱"],
  "status": "active",
  "applies_when": ["沙箱脚本自称 sandbox", "任何涉及 $HOME 读写的脚本"],
  "do_not_apply_when": ["真实宿主环境（非沙箱）", "明确知道不会污染 ~/.claude 的工具"],
  "topic_id": "security-patterns",
  "label": "good",
  "label_note": "真沙箱必须 export HOME=$SANDBOX_HOME，禁止 symlink 污染真实 ~/.claude",
  "raw_log": null
}
---

# 沙箱脚本必须 export HOME=$SANDBOX_HOME

> author: m1 · confidence: 0.95

## 根因

沙箱脚本若不设置 `HOME=$SANDBOX_HOME`，`~/.claude` 里的配置文件、hooks、memory 会被真实宿主污染。symlink 也可能干扰真实 session 状态。

## Good example

```bash
export HOME="$SANDBOX_HOME"
# 之后所有 ~/.foo 都指向 SANDBOX_HOME 而非真实 HOME
```

## Bad example

```bash
# ❌ 不设 HOME，~/.claude 被污染
./sandbox_script.sh    # 写入 ~/.claude/settings.json
```

## 真实案例

沙箱内运行 `./bootstrap.sh` 后，真实 `~/.claude/settings.json` 被覆盖，导致 claude 命令行为异常。

## 自检

```bash
echo "$HOME"    # 沙箱内应是 SANDBOX_HOME，非 /Users/m1
```

## Applies when

- 沙箱脚本自称 sandbox
- 任何涉及 $HOME 读写的脚本

## Do NOT apply when

- 真实宿主环境（非沙箱）
- 明确知道不会污染 ~/.claude 的工具
