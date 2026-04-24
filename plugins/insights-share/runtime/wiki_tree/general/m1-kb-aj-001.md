---
{
  "id": "m1-kb-aj-001",
  "title": "Technical Findings",
  "author": "m1",
  "confidence": 0.85,
  "tags": [
    "knowledge-extraction",
    "session-analysis",
    "group_aj"
  ],
  "status": "active",
  "topic_id": "m1-kb-aj",
  "label": "good",
  "label_note": "\n- FP16 precision alignment fix in autoencoder inference harness (1525b7a commit)\n- normalize_paths redundant O(n log n) sort in build_scope - called multiple times\n- ScopeSummary has_protected_scope should be @property not stored field\n- repo_lint_harness.py has redundant state storage (ScopeSummary + write_marker duplication)\n- TOCTOU race condition in load_marker - should use try/except instead of exists+open\n- Shell injection vulnerability in remote_preflight.py - shell=True misused\n- torch.",
  "applies_when": [],
  "do_not_apply_when": []
}
---

# Technical Findings

> author: m1 · confidence: 0.85


- FP16 precision alignment fix in autoencoder inference harness (1525b7a commit)
- normalize_paths redundant O(n log n) sort in build_scope - called multiple times
- ScopeSummary has_protected_scope should be @property not stored field
- repo_lint_harness.py has redundant state storage (ScopeSummary + write_marker duplication)
- TOCTOU race condition in load_marker - should use try/except instead of exists+open
- Shell injection vulnerability in remote_preflight.py - shell=True misused
- torch.
