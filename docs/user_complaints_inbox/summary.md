# inbox_loop run summary

- verdict_tag: **shipped**
- iters_used: 1
- final_artifact: docs/user_complaints_inbox/final_artifact.md
- pending proposals (from user_complaints_inbox): 16
- autofix count: 0
- exit_reason: normal
- ts: 2026-04-21T21:30:13

## final ship verdict (free text from judge)

```text
**结论: NOT ship-ready. 4 个 concrete bugs 未修复:**

| Bug | 位置 | 严重度 | 状态 |
|-----|------|--------|------|
| `summon` 无 fallback，文件不存在时命令失败 | 第6行 | 高 | 未修 |
| `~/.cache/insights-share/manifest.json` 路径无 proposal 背书，纯捏造 | 第17行 | 高 | 未修 |
| stale 识别无操作化定义，AI 可能误引用过期卡 | 第31行约束 | 高 | 未修 |
| `/share-diff` topic 选取策略缺失，多卡时 PM 不知道选谁先 diff | 第16行 | 中 | 未修 |

**次要问题:**
- `[share 🔒 sig-fail]` UI notation 在任何 design doc 无定义，prompt 自己在第31行引用了
- STAR 的 R 段"三维量化"无格式模板，AI 自由发挥空间太大

**修复要求:**

1. 第6行 summon 加 `|| { echo "ERROR: prompt_pm.md not found"; exit 1; }` 或改用绝对路径
2. 第17行 manifest.json 路径改为动态发现（如 `find ~/.config ~/.cache -name manifest.json 2>/dev/null | head -1`）并说明读哪个字段
3. 第31行硬约束加 stale 识别规则：如 "卡片 age > 90 天或带 stale 徽章视为过期"
4. 第16行之前加 topic 选取步骤：列出命中 topic，说明相关性，再进 diff
```