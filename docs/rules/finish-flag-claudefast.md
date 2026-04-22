# 完工 finish flag — claudefast READ ONLY probe

## 触发
任何 job (feature / fix / refactor / chore) 自认完成的最后一步。**不限于** CLAUDE.md 编辑。

## 强制顺序
1. **写 docs**: 把本次 job 的结果落到 `docs/finish_log/<YYYY-MM-DD>_<slug>.md`，包含:
   - 触发用户消息（一句话摘要）
   - 主要 commit hash 列表（`git log --oneline <since>`）
   - 涉及文件
   - 执行结果（PASS gates / 失败点 / 后续）
2. **跑 finish flag probe** (READ ONLY，禁写、禁工具改动):
   ```bash
   claudefast -p "READ ONLY, tell me what we have done in recent commits and based on docs. \
   Reply JSON: {\"verdict\":\"PASS|REFINE|FAIL\", \"recent_commits\":[hashes], \
   \"docs_referenced\":[paths], \"summary\":\"<≤120字>\", \"missing_or_inconsistent\":[]}"
   ```
3. **判定**:
   - `PASS` → 工作完成
   - `REFINE` / `FAIL` → 按 `missing_or_inconsistent` 修 docs（或修代码再补 docs）, **回到 step 1 重写日志，重跑 step 2**
4. **轮次上限**: fast 模式最多 3 轮；连续 REFINE 升级 `claude -p` 托底

## 写法约束
- `docs/finish_log/` 是 append-only 目录, 同一文件名不覆盖, 必要时加 `_v2.md`
- finish probe 不传 `@` 大文件附件, 让 claudefast 自己 git log + ls docs/
- 命令必须包含字面量 "READ ONLY"，禁授予 Bash/Edit 写权限
- finish flag PASS 后才允许向用户回报"完成"

## 与 meta-self-verify 区别
| 规则 | 触发 | 探针目标 | probe 内容 |
|------|------|---------|------------|
| meta-self-verify | CLAUDE.md 编辑 | 验规则被 CLI reasoning 路径理解 | 探规则触发是否生效 |
| finish-flag-claudefast (本规则) | **任意 job 完成** | 验 commit + docs 一致 | 复述 recent commits 是否对得上 docs |

两规则可叠加：CLAUDE.md 改动既走 meta-self-verify 也走 finish flag。

## 失败回滚
- finish probe FAIL 不回滚已 commit 的代码（避免破坏历史），改 docs 补全
- docs 写错可 amend 同一 finish_log md（同 job 同文件）
- 仍 FAIL → user-visible 标 BLOCKED，不报"完成"
