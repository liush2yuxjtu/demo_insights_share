---
{
  "id": "m1-kb-ah-034",
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
  "label_note": "\n### HPC Environment Setup\n```bash\nexport PYTHONPATH=/data1/syliu/reflow_monai\nsource /data/home/syliu/.conda/bin/activate liushiyu\ncd /data1/syliu/reflow_monai\n```\n\n### File Search on HPC\n```bash\nssh syliu@10.110.147.41 \"find /data1/syliu -name '*IXI012*' -type f 2>/dev/null | grep -E '(T1|tissue|final_tissues)'\"\n```\n\n### Python Testing\n```bash\n# Run all example validation tests\npython -m pytest tests/test_examples_*.py -v\n\n# Run specific test file\npython -m pytest tests/test_examples_syntax.py",
  "applies_when": [],
  "do_not_apply_when": []
}
---

# CLI Commands & Tools

> author: m1 · confidence: 0.85


### HPC Environment Setup
```bash
export PYTHONPATH=/data1/syliu/reflow_monai
source /data/home/syliu/.conda/bin/activate liushiyu
cd /data1/syliu/reflow_monai
```

### File Search on HPC
```bash
ssh syliu@10.110.147.41 "find /data1/syliu -name '*IXI012*' -type f 2>/dev/null | grep -E '(T1|tissue|final_tissues)'"
```

### Python Testing
```bash
# Run all example validation tests
python -m pytest tests/test_examples_*.py -v

# Run specific test file
python -m pytest tests/test_examples_syntax.py
