---
{
  "id": "m1-kb-ai-005",
  "title": "4. Project-Specific Knowledge",
  "author": "m1",
  "confidence": 0.85,
  "tags": [
    "knowledge-extraction",
    "session-analysis",
    "group_ai"
  ],
  "status": "active",
  "topic_id": "m1-kb-ai",
  "label": "good",
  "label_note": "\n### 4.1 Eval-Harness Skill (EDD Framework)\n\n**Capability Evals**: Test if Claude can do something new\n```\n[CAPABILITY EVAL: feature-name]\nTask: Description\nSuccess Criteria:\n  - [ ] Criterion 1\nExpected Output: Description\n```\n\n**Regression Evals**: Ensure changes don't break existing functionality\n```\n[REGRESSION EVAL: feature-name]\nBaseline: SHA or checkpoint\nTests:\n  - existing-test-1: PASS/FAIL\nResult: X/Y passed (previously Y/Y)\n```\n\n**Grader Types**:\n- **Code grader**: Deterministic check",
  "applies_when": [],
  "do_not_apply_when": []
}
---

# 4. Project-Specific Knowledge

> author: m1 · confidence: 0.85


### 4.1 Eval-Harness Skill (EDD Framework)

**Capability Evals**: Test if Claude can do something new
```
[CAPABILITY EVAL: feature-name]
Task: Description
Success Criteria:
  - [ ] Criterion 1
Expected Output: Description
```

**Regression Evals**: Ensure changes don't break existing functionality
```
[REGRESSION EVAL: feature-name]
Baseline: SHA or checkpoint
Tests:
  - existing-test-1: PASS/FAIL
Result: X/Y passed (previously Y/Y)
```

**Grader Types**:
- **Code grader**: Deterministic check
