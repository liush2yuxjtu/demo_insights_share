---
{
  "id": "m1-default-sanitization-2026-04-22",
  "title": "日志/JSON 输出默认脱敏",
  "author": "m1",
  "confidence": 0.9,
  "tags": ["sanitization", "json", "logging", "security", "PII"],
  "status": "active",
  "applies_when": ["日志包含用户数据", "JSON 输出可能被外部系统存储", "交付物含真实数据"],
  "do_not_apply_when": ["明确脱敏会影响功能（如加索引需要真实值）", "测试数据已确认无 PII"],
  "topic_id": "security-patterns",
  "label": "good",
  "label_note": "日志默认脱敏三件套：手机号/邮箱/ID 替换为占位符",
  "raw_log": null
}
---

# 日志/JSON 输出默认脱敏

> author: m1 · confidence: 0.9

## 脱敏规则

| 类型 | 脱敏后 |
|------|--------|
| 手机号 | `138****5678` |
| 邮箱 | `u***@example.com` |
| 内部 ID | `ID: <redacted>` |
| 真实路径 | `/Users/***/project` |

## 默认原则

- 日志/输出/交付物含真实用户数据时，必须脱敏
- 即使内部系统也默认脱敏（防止意外外泄）
- 脱敏影响功能时，明确标注并让用户决定

## Good log format

```json
{
  "user_id": "<redacted>",
  "email": "u***@company.com",
  "phone": "138****5678",
  "action": "file_deleted",
  "path": "/project/***/target"
}
```

## Bad example

```json
// ❌ 真实数据直接写日志
{"user_id": 998271, "email": "john.doe@company.com", "phone": "13901234567"}
```

## Applies when

- 日志包含用户数据
- JSON 输出可能被外部系统存储
- 交付物含真实数据

## Do NOT apply when

- 明确脱敏会影响功能（如加索引需要真实值）
- 测试数据已确认无 PII
