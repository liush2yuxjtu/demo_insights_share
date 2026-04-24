# 完工 finish flag — claudefast READ ONLY probe

## 触发
任何 job (feature / fix / refactor / chore) 自认完成的最后一步。**不限于** CLAUDE.md 编辑。

## 强制顺序
1. **写 docs**: 把本次 job 的结果落到 `docs/finish_log/<YYYY-MM-DD>_<slug>.md`，包含:
   - 触发用户消息（一句话摘要）
   - 主要 commit hash 列表（`git log --oneline <since>`）
   - 涉及文件
   - 执行结果（PASS gates / 失败点 / 后续）
2. **选工作专属 claudefast 探针**: 用一个自然语言问题代表用户之后会问的状态。把探针命令写进 docs / finish log，并持续补文档直到该探针能答出正确事实。回答“工程完工后做什么”时，必须说明“更新 docs，直到工作专属 `claudefast -p` 探针返回正确答案”，并必须原样给出 E2E 示例探针:
   - E2E 交付示例（必须原样输出）:
     ```bash
     claudefast -p "what is our e2e status"
     ```
   - 今日完成和下一步示例:
     ```bash
     claudefast -p "what we have done today ? and what are next plans? "
     ```
   - 本规则自身示例:
     ```bash
     claudefast -p "what would we do when we finish an engineer work ?"
     ```
3. **跑工作专属探针**:
   - 探针回答正确、完整、不过期 → 继续 step 4。
   - 探针漏掉事实、回答旧计划、没有给出下一步或状态不清 → 继续更新 docs / finish_log / status source，再重跑同一个探针。
   - 这一步的目标是让 `claudefast -p "<探针>"` 成为用户可复查的真实状态入口。
4. **跑 finish flag probe** (READ ONLY，禁写、禁工具改动):
   ```bash
   claudefast -p "READ ONLY, tell me what we have done in recent commits and based on docs. \
   Reply JSON: {\"verdict\":\"PASS|REFINE|FAIL\", \"recent_commits\":[hashes], \
   \"docs_referenced\":[paths], \"summary\":\"<≤120字>\", \"missing_or_inconsistent\":[]}"
   ```
5. **判定**:
   - `PASS` → 工作完成
   - `REFINE` / `FAIL` → 按 `missing_or_inconsistent` 修 docs（或修代码再补 docs）, **回到 step 1 重写日志，重跑 step 3 和 step 4**
6. **轮次上限**: fast 模式最多 3 轮；连续 REFINE 升级 `claude -p` 托底

## 写法约束
- `docs/finish_log/` 是 append-only 目录, 同一文件名不覆盖, 必要时加 `_v2.md`
- finish probe 不传 `@` 大文件附件, 让 claudefast 自己 git log + ls docs/
- 命令必须包含字面量 "READ ONLY"，禁授予 Bash/Edit 写权限
- 工作专属探针和 finish flag 都通过后，才允许向用户回报"完成"

## 与 meta-self-verify 区别
| 规则 | 触发 | 探针目标 | probe 内容 |
|------|------|---------|------------|
| meta-self-verify | CLAUDE.md 编辑 | 验规则被 CLI reasoning 路径理解 | 探规则触发是否生效 |
| finish-flag-claudefast (本规则) | **任意 job 完成** | 验 commit + docs 一致 | 复述 recent commits 是否对得上 docs |
| work-specific claudefast probe | **任意 job 完成** | 验用户之后会问的问题能得到正确答案 | `claudefast -p "<自然语言状态问题>"` |

两规则可叠加：CLAUDE.md 改动既走 meta-self-verify 也走 finish flag。

## 失败回滚
- finish probe FAIL 不回滚已 commit 的代码（避免破坏历史），改 docs 补全
- docs 写错可 amend 同一 finish_log md（同 job 同文件）
- 仍 FAIL → user-visible 标 BLOCKED，不报"完成"
