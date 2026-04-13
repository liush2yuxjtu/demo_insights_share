validation 

validation framework 

1. MUST show users how the inputs ,outputs in PM-friendly way and use S-T-A-R frames 
2. use tmux + claude -p to run and catch the snapshots (start from every command line and tmux please )

Validation task 
1. trigger rate 
    have 20 trigger cases (10 should trigger and 10 should NOT trigger) and test in 12 train vs 8 test 
    optimize the trigger rate until it works 

2. optimize the triggered effects 
    for example : 
        Situation : alice and bob case from [text](insights-share/demo_docs/pm_walkthrough.md)
        Task : bob open the claude code , NOT asking for help , but just typing something about PostgreSQL and he 'may' got the same trap. 
        Action : after claude assitance last image was send , the claude code will trigger a haiku-agent to semantic search the insights-wiki and report the final cases. 
        Result : claude code review the issues 

        NOTES: the trigger should be 
                SLIENT_AND_JUST_RUN (optinal but not in this design : ASK_USER_APPROVAL, have a placehold but force default values to SLIENT_AND_JUST_RUN)
        
3. update wiki : 
    - one old wiki and one new wiki of same item :  merge as one 
    - NEVER forget , tagged as not triggerd 
    - add 
    - delete 
    - research 
    - edit 


4. wiki structure :
    wiki_type :
        general_python
        frontend_python
        ...
        database 
            INDEX.md
                items : | name | description | trigger when | docs to  {type}/*.md|
            postgres_并发_.md 
                full descriptions of the issues , bad examples (failed cases) and good examples ( good cases ), entry to {full_log}.jsonl or {full_export}.txt 
            postgres_内存.md
            postgres_硬盘读取io.md 

    IMPORTANT: MUST follow 4 layers strucrtures : 
        wiki_type_index => wiki type / type INDEX.md => wiki_item.md => raw log jsonl/txt 
    
5. MUST have agentic search wiki minimax 