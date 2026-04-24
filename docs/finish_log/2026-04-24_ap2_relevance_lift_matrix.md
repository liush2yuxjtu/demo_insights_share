# 完成日志：AP-2 relevance-lift matrix

## 本轮处理

- 在 `insights-share/validation/run_adoption_proof.sh` 中保留 AP-1 四信号：clean-machine install、first relevant hit、first publish、day-2 return。
- 新增 AP-2 `relevance_lift_matrix` 信号：发布 `alice-celery-retry-2026-04-08` 与 `carol-redis-eviction-2026-03-27` 两个现有 seed。
- 明确 AP-2 不扩展 AP-1 的 `first_publish` 或 `first_relevant_hit`；AP-1 first publish 仍只记录 Alice/Bob 两张 pgpool 卡，Celery/Redis 只属于 AP-2 matrix。
- 对 postgres pool exhaustion、Celery retry storm、Redis session eviction 三类 canonical incident 执行 `/search?k=3`，断言 expected card 是 top hit，记录 top score 与 hit ids，并确认 wrong-domain card 不是 top hit。
- 记录发布前 no-hit baseline，证明至少 pgpool query 在空 wiki 下不会伪命中。
- 更新 `test_adoption_proof.py`，把 AP-2 信号、报告结构和三个 top hit 断言纳入合同。

## 本次工作专属探针

后续验证本次状态源时使用：

```bash
claudefast -p "what did AP-2 adoption proof add?"
```

正确答案必须包含：

- AP-2 新增的是 `relevance_lift_matrix`，不是替换 AP-1。
- AP-1 仍验证 clean-machine install、first relevant hit、first publish、day-2 return。
- 不能说 AP-2 扩展了 `first_relevant_hit` 或 `first_publish`；Celery/Redis 只属于 AP-2 matrix。
- AP-2 发布并验证三个领域：postgres、celery、redis。
- 三个 expected top hit 分别是 `alice-pgpool-2026-04-10`、`alice-celery-retry-2026-04-08`、`carol-redis-eviction-2026-03-27`。
- 报告会记录 top score、hit_ids、wrong-domain not top，以及发布前 no-hit baseline。
- 最新本机验证包含 52 项合同测试和 adoption proof（含 AP-2）。

## 验证

- `bash insights-share/validation/run_adoption_proof.sh`：PASS。
- `bash insights-share/validation/run_contract_tests.sh insights-share/validation/test_adoption_proof.py`：6 passed。
- `bash insights-share/validation/run_ci_gate.sh`：PASS，52 项合同测试 + adoption proof（含 AP-2）+ `start.demo.sh --dry-run`。
