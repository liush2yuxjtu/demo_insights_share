---
{
  "id": "m1-kb-ah-026",
  "title": "Technical Findings & Patterns",
  "author": "m1",
  "confidence": 0.85,
  "tags": [
    "knowledge-extraction",
    "session-analysis",
    "group_ah"
  ],
  "status": "active",
  "topic_id": "m1-kb-ah",
  "label": "good",
  "label_note": "\n### HPC GPU Usage Patterns\n- **Direct run**: `srun --gres=gpu:1 --cpus-per-gpu=8 --mem-per-gpu=8000M --time=1:00:00 /data/home/syliu/.conda/envs/liushiyu/bin/python your_script.py`\n- **Alloc then run**: `salloc --gres=gpu:1 --cpus-per-gpu=8 --mem-per-gpu=8000M --time=1:00:00 --no-shell sleep 3600 &` → get JOBID → `srun --jobid=JOBID your_command`\n- **Node restriction**: `-w node4` or `-w node2` (avoid node1, it's login node)\n- **InvalidAccount**: Cluster bug = waiting for resources, not actual ",
  "applies_when": [],
  "do_not_apply_when": []
}
---

# Technical Findings & Patterns

> author: m1 · confidence: 0.85


### HPC GPU Usage Patterns
- **Direct run**: `srun --gres=gpu:1 --cpus-per-gpu=8 --mem-per-gpu=8000M --time=1:00:00 /data/home/syliu/.conda/envs/liushiyu/bin/python your_script.py`
- **Alloc then run**: `salloc --gres=gpu:1 --cpus-per-gpu=8 --mem-per-gpu=8000M --time=1:00:00 --no-shell sleep 3600 &` → get JOBID → `srun --jobid=JOBID your_command`
- **Node restriction**: `-w node4` or `-w node2` (avoid node1, it's login node)
- **InvalidAccount**: Cluster bug = waiting for resources, not actual
