# 鸭子池塘 A/B demo 四项修复实施方案

仓库: /Users/m1/projects/demo_insights_share
主 target: /Users/m1/projects/demo_insights_share/examples/index.html
辅助 targets: insights-share/validation/*.sh, ~/.claude/skills/insights-wiki*

---

## 1. 实施顺序（风险从低到高）

| 序 | 修复 | 风险 | 可回滚 | 依赖 |
|----|------|------|--------|------|
| 1 | 修复 3 · 移除 user 级 skill（重命名为 .disabled） | 中 | 一条 mv 即可还原 | 无 |
| 2 | 修复 4 · .sh 脚本改用 /tmp/workspace_A|B | 低 | git checkout | 无 |
| 3 | 修复 2 · 命令 2️⃣ 拆成 2a/2b + fallback | 低 | git checkout | 依赖修复 4 的目录约定 |
| 4 | 修复 1 · 故事拆 4 读者版 + JS 切换 | 低 | git checkout | 无 |

**理由**: 修复 3 最脆弱（动文件系统 + 可能影响 daemon），先做并立即验证 project 级 skill 仍加载；其余 3 项是纯文件编辑，可平行验证。

---

## 2. 修复 3 · 移除 user 级 insights-wiki skill（优先执行）

**现状**: `~/.claude/skills-disabled/insights-wiki.disabled/` 已存在（前次尝试），但 `~/.claude/skills/insights-wiki/` 和 `~/.claude/skills/insights-wiki-server/` 仍在活动目录，settings.local.json 里已预授权 `mv` 命令。

**操作**（推荐"重命名"而非"rm -rf"，零风险）：
```bash
mv ~/.claude/skills/insights-wiki ~/.claude/skills/insights-wiki.disabled.$(date +%s)
mv ~/.claude/skills/insights-wiki-server ~/.claude/skills/insights-wiki-server.disabled.$(date +%s)
```

**验证**:
```bash
# 1. 确认 user 级已消失
ls ~/.claude/skills/ | grep insights        # 应无输出

# 2. 确认 project 级仍存在
ls /Users/m1/projects/demo_insights_share/insights-share/demo_codes/.claude/skills/

# 3. 纯净环境跑 A_without 命令（修复前常被污染）
pkill -f "insights_cli.py serve" 2>/dev/null
claude -p "postgres 午高峰拒绝连接" > /tmp/A_clean_test.log 2>&1
grep -c alice-pgpool-2026-04-10 /tmp/A_clean_test.log   # 期望 0
```

**澄清点**: 是否完全删除还是仅重命名？建议重命名保留回滚路径。

---

## 3. 修复 4 · A/B 脚本统一 /tmp/workspace_A|B

**改动文件** (4 个 shell 脚本):
- `insights-share/validation/with_reproduce.sh`
- `insights-share/validation/without_reproduce.sh`
- `insights-share/validation/with_oneline.sh`
- `insights-share/validation/without_oneline.sh`

**关键改动**:
```bash
# 每个脚本开头新增
WORKSPACE_A="/tmp/workspace_A"      # without_*.sh 用
WORKSPACE_B="/tmp/workspace_B"      # with_*.sh 用
rm -rf "${WORKSPACE_B}" && mkdir -p "${WORKSPACE_B}"
cd "${WORKSPACE_B}"
# 原来的 CLONE_DIR/OUT_DIR 全部改为 ${WORKSPACE_B}/clone, ${WORKSPACE_B}/out
```

**examples/index.html 命令 1️⃣/2a/2b/3️⃣ 全部前置**:
```bash
mkdir -p /tmp/workspace_A && cd /tmp/workspace_A && <原命令>
```

**验证**:
```bash
bash insights-share/validation/without_reproduce.sh && ls /tmp/workspace_A/
bash insights-share/validation/with_reproduce.sh && ls /tmp/workspace_B/
pwd   # 脚本结束后当前目录应未被污染
```

**澄清点**: 命名选 `/tmp/workspace_A` 还是 `/tmp/demo_insights_A`？建议前者（更通用）。

---

## 4. 修复 2 · 命令 2️⃣ 拆成 2a (clone + fallback) + 2b (install+run)

**改动文件**: `examples/index.html` line 386-407 的 `<!-- 命令 2 -->` 区块。

**2a · git clone with fallback**:
```html
<div class="cmd-card b">
  <h3>2a · 拉取 insights-share 仓库</h3>
  <div class="what-happens"><strong>你会看到：</strong>git clone 成功，/tmp/workspace_B/isw-clone 下出现仓库</div>
<pre id="cmd2a">mkdir -p /tmp/workspace_B && cd /tmp/workspace_B && rm -rf isw-clone && (git clone --depth 1 https://github.com/liush2yuxjtu/demo_insights_share.git isw-clone || cp -r /Users/m1/projects/demo_insights_share isw-clone) && echo "✅ clone ok → $(ls isw-clone | head -3)"<button class="copy-btn" onclick="copyCmd(this,'cmd2a')">📋 复制</button></pre>
```

**2b · 安装 skill + 启 daemon + 发问**:
```html
<pre id="cmd2b">cd /tmp/workspace_B && rm -rf ~/.claude/skills/insights-wiki ~/.claude/skills/insights-wiki-server && cp -r isw-clone/insights-share/demo_codes/.claude/skills/insights-wiki ~/.claude/skills/ && cp -r isw-clone/insights-share/demo_codes/.claude/skills/insights-wiki-server ~/.claude/skills/ && (cd isw-clone/insights-share/demo_codes && nohup python3 insights_cli.py serve --host 0.0.0.0 --port 7821 --store ./wiki.json > /tmp/isd.log 2>&1 &) && sleep 3 && curl -sf http://127.0.0.1:7821/insights >/dev/null && claude -p "checkout API 超时 postgres 拒绝连接" 2>&1 | sed -E 's/\x1b\[[0-9;]*[A-Za-z]//g' > /tmp/B_with.log && echo "✅ B/WITH → /tmp/B_with.log"<button class="copy-btn" onclick="copyCmd(this,'cmd2b')">📋 复制</button></pre>
```

**JS 无需改**: 现有 `copyCmd` 已用 ID 参数化。

**澄清点**:
- fallback 是直接 `cp -r /Users/m1/projects/demo_insights_share`（硬编码绝对路径，用户机器可能不同）还是 `cp -r $(dirname $(pwd))` 或改为提示用户设置 `INSIGHTS_LOCAL_REPO` 环境变量？
- 是否保留原单行命令 2️⃣ 作为"高级一行版"备份？

---

## 5. 修复 1 · 鸭子故事拆 4 读者版

**改动文件**: `examples/index.html` line 285-356 的 `<!-- 鸭子故事 -->` 区块。

**HTML 结构**:
```html
<h2>🦆 鸭子故事（选你的身份）</h2>
<div class="audience-bar">
  <button class="btn pink"  onclick="showStory('frontend')">我是前端</button>
  <button class="btn blue"  onclick="showStory('backend')">我是后端</button>
  <button class="btn purple" onclick="showStory('dl')">我是深度学习</button>
  <button class="btn amber" onclick="showStory('noob')">我是 AI 小白</button>
</div>

<div class="story-box" id="story-frontend" style="display:none">…300-400 字版…</div>
<div class="story-box" id="story-backend" style="display:block">…</div>
<div class="story-box" id="story-dl" style="display:none">…</div>
<div class="story-box" id="story-noob" style="display:none">…</div>
```

**JS 追加到 line 519 script 块**:
```javascript
function showStory(id) {
  ['frontend','backend','dl','noob'].forEach(k => {
    document.getElementById('story-' + k).style.display = (k === id ? 'block' : 'none');
  });
}
```

**4 个版本核心类比**（每版 ~350 字）:

| 读者 | 类比 | 关键词 |
|------|------|--------|
| 前端 | useEffect 每次重新 fetch → useMemo/Context 全局缓存；组件 rerender 每次重写荷叶 vs 高阶组件共享 | hooks, Context, memo |
| 后端 | 每个 API handler 重新查 DB → Redis 缓存 + connection pool；老鸭奶奶 ≈ middleware 自动注入 headers | middleware, cache, pool |
| 深度学习 | 每个 epoch 从零训练 → checkpoint 续训；荷叶 ≈ pretrained weights，老鸭奶奶 ≈ transfer learning | checkpoint, pretrain, transfer |
| 小白 | 新员工每次入职重新踩坑 → 前辈交班手册自动贴到新员工桌上 | 手册, 经验, 自动 |

每版保留不变内核: 新鸭从头找荷叶 → 老鸭奶奶发木头筐 → Alice 的 alice-pgpool-2026-04-10 卡片。

**默认显示**: 后端（原故事受众）。

**澄清点**:
- 4 段故事的具体文案是我在 plan 里写草稿，还是用户先审核一段范例？
- 是否保留原长版作为"大鸭子模式"按钮？

---

## 6. 验证方法总览

| 修复 | 验证命令 | 通过标准 |
|------|----------|----------|
| 3 | `ls ~/.claude/skills/ \| grep insights` | 无输出 |
| 3 | `claude -p "postgres 超时" \| grep alice-pgpool` | 0 命中（纯净 A） |
| 4 | `bash without_reproduce.sh; ls /tmp/workspace_A/` | 看到 clone/out 子目录 |
| 4 | `pwd`（脚本结束后） | 仍为原始 cwd |
| 2 | 断网测试 2a: `sudo dscacheutil -flushcache; <cmd2a>` | fallback 分支触发 |
| 2 | 正常跑 2a + 2b | 两次 echo ✅ 均出现 |
| 1 | 浏览器打开 index.html 点 4 个按钮 | 4 段切换，每段 300-400 字 |
| 1 | `wc -w examples/index.html` 故事块字数 | 每版 <= 400 字 |

---

## 7. 风险识别

| 风险 | 影响 | 缓解 |
|------|------|------|
| 删 user 级 skill 后某个 MCP 或其它技能依赖它 | 其它 skill 失败 | 用重命名而非 rm，保留 `.disabled.<ts>` 回滚点 |
| fallback cp 硬编码 `/Users/m1/...` 路径在别人机器失效 | cmd 2a 在非作者机器报 No such file | 用 `${INSIGHTS_LOCAL_REPO:-/path}` 允许覆盖，README 提示 |
| /tmp/workspace_B 跨 run 残留导致 clone 失败 | B 脚本挂 | 每次开头 `rm -rf` 清理 |
| 故事切换 JS 选错默认 id 导致 4 块都显示 | 页面高度炸 | 初始 CSS `display:none` 除 backend，JS 硬同步 |
| GitHub Pages 缓存 5-15min，修改后用户看到旧版 | 体验延迟 | 部署后 Ctrl+Shift+R；PR 合并后等 5min |
| 命令 2b 里 nohup 启的 daemon 进程未被 pkill 清理 → 端口 7821 占用 | 后续 run 连不上 | 命令 1️⃣ 的 `pkill -f insights_cli.py serve` 需保留 |
| copyCmd JS 目前取 `pre.childNodes[0].nodeValue`（首文本节点），若新 pre 内有嵌套 span/元素前置会取错 | 复制出错文本 | 新增的 pre 保持首子节点仍为纯文本；或改为 `pre.innerText` 去掉末尾 `📋 复制` 字符串 |

---

## 8. 汇总 · 需用户澄清的决策点

1. **修复 3**: 删除 vs 重命名 `.disabled`？（建议后者）
2. **修复 4**: 目录命名 `/tmp/workspace_A|B` vs `/tmp/demo_insights_A|B`？（建议前者）
3. **修复 2 fallback**: 硬编码绝对路径 vs `$INSIGHTS_LOCAL_REPO` env vs 仅提示不 fallback？
4. **修复 2**: 是否保留原超长一行命令作为"高级"备份？
5. **修复 1**: 4 段故事由我写草稿还是用户先看一段范例对齐风格？
6. **修复 1**: 是否保留原 2100+ 字版作为"全版"按钮？
7. **修复 1**: 默认显示哪一类？（建议后端 = 保持现状受众）

---

## Critical Files for Implementation

- /Users/m1/projects/demo_insights_share/examples/index.html
- /Users/m1/projects/demo_insights_share/insights-share/validation/with_reproduce.sh
- /Users/m1/projects/demo_insights_share/insights-share/validation/without_reproduce.sh
- /Users/m1/projects/demo_insights_share/insights-share/validation/with_oneline.sh
- /Users/m1/projects/demo_insights_share/insights-share/validation/without_oneline.sh
