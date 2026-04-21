# 编辑即原子 commit

## 规则

任意 Write / Edit / 文件移动 / 文件删除操作完成后，**立即**按单一关注点执行原子 git commit。禁止累积多个无关变更到同一 commit。

## 触发时机

- 每次 Write 调用完成后
- 每次 Edit 调用完成后
- 每次 `git mv` / `mv` / `rm` 文件操作后
- 每次用 Bash 批量改文件后

## 原子 commit 定义

一个 commit 只做一件事：

- 一次重命名 = 一个 commit
- 一次规则新增 = 一个 commit
- 一次索引更新 = 一个 commit
- 不把"移动文件 + 改规则 + 改索引"塞进同一 commit

## 执行模板

```bash
git add <具体文件列表>
git commit -m "$(cat <<'EOF'
<type>: <单一关注点描述>

<可选 why / 关联规则>
EOF
)"
```

禁止:

- `git add -A` / `git add .`（可能带入 .env / 大文件）
- `git commit --amend` 覆盖已推送 commit（除非用户显式授权）
- 跳过 hook（`--no-verify`）

## 例外

- 纯阅读 / 纯 Bash 查询不触发 commit
- 用户显式说"先不 commit"时暂缓，但必须在任务收尾统一分原子 commit

## Why

- 回滚粒度可控：坏改动只回退它自己
- history 可读：每条 log 对应一个意图
- review 友好：diff 聚焦单一关注点
