---
{
  "id": "m1-kb-ah-048",
  "title": "3. CLI Commands & Tools",
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
  "label_note": "\n### OpenClaw CLI\n```bash\nopenclaw plugins install -l <path>    # 本地软链安装\nopenclaw plugins inspect <plugin> --json\nopenclaw gateway --port <port>         # 启动网关\nopenclaw config set <key> <value>      # 修改配置\nopenclaw doctor                        # 诊断\nopenclaw status                        # 状态检查\n```\n\n### Plugin Development\n```bash\n# Python 运行\npython3 -c 'from main import plugin; plugin.run_once()'\n/opt/homebrew/bin/python3 -m unittest discover -s tests -q\n\n# NDJSON bridge 测试\necho '{\"cmd\":\"status\"",
  "applies_when": [],
  "do_not_apply_when": []
}
---

# 3. CLI Commands & Tools

> author: m1 · confidence: 0.85


### OpenClaw CLI
```bash
openclaw plugins install -l <path>    # 本地软链安装
openclaw plugins inspect <plugin> --json
openclaw gateway --port <port>         # 启动网关
openclaw config set <key> <value>      # 修改配置
openclaw doctor                        # 诊断
openclaw status                        # 状态检查
```

### Plugin Development
```bash
# Python 运行
python3 -c 'from main import plugin; plugin.run_once()'
/opt/homebrew/bin/python3 -m unittest discover -s tests -q

# NDJSON bridge 测试
echo '{"cmd":"status"
