---
{
  "id": "m1-zotero-mcp-2026-04-22",
  "title": "Zotero MCP 三工具降级链",
  "author": "m1",
  "confidence": 0.82,
  "tags": ["zotero", "MCP", "降级", "fallback", "search"],
  "status": "active",
  "applies_when": ["MCP server 连接失败", "zotero_search 不可用", "需要从 Zotero 库检索文献"],
  "do_not_apply_when": ["Zotero 未安装", "Zotero web API 未配置"],
  "topic_id": "tooling-patterns",
  "label": "good",
  "label_note": "zotero_search → zotero_get_item_metadata → zotero_search_notes 三级降级",
  "raw_log": null
}
---

# Zotero MCP 三工具降级链

> author: m1 · confidence: 0.82

## 降级路径

```
zotero_search_items    ← 首选语义搜索
  ↓ 失败/不可用
zotero_get_item_metadata    ← 查单条 metadata
  ↓ 失败/不可用
zotero_search_notes    ← 搜索笔记/annotations
```

## 触发条件

- MCP server 连接失败
- `No such tool available` 错误
- 网络隔离环境

## Error pattern 案例

```
No such tool available: zotero_search
→ 降级到 zotero_get_item_metadata by item_key
→ 仍失败 → zotero_search_notes
```

## Good usage

```python
try:
    result = zotero_search_items(query="LLM reasoning")
except:
    result = zotero_get_item_metadata(item_key="XXXX")
```

## Applies when

- MCP server 连接失败
- zotero_search 不可用
- 需要从 Zotero 库检索文献

## Do NOT apply when

- Zotero 未安装
- Zotero web API 未配置
