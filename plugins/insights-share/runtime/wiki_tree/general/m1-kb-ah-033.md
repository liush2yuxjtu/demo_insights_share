---
{
  "id": "m1-kb-ah-033",
  "title": "Error Patterns & Fixes",
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
  "label_note": "\n### Python Import Testing with Mocking\n- **Problem**: Scripts import torch/monai/etc which may not be installed\n- **Solution**: Create `MockModule` class with `__getattr__` returning MagicMock for any attribute access\n- **Key modules to mock**: torch (nn, optim, cuda, utils, optim.lr_scheduler), monai (transforms, data, networks, losses), fire, nibabel, ants, numpy, matplotlib\n- **Issue**: `torch.optim.lr_scheduler` submodule must be explicitly added\n- **Issue**: nibabel mock needs `Nifti1Image",
  "applies_when": [],
  "do_not_apply_when": []
}
---

# Error Patterns & Fixes

> author: m1 · confidence: 0.85


### Python Import Testing with Mocking
- **Problem**: Scripts import torch/monai/etc which may not be installed
- **Solution**: Create `MockModule` class with `__getattr__` returning MagicMock for any attribute access
- **Key modules to mock**: torch (nn, optim, cuda, utils, optim.lr_scheduler), monai (transforms, data, networks, losses), fire, nibabel, ants, numpy, matplotlib
- **Issue**: `torch.optim.lr_scheduler` submodule must be explicitly added
- **Issue**: nibabel mock needs `Nifti1Image
