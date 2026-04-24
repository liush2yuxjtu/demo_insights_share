---
{
  "id": "m1-kb-ah-024",
  "title": "Actionable Insights",
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
  "label_note": "\n1. **Zotero MCP 不可用时**：立即切换到 BibTeX/NBIB 手动导出，不要阻塞等待\n2. **codex CPU 暴涨时**：先 `ps -Ao pid,pcpu,comm -r` 确认进程再杀，避免误杀\n3. **多 agent 任务依赖**：用轮询 TaskList 而非 sleep，等待时输出当前状态\n4. **HPC 远程执行**：需先 git pull 更新代码，再跑 GPU 测试脚本\n5. **GPU 测试 pass 标准**：PSNR > 30 dB 且 SSIM > 0.9，不满足则需调优模型或数据\n\n\n================================================================================",
  "applies_when": [],
  "do_not_apply_when": []
}
---

# Actionable Insights

> author: m1 · confidence: 0.85


1. **Zotero MCP 不可用时**：立即切换到 BibTeX/NBIB 手动导出，不要阻塞等待
2. **codex CPU 暴涨时**：先 `ps -Ao pid,pcpu,comm -r` 确认进程再杀，避免误杀
3. **多 agent 任务依赖**：用轮询 TaskList 而非 sleep，等待时输出当前状态
4. **HPC 远程执行**：需先 git pull 更新代码，再跑 GPU 测试脚本
5. **GPU 测试 pass 标准**：PSNR > 30 dB 且 SSIM > 0.9，不满足则需调优模型或数据


================================================================================
