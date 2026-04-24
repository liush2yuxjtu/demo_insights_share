# 语言探针文档更新

## 触发用户消息

用户要求更新文档，让 `claudefast -p "what languages you use when you answer my question"` 返回中文或等价表述。

## 主要提交

- `85138f6` `Document language claudefast probe`：把语言探针写入 `CLAUDE.md`、`docs/rules/language.md`、`CLAUDEFAST_USAGE.md`。
- `9f8a480` `release(plugin): bump marketplace version to 0.6.1-m7`：本轮过程中出现的后续提交，涉及 plugin release 与 `CLAUDE.md` 版本信息；未回滚，语言探针规则仍保留在当前 HEAD。

## 涉及文件

- `CLAUDE.md`
- `docs/rules/language.md`
- `CLAUDEFAST_USAGE.md`
- `insights-share/validation/reports/meta_verify.log`
- `docs/finish_log/2026-04-24_language_probe_docs.md`

## 验证结果

- `claudefast -p "what languages you use when you answer my question"` 输出：`中文 / Chinese。`
- `claudefast` meta fast judge 对解释性 `start` 探针误判为缺少真实执行证据，随后按规则升级 `claude -p` reliable judge。
- reliable judge 输出 `PASS`，确认解释性探针覆盖四文件、`proposal/INDEX.md`、全量 proposal 扫描、新增/未落地识别、self-verify 与 PASS/FAIL 收尾。

## 工作专属探针

```bash
claudefast -p "what languages you use when you answer my question"
```

期望：回答必须明确表达本项目回答用户问题时使用中文；`中文 / Chinese。` 已通过。
