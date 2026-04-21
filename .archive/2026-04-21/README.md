# Archive 2026-04-21

Lightspeed cleanup 归档。原文件路径按镜像保留，随 commit 历史可查。

## 回滚

- 单文件：`git mv .archive/2026-04-21/<path> <original_path>`
- 全量：`bash .archive/2026-04-21/REVERT.sh`

## 分级

- manifest-tier1.txt — 零风险类（pycache / bak / 空壳 / 临时 dump）
- manifest-tier2.txt — 验引用类（逐条 grep 后归档）
- manifest-tier3.txt — 构建/依赖类（仅 validation/artifacts 非 latest 部分）

## 上游计划

`.claude/plans/lightspeed_archive_cleanup_2026-04-21.md`
