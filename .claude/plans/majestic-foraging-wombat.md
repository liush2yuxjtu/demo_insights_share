# 鸭子池塘 A/B demo — 4 项修复实施方案

## Context

当前 GitHub Pages 主页 `https://liush2yuxjtu.github.io/demo_insights_share/examples/` 上线后发现 4 个问题，需要一次性修复：

1. **鸭子故事太长**（2100+ 字）— 只有 Postgres/DBA 领域读者有耐心看完，其余前端/DL/小白读者会划走
2. **命令 2️⃣ 超长**（一整串 `rm && git clone && cp && nohup && sleep && curl && claude -p`）— 缺乏步骤感、出错难定位、没有 fallback
3. **A_without.human.md 意外触发了 insights-wiki skill 的 Stop hook** — user 级 skill 无条件全局触发，把 `alice-pgpool-2026-04-10` wiki 卡片注入到本应纯净的 A/WITHOUT 场景，污染对照实验
4. **A/B 脚本没有用隔离的 `/tmp/{workspace}/` 临时目录** — cwd 污染、产物乱放

修复目标：让 4 类读者（前端 / 后端 / 深度学习 / AI 小白）都能在 1 分钟内看懂 demo，让命令能分步复制 + 便于排错，让 A/B 对照实验在干净的隔离环境里跑，并且彻底根除 user 级 skill 对 A 场景的污染。

## 用户决策（已确认）

| 决策点 | 选择 |
|--------|------|
| Skill 禁用方式 | `mv ~/.claude/skills/insights-wiki → ~/.claude/skills.disabled/insights-wiki.disabled` |
| 命令 2️⃣ fallback | 不 fallback，`git clone ... \|\| echo "❌ clone 失败，请检查 github 配置"` |
| 故事切换方式 | 4 按钮切换，**默认显示"后端"版本**（呼应当前 Postgres 主题） |
| A/B 工作目录命名 | `/tmp/demo_insights_A`（WITHOUT）、`/tmp/demo_insights_B`（WITH） |

## 实施顺序（按风险由低到高）

1. **修复 3** — 移动 user 级 skill 到 `skills.disabled/`（文件系统操作，最先做以验证 project 级 skill 仍正常）
2. **修复 4** — 改 4 个 .sh 脚本 + HTML 命令行 `cd /tmp/demo_insights_{A,B}`
3. **修复 2** — 拆命令 2️⃣ 为 2a/2b，加 fallback 错误打印
4. **修复 1** — HTML 鸭子故事改为 4 按钮切换 4 段短文

## Critical Files to Modify

- `/Users/m1/projects/demo_insights_share/examples/index.html` （主页，修复 1+2+4）
- `/Users/m1/projects/demo_insights_share/insights-share/validation/with_reproduce.sh`
- `/Users/m1/projects/demo_insights_share/insights-share/validation/without_reproduce.sh`
- `/Users/m1/projects/demo_insights_share/insights-share/validation/with_oneline.sh`
- `/Users/m1/projects/demo_insights_share/insights-share/validation/without_oneline.sh`
- 文件系统：`~/.claude/skills/insights-wiki` 和 `~/.claude/skills/insights-wiki-server` → 移动到 `~/.claude/skills.disabled/`

Project 级 skill 保持原位不动：`/Users/m1/projects/demo_insights_share/insights-share/demo_codes/.claude/skills/insights-wiki{,-server}/`

---

## 修复 3 · 移除 user 级 skill（避免 A 场景污染）

### 操作步骤

```bash
# 1. 确保 skills.disabled 父目录存在
mkdir -p ~/.claude/skills.disabled

# 2. 移动 user 级 skill（保留回滚路径）
mv ~/.claude/skills/insights-wiki        ~/.claude/skills.disabled/insights-wiki.disabled
mv ~/.claude/skills/insights-wiki-server ~/.claude/skills.disabled/insights-wiki-server.disabled

# 3. 确认 user 级 skills 目录不再有 insights-wiki*
ls ~/.claude/skills/ | grep -i insights  # 应为空
```

### 依据（Phase 1 已验证）

- user 级 `~/.claude/settings.json` 的 Stop hook 块**不**包含 `insights_stop_hook.py`，说明 Stop hook 是通过 skill 目录自身的 SKILL.md frontmatter 加载的
- 因此"目录改名"就足以停用 hook，无需改 settings.json
- project 级 skill 独立存在于 `demo_codes/.claude/skills/`，不受影响

### 验证

```bash
# 验证 1：user 级 skill 已禁用
ls ~/.claude/skills/ | grep insights  # 期望：空输出

# 验证 2：A_without 场景不再自动注入 alice-pgpool 卡片
cd /tmp && claude -p "postgres 超时怎么办" 2>&1 | grep -c alice-pgpool-2026-04-10
# 期望：0

# 验证 3：project 级 skill 目录仍完整
ls /Users/m1/projects/demo_insights_share/insights-share/demo_codes/.claude/skills/
# 期望：看到 insights-wiki 和 insights-wiki-server
```

---

## 修复 4 · A/B 脚本统一 `/tmp/demo_insights_{A,B}` 隔离目录

### 脚本改动（4 个文件）

**`without_reproduce.sh` 和 `without_oneline.sh`（A / WITHOUT）** 开头加：

```bash
WORKSPACE_A="/tmp/demo_insights_A"
rm -rf "$WORKSPACE_A"
mkdir -p "$WORKSPACE_A"
cd "$WORKSPACE_A"
```

**`with_reproduce.sh` 和 `with_oneline.sh`（B / WITH）** 把原有 `CLONE_DIR=/tmp/insights-share-clone.$$` / `CLONE=/tmp/insights-share-clone-oneline` 全部替换为：

```bash
WORKSPACE_B="/tmp/demo_insights_B"
rm -rf "$WORKSPACE_B"
mkdir -p "$WORKSPACE_B"
cd "$WORKSPACE_B"
CLONE_DIR="$WORKSPACE_B/isw-clone"
```

后续 `git clone`、`cp -r`、`nohup python3 ...` 的目标路径全部改用 `$WORKSPACE_B/...`。产物 log 写 `$WORKSPACE_B/B_with.log` 而非 `/tmp/B_with.log`。

### HTML 命令行改动（examples/index.html 命令 1/2a/2b/3）

- 命令 1️⃣ 开头加 `mkdir -p /tmp/demo_insights_A && cd /tmp/demo_insights_A &&`
- 命令 2a / 2b 开头加 `mkdir -p /tmp/demo_insights_B && cd /tmp/demo_insights_B &&`
- 命令 3️⃣ 显式 `grep -c alice-pgpool-2026-04-10 /tmp/demo_insights_A/A_without.log /tmp/demo_insights_B/B_with.log`

### 验证

```bash
bash insights-share/validation/without_reproduce.sh
ls /tmp/demo_insights_A/   # 看到 A_without.log
bash insights-share/validation/with_reproduce.sh
ls /tmp/demo_insights_B/   # 看到 isw-clone/ 和 B_with.log
echo "原 cwd: $(pwd)"      # 确认脚本结束后 cwd 未被改
```

---

## 修复 2 · 命令 2️⃣ 拆成 2a / 2b + 不 fallback 打印错误

### HTML 改动（examples/index.html 命令块区域）

**命令 2a（github clone，无 fallback）**：

```bash
mkdir -p /tmp/demo_insights_B && cd /tmp/demo_insights_B && \
rm -rf isw-clone && \
git clone --depth 1 https://github.com/liush2yuxjtu/demo_insights_share.git isw-clone \
  || { echo "❌ git clone 失败，请检查 github 配置（ssh key / https token）后重试"; exit 1; } && \
echo "✅ Step 2a: clone 完成 → /tmp/demo_insights_B/isw-clone"
```

"你会看到"提示：绿色框显示 `✅ Step 2a: clone 完成`，大约 10~30 秒。

**命令 2b（install skill + 启 daemon + 注入问答）**：

```bash
cd /tmp/demo_insights_B && \
rm -rf ~/.claude/skills.disabled/insights-wiki.active ~/.claude/skills.disabled/insights-wiki-server.active 2>/dev/null; \
cp -r isw-clone/insights-share/demo_codes/.claude/skills/insights-wiki        ~/.claude/skills/ && \
cp -r isw-clone/insights-share/demo_codes/.claude/skills/insights-wiki-server ~/.claude/skills/ && \
(cd isw-clone/insights-share/demo_codes && nohup python3 insights_cli.py serve --host 0.0.0.0 --port 7821 --store ./wiki.json > /tmp/demo_insights_B/isd.log 2>&1 &) && \
sleep 3 && curl -sf http://127.0.0.1:7821/insights >/dev/null && \
claude -p "我们的 checkout API 正在超时，postgres 在午餐高峰拒绝新连接，应该如何诊断与修复？若 insights-wiki 注入了 LAN 实战卡片请在回答里明确引用。" 2>&1 \
  | sed -E 's/\x1b\[[0-9;]*[A-Za-z]//g' > /tmp/demo_insights_B/B_with.log && \
echo "✅ Step 2b: B_with.log $(wc -c < /tmp/demo_insights_B/B_with.log) bytes"
```

"你会看到"提示：`✅ Step 2b: B_with.log ~XX000 bytes`。

**复制按钮**：分别绑定到 `id="cmd2a"` 和 `id="cmd2b"`，沿用现有 `copyCmd(btn, id)` JS，无需改 JS（已验证 `pre.childNodes[0].nodeValue` 取首文本节点在纯文本 pre 上正常工作）。

### 注意事项

- 命令 2b 需要注意：它会把 skill **写入 user 级 `~/.claude/skills/`**。这和修复 3（禁用 user 级 skill）看似冲突，实际不冲突：修复 3 只清理**当前已有**的 stale skill；命令 2b 是 B 场景**主动安装** skill（这正是 WITH 场景的语义）。所以命令 2b 运行前必须保证 user 级 skill 不存在（修复 3 已做到），2b 运行完会临时装回来。
- 命令 1️⃣ 需要在开头再次 `rm -rf ~/.claude/skills/insights-wiki*` 来清理 B 场景残留，确保 A/B 可循环跑。

### 验证

```bash
# 复制命令 2a 粘贴运行 → 看到 ✅ Step 2a: clone 完成
# 断网或改 URL 为 404 → 看到 ❌ git clone 失败... 提示
# 复制命令 2b 粘贴运行 → 看到 ✅ Step 2b: B_with.log XXXX bytes
grep -c alice-pgpool-2026-04-10 /tmp/demo_insights_B/B_with.log  # 期望 ≥1
```

---

## 修复 1 · 4 按钮切换 4 段短故事（默认后端）

### HTML 改动（examples/index.html 鸭子故事区块）

把原 `<div class="story-box">` 2100+ 字整段替换为：

```html
<section class="story-section">
  <div class="story-tabs">
    <button class="story-tab" data-role="frontend" onclick="showStory('frontend')">👩‍🎨 我是前端</button>
    <button class="story-tab active" data-role="backend" onclick="showStory('backend')">🛠️ 我是后端</button>
    <button class="story-tab" data-role="dl" onclick="showStory('dl')">🧠 我是深度学习</button>
    <button class="story-tab" data-role="noob" onclick="showStory('noob')">🐣 我是 AI 小白</button>
  </div>

  <div id="story-frontend" class="story-box" style="display:none;"> … 前端类比 300-400 字 … </div>
  <div id="story-backend"  class="story-box"> … 后端类比 300-400 字（默认显示） … </div>
  <div id="story-dl"       class="story-box" style="display:none;"> … 深度学习类比 300-400 字 … </div>
  <div id="story-noob"     class="story-box" style="display:none;"> … AI 小白类比 300-400 字 … </div>
</section>

<script>
function showStory(id) {
  ['frontend','backend','dl','noob'].forEach(k => {
    document.getElementById('story-' + k).style.display = (k === id ? 'block' : 'none');
    document.querySelector('.story-tab[data-role="' + k + '"]').classList.toggle('active', k === id);
  });
}
</script>
```

CSS 新增 `.story-tab` / `.story-tab.active` 样式（参考现有 `.btn` 样式保持视觉一致）。

### 4 段故事内核（每段 300-400 字，统一保留 `alice-pgpool-2026-04-10` 卡片锚点）

**共同结构**：
1. 场景：每次"从头找答案"很慢（1-2 句）
2. 老鸭奶奶发"木头筐"（共享知识）（1-2 句）
3. 对应到 claude-code 的 insights-wiki skill（1-2 句）
4. 呼应 alice 卡片、A/B 对照结果（1 句）

**前端版**（类比 hooks/memo/Context）：
- 场景：每次组件重新 mount 都要重新 fetch + 计算 state → 慢
- 木头筐 = `useMemo` / Context Provider / localStorage 缓存
- insights-wiki = 团队共享的"已经用过的 hooks 写法集"
- alice 卡片 = 某次处理 checkout 按钮超时的"同款写法"

**后端版**（默认显示，类比 middleware/cache/pool）：
- 场景：每个请求都重新建连接 / 每个开发者都重新查 Slack 是不是过 pool
- 木头筐 = PgBouncer / Redis / 团队 wiki 的现成方案
- insights-wiki = LAN wiki + Stop hook 的"自动查找同款问题的记忆"
- alice 卡片 = Alice 在 2026-04-10 记录的 pgpool 卡片

**深度学习版**（类比 checkpoint/pretrain/transfer）：
- 场景：每次 fine-tune 都从头训，epoch 又长 loss 又高
- 木头筐 = 预训练权重 / checkpoint / transfer learning
- insights-wiki = 团队已训练好的"经验 embedding"（实战卡片）
- alice 卡片 = 一条"alice-pgpool"这种 pretrained insight，直接 load

**AI 小白版**（完全大白话）：
- 场景：新同事每次遇到问题都要从头翻 Slack/Google/问人
- 木头筐 = 老同事写的"遇到这个问题直接这样做"的便签本
- insights-wiki = Claude 自己学会了从便签本里翻答案
- alice 卡片 = 便签本里其中一张「Alice 在 4 月 10 号写过的小贴士」

### 验证

```bash
# 1. 打开页面验证 4 段切换
open examples/index.html
# 默认显示"后端"版，点"我是前端"切换到前端版，以此类推

# 2. 字数检查（每段 300-400 字）
grep -c . examples/index.html  # 粗略
# 或在浏览器 DevTools 中：document.getElementById('story-backend').innerText.length
```

---

## 端到端验证清单

| 序 | 验证项 | 命令 | 通过标准 |
|----|--------|------|----------|
| 1 | user 级 skill 已禁用 | `ls ~/.claude/skills/ \| grep insights` | 空输出 |
| 2 | skills.disabled 目录存在 | `ls ~/.claude/skills.disabled/` | 看到两个 `.disabled` 目录 |
| 3 | A 场景无污染 | 跑 without_reproduce.sh 后 `grep -c alice-pgpool` A 日志 | 0 |
| 4 | B 场景命中卡片 | 跑 with_reproduce.sh 后 `grep -c alice-pgpool` B 日志 | ≥1 |
| 5 | A 工作目录隔离 | `ls /tmp/demo_insights_A/` | 看到 A_without.log |
| 6 | B 工作目录隔离 | `ls /tmp/demo_insights_B/` | 看到 isw-clone/ 和 B_with.log |
| 7 | 命令 2a fallback 错误 | 改 URL 为 404 后粘贴 2a | 看到 ❌ git clone 失败... |
| 8 | 命令 2a 正常 clone | 正常粘贴 2a | 看到 ✅ Step 2a 完成 |
| 9 | 命令 2b 启 daemon 成功 | 正常粘贴 2b | 看到 ✅ Step 2b: B_with.log XX bytes |
| 10 | 4 按钮切换正常 | 浏览器打开 index.html 点每个按钮 | 只有对应段显示，active 状态切换 |
| 11 | 默认显示后端 | 首次加载页面 | backend 段可见，其余 display:none |
| 12 | HTML console 零错误 | 浏览器 DevTools Console | 无红色 Error |
| 13 | 每段故事字数 ≤ 400 字 | `innerText.length` | 每个 story-* div < 400 |

## 风险与回滚

| 风险 | 缓解 |
|------|------|
| 移走 user 级 skill 后别的 skill 依赖它会连锁失败 | 用 mv 而非 rm，回滚只需 `mv ~/.claude/skills.disabled/*.disabled ~/.claude/skills/` |
| 命令 2b 成功后又把 skill 装回 user 级，重复跑会污染下一次 A | 命令 1️⃣ 已有 `rm -rf ~/.claude/skills/insights-wiki*`，能清干净 |
| port 7821 daemon 未停导致第二次 2b 失败 | 命令 1️⃣ 开头保留 `pkill -f insights_cli.py` |
| copyCmd JS `childNodes[0].nodeValue` 取文本在新 pre 上失效 | 新 pre 不要内嵌 `<span>` 等子元素，保持纯文本；若后续需要高亮则改为 `innerText.replace('📋 复制','')` |
| GitHub Pages CDN 缓存 5-15 min | 部署 commit 后需 Ctrl+Shift+R，或等 15 min |
| 故事 JS 初始化前 4 段同时可见闪烁 | 原始 HTML 中 `display:none` 兜底，不依赖 JS 执行顺序 |

## 部署

修复 3 立即生效（本地 FS 操作）；修复 1/2/4 需要 commit → push → GitHub Pages rebuild（约 45 秒）。commit 消息示例：

```
fix(examples): 4 类读者故事切换 + 命令拆分 + /tmp/demo_insights_{A,B} 隔离 + 禁用 user 级 skill
```
