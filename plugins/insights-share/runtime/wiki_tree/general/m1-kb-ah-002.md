---
{
  "id": "m1-kb-ah-002",
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
  "label_note": "\n- **Qwen OAuth PKCE Implementation**: Project uses Proof Key for Code Exchange (PKCE) with Qwen OAuth Device Code Flow for secure authentication\n- **PKCE Key Functions**: `generatePKCE()` creates verifier (43 chars) + challenge (SHA-256); `verifyPKCE()` validates the pair; `loginQwen()` is main flow; `refreshQwenToken()` handles token refresh; `startDeviceFlow()` initiates device flow; `pollForToken()` polls for token\n- **Four Testing Tiers**: Unit (15+ tests) → Contract (13 tests) → E2E (7 tes",
  "applies_when": [],
  "do_not_apply_when": []
}
---

# Technical Findings & Patterns

> author: m1 · confidence: 0.85


- **Qwen OAuth PKCE Implementation**: Project uses Proof Key for Code Exchange (PKCE) with Qwen OAuth Device Code Flow for secure authentication
- **PKCE Key Functions**: `generatePKCE()` creates verifier (43 chars) + challenge (SHA-256); `verifyPKCE()` validates the pair; `loginQwen()` is main flow; `refreshQwenToken()` handles token refresh; `startDeviceFlow()` initiates device flow; `pollForToken()` polls for token
- **Four Testing Tiers**: Unit (15+ tests) → Contract (13 tests) → E2E (7 tes
