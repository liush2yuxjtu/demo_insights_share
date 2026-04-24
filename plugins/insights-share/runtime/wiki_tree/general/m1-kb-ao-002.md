---
{
  "id": "m1-kb-ao-002",
  "title": "2. SSH / Remote Server 连接",
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
  "label_note": "\n### 典型场景\n- 远程服务器探索（myserver）\n- SSH 密钥认证问题排查\n- 远程 HPC 环境检查\n\n### 常见问题模式\n```\nPermission denied (publickey)\n```\n\n### 排查步骤\n1. `ping -c 3 <host>` - 检查主机可达性\n2. `nc -zv <host> 22` - 检查端口开放\n3. `ssh -vvv -o ConnectTimeout=10 <host> exit` - 详细调试连接\n4. 检查 SSH 配置（`~/.ssh/config`）\n5. 验证公钥是否在远程服务器 `authorized_keys` 中\n\n### SSH 配置示例\n```\nHost myserver\n    HostName 10.110.147.41\n    User syliu\n    IdentityFile ~/.ssh/id_rsa\n```\n\n### 关键发现\n- 远程探索 agent 只能通过 SSH 命令操作远程服务器\n- 密钥存在但未被服务器授权是常见失败原因\n- 远程服务器通常是 Ubuntu 22.04",
  "applies_when": [],
  "do_not_apply_when": []
}
---

# 2. SSH / Remote Server 连接

> author: m1 · confidence: 0.85


### 典型场景
- 远程服务器探索（myserver）
- SSH 密钥认证问题排查
- 远程 HPC 环境检查

### 常见问题模式
```
Permission denied (publickey)
```

### 排查步骤
1. `ping -c 3 <host>` - 检查主机可达性
2. `nc -zv <host> 22` - 检查端口开放
3. `ssh -vvv -o ConnectTimeout=10 <host> exit` - 详细调试连接
4. 检查 SSH 配置（`~/.ssh/config`）
5. 验证公钥是否在远程服务器 `authorized_keys` 中

### SSH 配置示例
```
Host myserver
    HostName 10.110.147.41
    User syliu
    IdentityFile ~/.ssh/id_rsa
```

### 关键发现
- 远程探索 agent 只能通过 SSH 命令操作远程服务器
- 密钥存在但未被服务器授权是常见失败原因
- 远程服务器通常是 Ubuntu 22.04
