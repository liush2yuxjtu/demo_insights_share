# 优秀 HTML 示例归档

## 规则

当用户明确表示某个 HTML 页面是“perfect”“good example”或要求将其沉淀为可复用示例时，Agent 必须把该页面的原始 HTML 内容原样归档到 `docs/examples/`，并在规则文档中记录来源与用途。

## 归档要求

- 必须保存原始 HTML：归档文件内容应与源 HTML 文件逐字一致，不得自行改写结构、内联脚本、压缩或追加说明文字。
- 默认保留原始资源引用：若源文件使用 `/static/*.css`、`/static/*.js` 等相对或站内路径，归档时保持不变。
- 文件名应清晰表达主题，推荐使用 `*.raw.html` 后缀，表示这是原始 HTML 快照。
- 若需要解释示例用途、来源、适用边界，应写入 `docs/rules/*.md` 或其他说明文档，不得污染归档的 raw HTML。

## 当前示例

- `docs/examples/claude-code-cli-tmux-window.raw.html`
  来源：`insights-share/demo_codes/insightsd/cli.html`
  用途：作为 “tmux terminal stream web version” 的优质网页示例，保留 Claude Code CLI 浏览器映射窗口的原始 HTML 结构。

## 触发场景

- 用户明确要求“保存为 good example”
- 用户要求把某个网页模板沉淀到 `docs/examples/`
- 用户要求保留“raw contents of html”

## 不应这样做

- 只保存截图，不保存 HTML 原文
- 只写总结，不留原始页面结构
- 为了“更漂亮”而修改归档文件，使其与源文件不一致
