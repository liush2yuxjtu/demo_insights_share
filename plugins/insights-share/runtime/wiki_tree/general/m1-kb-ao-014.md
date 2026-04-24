---
{
  "id": "m1-kb-ao-014",
  "title": "11. 错误模式",
  "author": "m1",
  "confidence": 0.85,
  "tags": [
    "knowledge-extraction",
    "session-analysis",
    "group_ao"
  ],
  "status": "active",
  "topic_id": "m1-kb-ao",
  "label": "good",
  "label_note": "\n### 常见错误\n1. **SSH 认证失败**: 公钥未在远程服务器授权\n2. **Fish shell 不存在**: `bash: /opt/homebrew/bin/fish: No such file or directory`\n3. **Stale file handle**: NFS 挂载问题（`df: /data5: Stale file handle`）\n\n### 排查方法\n- 验证文件存在性\n- 检查文件权限（600 for SSH keys）\n- 使用 `ssh -vvv` 详细调试\n\n---",
  "applies_when": [],
  "do_not_apply_when": []
}
---

# 11. 错误模式

> author: m1 · confidence: 0.85


### 常见错误
1. **SSH 认证失败**: 公钥未在远程服务器授权
2. **Fish shell 不存在**: `bash: /opt/homebrew/bin/fish: No such file or directory`
3. **Stale file handle**: NFS 挂载问题（`df: /data5: Stale file handle`）

### 排查方法
- 验证文件存在性
- 检查文件权限（600 for SSH keys）
- 使用 `ssh -vvv` 详细调试

---
