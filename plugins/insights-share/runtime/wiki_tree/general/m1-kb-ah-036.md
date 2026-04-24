---
{
  "id": "m1-kb-ah-036",
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
  "label_note": "\n1. **Mocking strategy for dependency-light testing**: When testing scripts that require heavy dependencies (torch, monai), use `MagicMock` with recursive attribute handling instead of skipping tests with `pytest.importorskip`\n\n2. **Perceptual colormap selection**: For scientific visualization, always prefer perceptually uniform colormaps (viridis, magma) over rainbow/jet; CVD-safe options exist\n\n3. **Lazy evaluation in transforms**: MONAI's Compose supports lazy evaluation to minimize resamplin",
  "applies_when": [],
  "do_not_apply_when": []
}
---

# Actionable Insights

> author: m1 · confidence: 0.85


1. **Mocking strategy for dependency-light testing**: When testing scripts that require heavy dependencies (torch, monai), use `MagicMock` with recursive attribute handling instead of skipping tests with `pytest.importorskip`

2. **Perceptual colormap selection**: For scientific visualization, always prefer perceptually uniform colormaps (viridis, magma) over rainbow/jet; CVD-safe options exist

3. **Lazy evaluation in transforms**: MONAI's Compose supports lazy evaluation to minimize resamplin
