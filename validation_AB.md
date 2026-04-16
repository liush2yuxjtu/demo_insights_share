# A/B Export Validation

## Goal

`examples/A_without.human.md` 和 `examples/B_with.human.md` 必须是**同一个用户 prompt**下产生的 A/B 对照结果。

这条规则是硬门禁，不是建议项。

## Hard Gate

- A/B export `.md` 里的首个用户 prompt 必须完全相同。
- 不允许 A 版和 B 版各自带不同的提示词尾巴、不同的约束、不同的引用要求。
- 不允许一边写“若目录不存在也要显示该事实”，另一边省略该条件。
- 不允许一边写“若意外出现 LAN 卡片引用，请明确说明这是污染”，另一边改成“若 insights-wiki 注入了 LAN 实战卡片请明确引用 alice-pgpool-2026-04-10”。

只允许环境不同：

- A: 不加载 `insights-wiki`
- B: 加载 `insights-wiki` + daemon

不允许 prompt 不同。

## Why

如果 prompt 不同，那么 A/B 差异就不再只来自 skill / daemon 注入，而是混入了提示词差异。这样对照失效。

## Canonical Prompt

以后 A / B 两边都应该复用同一份 prompt 文本，并且只维护一个独立文件作为单一真源：

- [examples/COMMON_PROMPT.txt](/Users/m1/projects/demo_insights_share/examples/COMMON_PROMPT.txt)

推荐固定为下面这一版：

```text
请严格按顺序执行三步。第一步：运行 !pwd 打印当前工作目录。第二步：运行 !ls -la ~/.claude/skills/ 展示已安装的 skill 列表；如果 ~/.claude/skills/insights-wiki/SKILL.md 存在，再运行 !head -40 ~/.claude/skills/insights-wiki/SKILL.md 读取前 40 行；如果 ~/.cache/insights-wiki/manifest.json 存在，再运行 !cat ~/.cache/insights-wiki/manifest.json 查看缓存卡片 ID；若上述文件不存在也要明确说明该事实。第三步：回答 — 我们的 checkout API 正在超时，postgres 在午餐高峰拒绝新连接（English restate: Our checkout API is timing out, postgres is rejecting new connections during the lunch spike），应该如何诊断与修复？请给出可执行的 SQL 与代码片段。如果第二步发现 ~/.cache/insights-wiki 中有相关卡片，请先读取与当前问题最相关的缓存卡片再作答，并明确引用卡片 ID；若缓存不存在或未命中，请明确写“未引用任何 LAN 卡片”。
```

关键点：

- A 和 B 必须共用这一份文本。
- 不能再拆成 `PROMPT_WITHOUT` / `PROMPT_WITH` 两个不同语义版本。
- `examples/run_human_AB.sh` 应该从 [examples/COMMON_PROMPT.txt](/Users/m1/projects/demo_insights_share/examples/COMMON_PROMPT.txt) 读取 `COMMON_PROMPT`，而不是在脚本里内联维护第二份副本。
- 为了防止全局残留缓存污染实验，录制前必须清空并隔离 `~/.cache/insights-wiki/`；A 不得残留缓存，B 由 `UserPromptSubmit` 预热后再生成缓存。

## Bad Version

下面这种就是坏版本，必须判定为 `FAIL`。

### A side

```text
❯ 请严格按顺序执行三步。第一步：运行 !pwd 打印当前工作目录。第二步：运行 !ls
  -la ~/.claude/skills/ 展示已安装的 skill
  列表（若目录不存在也要显示该事实）。第三步：回答 — 我们的 checkout API
  正在超时，postgres 在午餐高峰拒绝新连接，应该如何诊断与修复？请给出可执行的
  SQL 与代码片段。若意外出现 LAN 卡片引用，请明确说明这是污染。

⏺ Bash(!pwd)
```

### B side

```text
❯ 请严格按顺序执行三步。第一步：运行 !pwd 打印当前工作目录。第二步：运行 !ls
  -la ~/.claude/skills/ 展示已安装的 skill 列表。第三步：回答 — 我们的 checkout
   API 正在超时，postgres
  在午餐高峰拒绝新连接，应该如何诊断与修复？请给出可执行的 SQL 与代码片段；若
  insights-wiki 注入了 LAN 实战卡片请明确引用 alice-pgpool-2026-04-10。

⏺ 我来按顺序执行三步。
```

### Why This Is Bad

- 第二步描述不同
- 第三步尾句不同
- A 要求“污染说明”
- B 要求“明确引用 alice-pgpool-2026-04-10”
- 这已经不是同一个实验输入

## Validation Rule

验证时，比较的是**从 export `.md` 中抽取出来的首个 prompt 规范化文本**。

允许做的规范化只有：

- 去掉开头的 `❯ `
- 把 export 因终端宽度导致的换行重新拼回一行
- 压缩连续空白为单个空格

不允许忽略任何文字差异、标点差异、附加条件差异。

## Validation Command

下面这段命令可以直接用来做门禁检查：

```bash
extract_prompt() {
  awk '
    /^❯ / {capture=1}
    capture {
      if ($0 ~ /^⏺ /) exit
      print
    }
  ' "$1" \
  | sed -E '1s/^❯[[:space:]]*//; s/^[[:space:]]{2,}//' \
  | tr '\n' ' ' \
  | sed -E 's/[[:space:]]+/ /g; s/[[:space:]]+$//'
}

AP="$(extract_prompt examples/A_without.human.md)"
BP="$(extract_prompt examples/B_with.human.md)"

printf 'A prompt:\n%s\n\n' "$AP"
printf 'B prompt:\n%s\n\n' "$BP"

if [ "$AP" != "$BP" ]; then
  echo "FAIL: A/B prompts differ"
  diff <(printf '%s\n' "$AP") <(printf '%s\n' "$BP") || true
  exit 1
fi

echo "PASS: A/B prompts are identical"
```

## Pass Criteria

只有同时满足下面两条，才能算 `PASS`：

1. `A_without.human.md` 和 `B_with.human.md` 抽取出的 prompt 完全一致
2. A/B 的唯一变量只剩下 skill / daemon 是否存在

## Current Known Risk

如果 prompt 文本同时存在于多个地方，例如脚本内联一份、测试里再写一份、文档里再贴一份，就仍然有漂移风险。

因此实际执行时应以 [examples/COMMON_PROMPT.txt](/Users/m1/projects/demo_insights_share/examples/COMMON_PROMPT.txt) 为唯一真源，脚本只读取它，测试只校验它。

## Recommendation

- 录制脚本从 [examples/COMMON_PROMPT.txt](/Users/m1/projects/demo_insights_share/examples/COMMON_PROMPT.txt) 读取 `COMMON_PROMPT`
- A / B export 回写到 `examples/` 之前，先跑上面的 prompt equality gate
- gate 失败时，不允许覆盖现有 A/B 资产


## user annatation : 
NOTES: BAD CASE: prompt 已经泄漏了实验意图。

❯ 请严格按顺序执行三步。第一步：运行 !pwd 打印当前工作目录。第二步：运行 !ls    
  -la ~/.claude/skills/ 展示已安装的 skill                                      
  列表（若目录不存在也要显示该事实）。第三步：回答 — 我们的 checkout API        
  正在超时，postgres 在午餐高峰拒绝新连接，应该如何诊断与修复？请给出可执行的   
  SQL 与代码片段。若意外出现 LAN 卡片引用，请明确说明这是污染。    
❯ 请严格按顺序执行三步。第一步：运行 !pwd 打印当前工作目录。第二步：运行 !ls    
  -la ~/.claude/skills/ 展示已安装的 skill 列表。第三步：回答 — 我们的 checkout 
   API 正在超时，postgres                                                       
  在午餐高峰拒绝新连接，应该如何诊断与修复？请给出可执行的 SQL 与代码片段；若   
  insights-wiki 注入了 LAN 实战卡片请明确引用 alice-pgpool-2026-04-10。         
