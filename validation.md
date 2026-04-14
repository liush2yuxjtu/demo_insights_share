验证

验证框架

1. 必须以 PM 友好的方式向用户展示输入/输出，使用 S-T-A-R 框架
2. 使用 tmux + claude -p 运行并捕获截图（从每条命令行和 tmux 开始）

验证任务

1. 触发率
    准备 20 个触发用例（10 个应触发、10 个不应触发），按 12 训练 / 8 测试划分
    持续优化触发率，直到达标

2. 优化触发效果
    示例：
        现状（Situation）：来自 [Alice 和 Bob 案例](insights-share/demo_docs/pm_walkthrough.md)
        任务（Task）：Bob 打开 Claude Code，不是主动求助，而是在输入与 PostgreSQL 相关的内容时，可能遇到同样的陷阱
        行动（Action）：Claude 发出最后一张图片后，Claude Code 触发一个 haiku-agent 对 insights-wiki 进行语义搜索并汇报最终结果
        结果（Result）：Claude Code 审查相关问题

        备注：触发方式应为
                静默直接执行（SILENT_AND_JUST_RUN）
                （可选但本设计不采用：请求用户确认 ASK_USER_APPROVAL，保留占位符但强制默认值为 SILENT_AND_JUST_RUN）

3. 更新 wiki：
    - 同一条目存在旧版和新版时：合并为一条
    - 绝不遗忘，标记为未触发
    - 新增
    - 删除
    - 调研
    - 编辑

4. wiki 结构：
    wiki_type（类型）：
        general_python
        frontend_python
        ...
        database
            INDEX.md
                条目格式：| 名称 | 描述 | 触发时机 | 指向 {type}/*.md 的文档链接 |
            postgres_并发_.md
                完整问题描述、反例（失败案例）与正例（成功案例），指向 {full_log}.jsonl 或 {full_export}.txt
            postgres_内存.md
            postgres_硬盘读取io.md

    重要：必须遵循 4 层结构：
        wiki_type_index => wiki 类型目录 / 类型 INDEX.md => wiki_item.md => 原始日志 jsonl/txt

5. 必须支持基于 minimax 的 agentic wiki 搜索
