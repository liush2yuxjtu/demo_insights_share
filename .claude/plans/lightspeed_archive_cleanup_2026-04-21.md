# Lightspeed Archive Cleanup Plan

> 日期：2026-04-21
> 作者：agent（caveman 模式产出）
> 目标：以最快速度把非必要文件归档（非删除），保留回退能力
> 门禁：`start.demo.sh` 全绿 + A/B prompt-equality PASS + 触发率不降

---

## 1. 核心原则

| 原则 | 落地 |
|------|------|
| **归档不删** | `git mv` 到 `.archive/2026-04-21/<mirror_path>/`，保留 git 历史可 revert |
| **原子 commit** | 每 tier 单独 commit，按单一关注点；不合并 |
| **先盘点再动** | 每步输出盘点 manifest 到 `.archive/2026-04-21/manifest-<tier>.txt` |
| **门禁回归** | 每 commit 后跑 `start.demo.sh` self-verify，破绿立即 revert |
| **根 md 只读** | `proposal.md` / `README.md` / `validation.md` / `validation_AB.md` 整段禁动 |
| **user_design 只读** | `docs/designs/user_design/` 整段禁动 |

---

## 2. 归档目录结构

```
.archive/
└── 2026-04-21/
    ├── README.md                  # 本次归档索引 + 回滚命令
    ├── manifest-tier1.txt         # Tier 1 文件清单（归档前 find 输出）
    ├── manifest-tier2.txt         # Tier 2
    ├── manifest-tier3.txt         # Tier 3
    ├── <mirror of original paths> # git mv 后的镜像路径
    └── REVERT.sh                  # 一键回滚脚本
```

`.archive/` 加入 `.gitignore` 的**反例**（即：归档内容入仓，后续才 tombstone）。

---

## 3. 分级清单（承接先前研判）

### Tier 0 — 禁动（不在本计划范围）

详见研判稿，略。

### Tier 1 — 零风险归档（pycache / bak / 空壳 / 临时 dump）

| 路径 | 体积 | 理由 |
|------|------|------|
| `AGENTS.md` | 0B | 空文件，被 CLAUDE.md 取代 |
| `2026-04-15-173013-command-messagedeep-researchcommand-message.txt` | 8K | 旧 command 原始 dump |
| `insights-share/demo_codes/__pycache__/` | 124K | Python bytecode |
| `insights-share/validation/__pycache__/` | 404K | Python bytecode |
| `insights-share/wiki_daemon/__pycache__/` | untracked | Python bytecode |
| `insights-share/demo_codes/.claude/settings.json.bak-0414` | <4K | 2 周前备份，git 已是版本系统 |

**累计**：≈550K。

### Tier 2 — 验引用后归档（需 grep 验证无活引用）

| 路径 | 体积 | 验证命令 |
|------|------|----------|
| `insights-share/demo_codes/wiki.json` | 4K | `grep -rn "wiki\.json" insights-share/ plugins/ --include="*.py" --include="*.sh"` 只命中 `insights_cli.py` → 确认 CLI 是否走 tree 模式 |
| `insights-share/demo_codes/runtime/sessions/` | 20K | `grep -rn "runtime/sessions" insights-share/ plugins/` |
| `insights-share/demo_codes/runtime-live/sessions/` | 20K | 同上 |
| `insights-share/demo_codes/runtime-smoke/sessions/` | 8K | 同上 |
| `insights-share/demo_codes/runtime-web/sessions/` | 196K | 同上 |
| `insights-share/demo_codes/standalone_runtime_preview.html` | 36K | `grep -rn "standalone_runtime_preview" . --include="*.sh" --include="*.md"` |
| `save_plan_in_project.txt` | 12K | `grep -rn "save_plan_in_project" .` |
| `report.zh.html` | 60K | `grep -rn "report\.zh\.html" .` |
| `minimax_work/need_review/` | 8K | 人工审 |
| `insights-share/plan.md` | 16K | 与 `proposal/*.md` diff；若全被取代，归档 |

**累计**：≈380K（含 `plan.md` 则 ≈396K）。

### Tier 3 — 依赖/构建类（`.gitignore` 吸 + 可选归档）

| 路径 | 体积 | 策略 |
|------|------|------|
| `insights-share/validation/node_modules/` | 14M | `.gitignore` 加入，`git rm -r --cached`；不归档（可重装） |
| `insights-share/validation/artifacts/` | 26M | 保留 `latest/` 软链，其他归档至 `.archive/2026-04-21/validation-artifacts/<timestamp>/` |
| `insights-share/dist/insights-share-v1.0.0.*` | 176K | 保留；旧版本后续随 tag 归档 |
| `.claude/worktrees/minimax0416_dev/` | 16M | `git worktree list` 验状态；若 dead → `git worktree remove`；不归档 |

**累计**：节省 ≈30M+16M=46M；归档部分仅 artifacts 非 latest 部分。

---

## 4. 执行步骤（4 个原子 commit）

### Commit 0 — 初始化归档骨架

```bash
ARCHIVE_ROOT=".archive/2026-04-21"
mkdir -p "$ARCHIVE_ROOT"

cat > "$ARCHIVE_ROOT/README.md" <<'EOF'
# Archive 2026-04-21

Lightspeed cleanup 归档。原文件路径按镜像保留，随 commit 历史可查。

## 回滚

- 单文件：`git mv .archive/2026-04-21/<path> <original_path>`
- 全量：`bash .archive/2026-04-21/REVERT.sh`

## 分级

- manifest-tier1.txt — 零风险类
- manifest-tier2.txt — 验引用类
- manifest-tier3.txt — 构建/依赖类（仅 validation/artifacts 非 latest 部分）
EOF

cat > "$ARCHIVE_ROOT/REVERT.sh" <<'EOF'
#!/bin/bash
# 一键回滚本次归档
set -euo pipefail
ARCHIVE="$(cd "$(dirname "$0")" && pwd)"
cd "$(git rev-parse --show-toplevel)"
while IFS= read -r line; do
  [ -z "$line" ] && continue
  src=".archive/2026-04-21/$line"
  [ -e "$src" ] || continue
  mkdir -p "$(dirname "$line")"
  git mv "$src" "$line"
done < "$ARCHIVE/manifest-tier1.txt"
# tier2 / tier3 同理
echo "Revert done. Run start.demo.sh to verify."
EOF
chmod +x "$ARCHIVE_ROOT/REVERT.sh"

git add "$ARCHIVE_ROOT"
git commit -m "chore(archive): init lightspeed cleanup archive 2026-04-21"
```

### Commit 1 — Tier 1 归档（零风险，立即）

```bash
ARCHIVE_ROOT=".archive/2026-04-21"

# 盘点 manifest
{
  echo "AGENTS.md"
  echo "2026-04-15-173013-command-messagedeep-researchcommand-message.txt"
  find insights-share/demo_codes/__pycache__ insights-share/validation/__pycache__ -type f 2>/dev/null
  [ -f insights-share/demo_codes/.claude/settings.json.bak-0414 ] && echo "insights-share/demo_codes/.claude/settings.json.bak-0414"
} > "$ARCHIVE_ROOT/manifest-tier1.txt"

# 镜像归档
while IFS= read -r f; do
  [ -z "$f" ] && continue
  dst="$ARCHIVE_ROOT/$f"
  mkdir -p "$(dirname "$dst")"
  if git ls-files --error-unmatch "$f" >/dev/null 2>&1; then
    git mv "$f" "$dst"
  else
    mv "$f" "$dst"
    git add "$dst"
  fi
done < "$ARCHIVE_ROOT/manifest-tier1.txt"

# .gitignore 防再生
cat >> .gitignore <<'EOF'

# Python bytecode
__pycache__/
*.pyc
*.pyo

# editor/tool backups
*.bak-*
*.swp
EOF

git add .gitignore "$ARCHIVE_ROOT"
git commit -m "chore(archive): tier-1 archive pycache, bak, empty stubs, stale dumps"

# 门禁
bash start.demo.sh   # 必须 ALL GREEN
```

### Commit 2 — Tier 2 归档（逐条验引用）

对每个候选文件：

```bash
ARCHIVE_ROOT=".archive/2026-04-21"
: > "$ARCHIVE_ROOT/manifest-tier2.txt"

candidates=(
  "insights-share/demo_codes/wiki.json"
  "insights-share/demo_codes/runtime/sessions"
  "insights-share/demo_codes/runtime-live/sessions"
  "insights-share/demo_codes/runtime-smoke/sessions"
  "insights-share/demo_codes/runtime-web/sessions"
  "insights-share/demo_codes/standalone_runtime_preview.html"
  "save_plan_in_project.txt"
  "report.zh.html"
  "minimax_work/need_review"
  "insights-share/plan.md"
)

for c in "${candidates[@]}"; do
  name="$(basename "$c")"
  hits=$(grep -rn --exclude-dir=.git --exclude-dir=.archive --exclude-dir=node_modules \
    -- "$name" . 2>/dev/null \
    | grep -v "^\./$c" \
    | grep -v "^\./\.archive" \
    | grep -v "^\./\.claude/plans/lightspeed_archive_cleanup" || true)
  if [ -z "$hits" ]; then
    echo "$c" >> "$ARCHIVE_ROOT/manifest-tier2.txt"
  else
    echo "[SKIP] $c 有活引用：" >&2
    printf '%s\n' "$hits" >&2
  fi
done

# 逐条归档 + 逐条 commit（原子）
while IFS= read -r f; do
  [ -z "$f" ] && continue
  dst="$ARCHIVE_ROOT/$f"
  mkdir -p "$(dirname "$dst")"
  git mv "$f" "$dst"
  git commit -m "chore(archive): tier-2 archive $f (no active references)"
  bash start.demo.sh || { git revert HEAD; echo "门禁破绿，已 revert"; exit 1; }
done < "$ARCHIVE_ROOT/manifest-tier2.txt"
```

### Commit 3 — Tier 3 `.gitignore` + artifacts 轮转

```bash
ARCHIVE_ROOT=".archive/2026-04-21"

# 3a) node_modules 出仓
cat >> .gitignore <<'EOF'

# validation deps (playwright 等)
insights-share/validation/node_modules/
EOF
git rm -r --cached insights-share/validation/node_modules 2>/dev/null || true
git add .gitignore
git commit -m "chore(archive): tier-3a untrack node_modules via gitignore"

# 3b) artifacts 只留 latest，其他归档
ART_DIR="insights-share/validation/artifacts"
mkdir -p "$ARCHIVE_ROOT/$ART_DIR"
LATEST="$(ls -1t "$ART_DIR" 2>/dev/null | head -1)"
: > "$ARCHIVE_ROOT/manifest-tier3.txt"
for d in "$ART_DIR"/*; do
  [ -d "$d" ] || continue
  bn="$(basename "$d")"
  [ "$bn" = "$LATEST" ] && continue
  echo "$d" >> "$ARCHIVE_ROOT/manifest-tier3.txt"
  git mv "$d" "$ARCHIVE_ROOT/$ART_DIR/$bn"
done
git add "$ARCHIVE_ROOT"
git commit -m "chore(archive): tier-3b rotate validation artifacts (keep latest only)"

# 3c) worktree prune（不归档，git 原生清理）
git worktree list
# 确认 .claude/worktrees/minimax0416_dev 未在跑 → 手动 git worktree remove
# 留给人工决策，不在 commit 3 中自动执行
```

---

## 5. 门禁（每 commit 后必跑）

| 门 | 命令 | 通过条件 |
|----|------|----------|
| self-verify | `bash start.demo.sh` | `ALL GREEN` + `[share ✓ N/today]` |
| A/B prompt-equality | `bash examples/run_human_AB.sh` 或单独 extract_prompt diff | 两侧 prompt 完全一致 |
| plugin 契约 | `python insights-share/validation/test_plugin_contract.py` | PASS |
| 触发率 | `python insights-share/validation/trigger_rate.py` | ≥ 基线 |
| doc 完整性 | `bash ~/.claude/scripts/doc-integrity-check.sh` | PASS |
| 无 wiki leak | `grep -rn "insights-wiki" --exclude-dir=.git --exclude-dir=.archive --exclude-dir=.claude/worktrees .` | 只命中 rename proposal 表格 |

**任一破绿 → 单条 `git revert <commit>` → 立即停推**。

---

## 6. 回滚路径

- 单文件回退：`git mv .archive/2026-04-21/<mirror_path> <original_path>` → commit
- 单 commit 回退：`git revert <commit-sha>`
- 全量回退：`bash .archive/2026-04-21/REVERT.sh`
- 归档内容永久失效（确认稳定一个 demo 周期后）：单独 commit 删 `.archive/2026-04-21/`

---

## 7. 预期收益

| Tier | 归档体积 | 风险 | 动作 |
|------|----------|------|------|
| Tier 1 | ≈550K | 0 | 一次性 mv |
| Tier 2 | ≈380K | 低 | 逐条验后 mv |
| Tier 3 | ≈40M（artifacts 非 latest + node_modules 出仓） | 中 | `.gitignore` + 轮转 |
| **合计** | **≈41M** 从工作目录移出，311M → ≈270M | 全部可 revert | |

---

## 8. 不做

- 不 `git rm`（硬删），只 `git mv` 到 `.archive/`
- 不动根只读 md（proposal / README / validation / validation_AB）
- 不动 `docs/designs/user_design/`
- 不改数据模型（Topic Good/Bad 并列）
- 不改 MCP tool 名 `wiki_*`（留 M6_MCP_RENAME）
- 不重写 `start.demo.sh`，只校验
- 不新增 milestone，只做清理

---

## 9. 时间估算

| 阶段 | 用时 |
|------|------|
| Commit 0（骨架） | 5 min |
| Commit 1（Tier 1） | 5 min |
| Commit 2（Tier 2 逐条） | 15 min |
| Commit 3（Tier 3） | 10 min |
| 全流程门禁 | 15 min |
| **合计** | **≈50 min** |

---

## 10. 一句话契约

**归档不删、逐层 commit、门禁护航、`REVERT.sh` 兜底 → 40+M 瘦身，零破绿，1 工时内收工。**
