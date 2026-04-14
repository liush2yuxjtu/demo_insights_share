现状（Situation）：claude /insights 功能本身很好，但存在以下问题：
    1. 生成耗时过长
    2. insights 仅对个人有效，无法适配其他团队成员
    3. 直接沿用他人的 insights 可能导致次优表现
    # update 0414 09:29
    4. uploading/downloading insights must be SILENT-IN-BACKGROUND
    5. force downloading insights to users when users are not aware as long as then load our insights tool 
    6. administrators can CRUD wiki-insights and review the wiki-insights . In this demo developing stage  , everyone is administrators 
    7. the wiki-insights work as a skill for now . 

任务（Task）：制作一个 demo，在局域网内发布 insights-share 功能
    1. 生成一条 insight
    2. 公司有一个 wiki 或渐进式披露系统
    3. 每次遇到新问题时，先从公司 wiki 中检索相关 insights
    4. 仅热加载 wiki-insights
    5. 在用户无感知的时间内快速比对并验证 insights
    6. 携带这些高层次 insights 继续工作
    备注：demo 必须基于 CLI。AGENTS 更容易使用 CLI；如需 REPL，应提供用于启动守护进程或服务器的 CLI
    备注：使用以下配置通过 agent-sdk 添加 AI 功能（minimax 2.7 速度快但较贵）：

    "ANTHROPIC_AUTH_TOKEN": "sk-cp-ocXR33dHiaUN25FsLP1kVkGtEW8gA71UoNWWIw_2zdllZXZ5j6hMH7LGiYpQdtVm8eHXOlTwCGNhBGnnRObBEdrkWlsmJBjpd3FCEdLK7ScX3hKOtbMUp50",
    "ANTHROPIC_BASE_URL": "https://api.minimaxi.com/anthropic",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "MiniMax-M2.7-highspeed",
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "MiniMax-M2.7-highspeed",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "MiniMax-M2.7-highspeed",
    "ANTHROPIC_MODEL": "MiniMax-M2.7-highspeed",

行动（Action）：
    请立即开始执行
    demo 面向 PM，而非开发者或 CEO
    请展示 MVP 产品，要求即点即用

预期结果（Expected Results）：
    一份完整的 demo 及配套 design.md，存放于 demos/{demo_topic}/demo_codes 和 demo_docs 目录下
    一份完整的终端截图或 .md 格式日志，用于展示执行过程
    # updates 0414 09:26
    1. fix : we MUST show to other agent developers 
    here is full list:
        1. before start : MUST write in linear style , tracking ~/.claude/projects/*, show the full timeline  
        2. a step by step of our proposal.md in html format 
            explain how we write proposal. 
        3. a step by step of our vlaidation.md in html format 
            explain how we design validation 
        4. open tmux and open claude and chat WITHOUT our demo and run /export in claude session to export a human-readable .txt format chat messages 
        5. open tmux and open claude and chat WITH our demo and run /export in claude session to export a human-readable .txt format chat messages 
        6. collector : proposal_linear.html , validation_linear.html , claude_export_WITH.txt , claude_expoert_WITHOUT.txt 

