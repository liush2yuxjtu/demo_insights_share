# 2026-04-22 READ ONLY snapshot

## 探针结果

```
READ ONLY, tell me what we have done in recent commits and based on docs
```

## 近期完成事项

### M6/M7 LATENCY 闭环
- M6 MVP PASS（cache-hit ~1ms）
- M7 DEEP PARTIAL（cache-miss p95=12314ms 超 6000ms budget）
- O2 layer-skip hint 已落地，max_turns=5 恢复
- O4 并行 search+adapter 在 stop hook
- O6 SessionStart prefetch hook 注册

### 发布流程
- `4366506` release(plugin): bump plugin.json to 0.6.0-m7
- `a85e416` release(marketplace): bump root marketplace to 0.6.0-m7
- `e96f4d1` docs(plugin): document dual-repo split (dev 46M vs plugin-only 108K)

### finish-flag-claudefast 规则
- 新增 `docs/rules/finish-flag-claudefast.md`
- `CLAUDE.md` 新增索引行
- 自洽验证 PASS

### upload 基础设施
- `extract_lessons.py` — jsonl→wiki card with topic infer + dedup
- `upload_lessons.sh` — staging→daemon mapper + uploader
- macOS compat fix（curl args quoting, mktemp 替代 head -n-1）
- G1–G5 kanban gate 全 PASS

## 进行中
- M8 候选：O7 embedding 预索引 / 模型切换 / fan-out 并行（攻 cache-miss 瓶颈）
- 3740 jsonl 待扫描（本次只处理 10 个）
