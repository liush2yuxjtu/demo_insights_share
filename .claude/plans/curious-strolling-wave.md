# Plan: 创意打招呼

## Context

用户在测试 plan mode 流程，要求"用创意方式说 hi"。这是一个轻量演示任务，目的是验证 plan 模式从理解 → 设计 → 写入 plan 文件 → ExitPlanMode 的完整闭环，同时产出一个有趣的、可视化的问候作品。

结合项目级规则（中文输出、可视化优先输出到 `/tmp/TOPIC.html`、HTML 写入后自动 Chrome 弹出），最贴合的形态是一个单页 HTML 打招呼作品。

## 推荐方案

**形式**：一个自包含的单页 HTML 问候卡 `/tmp/hi.html`

**创意要点**：
1. 全屏渐变背景（深紫 → 蓝 → 青）+ 噪点纹理
2. 中文大字 `你好，m1 👋`（字体由 system-ui 兜底；按规则不主动加 emoji，使用文字 `挥手`）
3. 字符逐个淡入 + 轻微浮动动画（CSS keyframes，无 JS 依赖）
4. 下方副标题循环切换：`Hi` / `こんにちは` / `Bonjour` / `Hola` / `안녕` / `你好`（多语言轮播）
5. 鼠标移动时背景跟随产生视差光斑（轻量 JS）
6. 右下角小字标注：`plan-mode 演示 · 2026-04-14`

**为什么用 HTML 而不是终端 ASCII**：
- 项目规则明确"可视化优先 → /tmp/TOPIC.html"
- 写入后会自动 `open -a "Google Chrome"`，可立即看到效果
- 视觉冲击力比终端 echo 更强，更符合"创意"诉求

## 关键文件

| 文件 | 操作 | 说明 |
|------|------|------|
| `/tmp/hi.html` | 新建 | 自包含单页：内联 CSS + 内联 JS，无外部资源依赖 |

## 实现步骤

1. Write `/tmp/hi.html`（约 80–120 行，HTML/CSS/JS 全内联）
2. Bash `open -a "Google Chrome" /tmp/hi.html` 自动弹出预览
3. 在最终回复里报告：文件路径 + 一句话效果描述

## 验证

- **命令**：`open -a "Google Chrome" /tmp/hi.html`
- **预期**：Chrome 新标签页打开，看到渐变背景 + 中文大字淡入 + 多语言副标题循环 + 鼠标视差
- **失败兜底**：若 Chrome 未安装则改用 `open /tmp/hi.html`（系统默认浏览器）

## 不做的事

- 不引入任何外部 CDN / 字体 / 图片（保持单文件自包含）
- 不写到项目源码目录（仅 `/tmp/`，不污染 git 工作区）
- 不加表情符号（遵循 `Only use emojis if user explicitly requests it`）
- 不创建额外文档/报告文件（任务太轻量，不需要证据 HTML）
