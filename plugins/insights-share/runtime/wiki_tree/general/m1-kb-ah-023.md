---
{
  "id": "m1-kb-ah-023",
  "title": "Project-Specific Knowledge",
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
  "label_note": "\n### paperclip-demo\n- `paperclipai` npm 包，本地 server 在 `http://127.0.0.1:3100`\n- 启动模式：embedded-postgres，local_trusted（仅 loopback）\n\n### pmcx-deeplearningV2\n- 工作目录：`.claude/worktrees/gpu-viz-implementation`\n- 数据集：IXI_MCX_paired（配对潜在空间数据）\n- 模型：VAE + RectifiedFlow\n- 输出：`results/real_metrics_summary.json`，`results/gpu_test_results.json`\n- 可视化 4 图：mip_comparison_real.png / slice_comparison_real.png / metrics_distribution_real.png / correlation_scatter_real.png\n\n### paper-review (Leidenfrost)\n- 研究框架：驱动源",
  "applies_when": [],
  "do_not_apply_when": []
}
---

# Project-Specific Knowledge

> author: m1 · confidence: 0.85


### paperclip-demo
- `paperclipai` npm 包，本地 server 在 `http://127.0.0.1:3100`
- 启动模式：embedded-postgres，local_trusted（仅 loopback）

### pmcx-deeplearningV2
- 工作目录：`.claude/worktrees/gpu-viz-implementation`
- 数据集：IXI_MCX_paired（配对潜在空间数据）
- 模型：VAE + RectifiedFlow
- 输出：`results/real_metrics_summary.json`，`results/gpu_test_results.json`
- 可视化 4 图：mip_comparison_real.png / slice_comparison_real.png / metrics_distribution_real.png / correlation_scatter_real.png

### paper-review (Leidenfrost)
- 研究框架：驱动源
