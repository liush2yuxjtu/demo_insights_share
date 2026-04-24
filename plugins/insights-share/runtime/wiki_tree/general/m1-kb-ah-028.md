---
{
  "id": "m1-kb-ah-028",
  "title": "CLI Commands & Tools",
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
  "label_note": "\n### HPC Monitoring\n```bash\nssh myserver \"squeue -u syliu\"                                    # Check job status\nssh myserver \"find /data1/syliu/ixi_charm_output -name 'tissue_labeling_upsampled.nii.gz' | wc -l\"  # CHARM completed\nssh myserver \"find /data1/syliu/ixi_final_tissues -name '*.nii.gz' | wc -l\"  # MCX-ready output count\nssh myserver \"ls /data1/syliu/ixi_final_tissues/ 2>/dev/null | wc -l\"        # Quick count\n```\n\n### HPC SSH Access\n```bash\nssh syliu@10.110.147.41                     ",
  "applies_when": [],
  "do_not_apply_when": []
}
---

# CLI Commands & Tools

> author: m1 · confidence: 0.85


### HPC Monitoring
```bash
ssh myserver "squeue -u syliu"                                    # Check job status
ssh myserver "find /data1/syliu/ixi_charm_output -name 'tissue_labeling_upsampled.nii.gz' | wc -l"  # CHARM completed
ssh myserver "find /data1/syliu/ixi_final_tissues -name '*.nii.gz' | wc -l"  # MCX-ready output count
ssh myserver "ls /data1/syliu/ixi_final_tissues/ 2>/dev/null | wc -l"        # Quick count
```

### HPC SSH Access
```bash
ssh syliu@10.110.147.41
