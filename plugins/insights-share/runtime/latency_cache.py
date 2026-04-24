"""search_agent 结果级缓存（M6 O1）。

纯函数 + 磁盘原子写；wiki_tree 更新会自动失效 cache。
对齐 proposal_generation_latency.md §Optimization O1 / §Self-verify。
"""

from __future__ import annotations

import hashlib
import json
import os
import pathlib
from datetime import datetime, timezone
from pathlib import Path

# 默认缓存目录；~/.cache/insights-share/hits/
CACHE_DIR_DEFAULT: Path = Path("~/.cache/insights-share/hits").expanduser()


def compute_wiki_sha(wiki_tree_root: pathlib.Path) -> str:
    """对 wiki_tree 算稳定短 sha。

    只看两类关键状态：每个 category 的 INDEX.md mtime + topics.json 字节。
    任一变动，sha 变，cache 自动失效。
    """
    root = Path(wiki_tree_root)
    h = hashlib.sha1()

    # 1) 所有 <category>/INDEX.md 的 (相对路径, mtime_ns)
    index_files = sorted(root.glob("*/INDEX.md"))
    for p in index_files:
        rel = p.relative_to(root).as_posix()
        try:
            mtime_ns = p.stat().st_mtime_ns
        except FileNotFoundError:
            continue
        h.update(rel.encode("utf-8"))
        h.update(b"\0")
        h.update(str(mtime_ns).encode("ascii"))
        h.update(b"\n")

    # 2) topics.json 字节
    topics_json = root / "topics.json"
    if topics_json.exists():
        h.update(b"topics.json\0")
        h.update(topics_json.read_bytes())

    return h.hexdigest()[:12]


def cache_key(query: str, wiki_sha: str) -> str:
    """query + wiki_sha 的 sha1 前 16 位 hex。"""
    blob = f"{query}\0{wiki_sha}".encode("utf-8")
    return hashlib.sha1(blob).hexdigest()[:16]


def _cache_path(cache_dir: Path, key: str) -> Path:
    return Path(cache_dir) / f"{key}.json"


def _utc_now_z() -> str:
    """ISO8601 UTC with Z suffix."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load(
    query: str,
    wiki_sha: str,
    cache_dir: Path = CACHE_DIR_DEFAULT,
    ttl_seconds: int = 300,
) -> dict | None:
    """命中且未过期返回 hits dict；否则返回 None。

    miss / 过期 / 损坏均静默返回 None（cache 仅是加速层，不抛）。
    底层 search_agent / IO 异常仍会从 store() 或 caller 冒出。
    """
    key = cache_key(query, wiki_sha)
    path = _cache_path(Path(cache_dir), key)
    if not path.exists():
        return None

    # TTL：用 mtime 判过期；过期就当 miss
    try:
        age = (os.stat(path).st_mtime_ns) / 1e9
    except FileNotFoundError:
        return None
    now = datetime.now(timezone.utc).timestamp()
    if now - age > ttl_seconds:
        return None

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None

    # 校验 wiki_sha 一致，防 wiki 变更后读到旧缓存
    if payload.get("wiki_sha") != wiki_sha:
        return None

    hits = payload.get("hits")
    if not isinstance(hits, dict):
        return None
    return hits


def store(
    query: str,
    wiki_sha: str,
    hits: dict,
    cache_dir: Path = CACHE_DIR_DEFAULT,
) -> Path:
    """原子写 cache：tmp + rename。

    payload schema: {"query","wiki_sha","ts","hits"}
    返回落盘路径。
    """
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)

    key = cache_key(query, wiki_sha)
    path = _cache_path(cache_dir, key)
    tmp = path.with_suffix(path.suffix + ".tmp")

    payload = {
        "query": query,
        "wiki_sha": wiki_sha,
        "ts": _utc_now_z(),
        "hits": hits,
    }
    tmp.write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    os.replace(tmp, path)
    return path


def cached_search(
    query: str,
    wiki_tree_root: pathlib.Path,
    runner,
    ttl_seconds: int = 300,
    cache_dir: Path = CACHE_DIR_DEFAULT,
) -> tuple[dict, bool]:
    """带 cache 的 search 包装。

    runner: callable(query, wiki_tree_root) -> dict，通常是 search_agent.run。
    返回 (hits, was_cache_hit)。
    runner 抛错会直接冒出去（对齐项目规则：严禁 fallback）。
    """
    wiki_sha = compute_wiki_sha(wiki_tree_root)
    cached = load(query, wiki_sha, cache_dir=cache_dir, ttl_seconds=ttl_seconds)
    if cached is not None:
        return cached, True

    hits = runner(query, wiki_tree_root)
    if not isinstance(hits, dict):
        raise TypeError(
            f"runner must return dict, got {type(hits).__name__}"
        )
    store(query, wiki_sha, hits, cache_dir=cache_dir)
    return hits, False


__all__ = [
    "CACHE_DIR_DEFAULT",
    "compute_wiki_sha",
    "cache_key",
    "load",
    "store",
    "cached_search",
]
