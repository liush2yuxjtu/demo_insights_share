---
{
  "id": "m1-kb-aa-001",
  "title": "1. Agent Teams 架构与 Timeout 纪律",
  "author": "m1",
  "confidence": 0.85,
  "tags": [
    "knowledge-extraction",
    "session-analysis",
    "group_aa"
  ],
  "status": "active",
  "topic_id": "m1-kb-aa",
  "label": "good",
  "label_note": "\n### 角色链\n- **Manager** → 监督team结构与timeout纪律，不直接产出最终HTML\n- **Builder** → 读取 spec 文件，执行阶段1（设计说明）和阶段2（实现）\n- **Verifier** → 读取产物，执行 KEEP/RESET 判断\n\n### Timeout 配置（endless-live 场景）\n| 角色 | Timeout |\n|------|---------|\n| manager | 360s |\n| builder | 300s |\n| verifier | 90s |\n\n### KEEP/RESET 语义（demo2_program 场景）\n**KEEP条件（全部满足）：**\n1. 文件存在且语法正确（HTML可解析）\n2. 包含 level editor（格子地图编辑）\n3. 包含 sprite editor（像素画编辑）\n4. 包含 entity behaviors（实体行为配置）\n5. 包含 playable test mode（可切换到游戏测试模式并运行）\n6. 纯 HTML/CSS/JS，无外部框架依赖\n7. 所有",
  "applies_when": [],
  "do_not_apply_when": []
}
---

# 1. Agent Teams 架构与 Timeout 纪律

> author: m1 · confidence: 0.85


### 角色链
- **Manager** → 监督team结构与timeout纪律，不直接产出最终HTML
- **Builder** → 读取 spec 文件，执行阶段1（设计说明）和阶段2（实现）
- **Verifier** → 读取产物，执行 KEEP/RESET 判断

### Timeout 配置（endless-live 场景）
| 角色 | Timeout |
|------|---------|
| manager | 360s |
| builder | 300s |
| verifier | 90s |

### KEEP/RESET 语义（demo2_program 场景）
**KEEP条件（全部满足）：**
1. 文件存在且语法正确（HTML可解析）
2. 包含 level editor（格子地图编辑）
3. 包含 sprite editor（像素画编辑）
4. 包含 entity behaviors（实体行为配置）
5. 包含 playable test mode（可切换到游戏测试模式并运行）
6. 纯 HTML/CSS/JS，无外部框架依赖
7. 所有
