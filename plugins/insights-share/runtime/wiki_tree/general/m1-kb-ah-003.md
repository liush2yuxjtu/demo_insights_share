---
{
  "id": "m1-kb-ah-003",
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
  "label_note": "\n- **TypeScript JSON Parsing Error**: Response casting issues with `response.json()` → Fix: Use `as DeviceCodeResponse` and `as Partial<TokenResponse & { error?: string; error_description?: string }>` casting\n- **Token Refresh Validation**: Missing access_token check on refresh → Fix: Added `if (!data.access_token) throw new Error(...)` validation\n- **OAuth Response Handling**: Need to check both `response.ok` AND token presence → Fix: Added `if (response.ok && data.access_token)` dual validatio",
  "applies_when": [],
  "do_not_apply_when": []
}
---

# Error Patterns & Fixes

> author: m1 · confidence: 0.85


- **TypeScript JSON Parsing Error**: Response casting issues with `response.json()` → Fix: Use `as DeviceCodeResponse` and `as Partial<TokenResponse & { error?: string; error_description?: string }>` casting
- **Token Refresh Validation**: Missing access_token check on refresh → Fix: Added `if (!data.access_token) throw new Error(...)` validation
- **OAuth Response Handling**: Need to check both `response.ok` AND token presence → Fix: Added `if (response.ok && data.access_token)` dual validatio
