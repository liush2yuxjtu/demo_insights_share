---
{
  "id": "m1-kb-ah-032",
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
  "label_note": "\n### Scientific Visualization Design (Medical Imaging)\n- **Perceptually uniform colormaps**: Use `viridis` (CVD-safe), `magma` (sequential, emphasizes high errors), `coolwarm` (diverging, centered at zero)\n- **Colorblind-safe palette**: Red=Simple, Green=DL, Blue=Full\n- **Error visualization principle**: Dark=good (low error), Bright=bad (high error)\n- **Light source focus**: 30×30×30mm zoom window where signal is strongest\n- **Reference**: Nature Scientific Reports best practices for violin vs ",
  "applies_when": [],
  "do_not_apply_when": []
}
---

# Technical Findings & Patterns

> author: m1 · confidence: 0.85


### Scientific Visualization Design (Medical Imaging)
- **Perceptually uniform colormaps**: Use `viridis` (CVD-safe), `magma` (sequential, emphasizes high errors), `coolwarm` (diverging, centered at zero)
- **Colorblind-safe palette**: Red=Simple, Green=DL, Blue=Full
- **Error visualization principle**: Dark=good (low error), Bright=bad (high error)
- **Light source focus**: 30×30×30mm zoom window where signal is strongest
- **Reference**: Nature Scientific Reports best practices for violin vs
