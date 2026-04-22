# 2026-04-22 — jsonl 教训抽取上传 + finish-flag-claudefast 规则

## 触发
两条用户请求合并落地:
1. "scan 本地 ~/.claude/projects/**/*.jsonl 抽 lesson → 上传 insights-share"，loop self-verify by editing upload_plan.md
2. "add RULES: every job finish 写 docs + 跑 claudefast READ ONLY 当 finish flag"

## 主要 commit
- `27b1faf` feat(rules): 加 finish-flag-claudefast 行进 CLAUDE.md 索引
- `51e2c9e` docs(rules): finish-flag-claudefast.md 详细规约
- `d1c92ee` fix(upload): macOS compat (quote curl args, mktemp 代替 head -n-1)
- `73094c0` feat(scripts): upload_lessons.sh — staging→daemon mapper + uploader
- `87775d6` fix(plan): dynamic topic_id from staging dirs + absolute daemon path
- `406822a` fix(plan): daemon 真 schema + mapper + topic pre-register
- `f35c6e0` fix(plan): + daemon precondition + Clash proxy bypass + API 表
- `5b45e72` feat(scripts): extract_lessons.py — jsonl→wiki card with topic infer + dedup
- `1306d3f` feat: 初版 upload_plan.md

## 涉及文件
- 新增: `upload_plan.md`, `scripts/extract_lessons.py`, `scripts/upload_lessons.sh`,
  `docs/rules/finish-flag-claudefast.md`, `docs/finish_log/2026-04-22_jsonl-upload-and-finish-flag-rule.md`
- 修改: `CLAUDE.md` (+1 行规则)

## 执行结果
| Gate | 状态 | 证据 |
|------|------|------|
| G1 plan judge probe | PASS (R1-R2) / REFINE (R3-R4 → 转执行) | claudefast -p JSON verdict |
| G2 dry-run | PASS | 5 cards in /tmp/insights_upload_staging/ (3 topics) |
| G3 schema | PASS | 5/5 JSON parse OK |
| G4 上传 | PASS | 5/5 HTTP 200 |
| G5 kanban gate | PASS | curl /topics 列出 auto-{database,infra_cache,tooling}, ed25519 verified |
| meta-self-verify (新规则) | PASS | probe + judge JSON: covers=[true,true,true] |

## 后续
- 本次只扫 10 个 jsonl, 全 3740 待跑
- topic infer 规则 ("database" 误命中) 待改进
- finish-flag-claudefast 自洽性: 本 finish_log 即应用新规则的第一份证据

## finish flag probe (本 job 自验)
见同目录后续 commit 输出 / 终端日志。
