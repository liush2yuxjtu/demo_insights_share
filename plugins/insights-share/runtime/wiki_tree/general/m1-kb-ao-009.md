---
{
  "id": "m1-kb-ao-009",
  "title": "8. HPC / GPU 使用",
  "author": "m1",
  "confidence": 0.85,
  "tags": [
    "knowledge-extraction",
    "session-analysis",
    "group_ao"
  ],
  "status": "active",
  "topic_id": "m1-kb-ao",
  "label": "good",
  "label_note": "\n### 典型规则\n```markdown\nIMPORTANT: HPC, Use assigned GPU to temporarily test GPU codes best practice is : ...\n```\n\n### 常用监控\n```bash\n# GPU 使用率收集\n./check_gpu_usage.sh\n```\n\n### 关键发现\n- 支持多类型 GPU：titan xp, titan, rtx3090, a100 等\n- 非 Git 相关任务也可以在 HPC 上执行（如多配置 GPU 训练）\n\n---",
  "applies_when": [],
  "do_not_apply_when": []
}
---

# 8. HPC / GPU 使用

> author: m1 · confidence: 0.85


### 典型规则
```markdown
IMPORTANT: HPC, Use assigned GPU to temporarily test GPU codes best practice is : ...
```

### 常用监控
```bash
# GPU 使用率收集
./check_gpu_usage.sh
```

### 关键发现
- 支持多类型 GPU：titan xp, titan, rtx3090, a100 等
- 非 Git 相关任务也可以在 HPC 上执行（如多配置 GPU 训练）

---
