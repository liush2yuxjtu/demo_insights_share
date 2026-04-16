"""Topic 相关功能的单元测试：TreeInsightStore."""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

import pytest

from insightsd.store import TreeInsightStore


@pytest.fixture
def store(tmp_path: Path) -> TreeInsightStore:
    """在临时目录初始化一个干净的 TreeInsightStore."""
    shutil.copytree(
        Path(__file__).resolve().parents[1] / "demo_codes" / "wiki_tree",
        tmp_path / "wiki_tree",
    )
    return TreeInsightStore(tmp_path / "wiki_tree")


class TestTopicStore:
    def test_topic_create_and_list(self, store: TreeInsightStore) -> None:
        """create_topic 后 list_topics 能返回新建的 topic."""
        topic = {
            "id": "test-topic-1",
            "title": "Test Topic",
            "tags": ["test"],
            "created_by": "tester",
            "created_at": "2026-04-15T00:00:00Z",
        }
        result = store.create_topic(topic)
        assert result["id"] == "test-topic-1"

        topics = store.list_topics()
        assert any(t["id"] == "test-topic-1" for t in topics)

    def test_topic_idempotent(self, store: TreeInsightStore) -> None:
        """重复 create_topic 幂等，不报错."""
        topic = {
            "id": "dup-topic",
            "title": "Dup",
            "tags": [],
            "created_by": "tester",
        }
        store.create_topic(topic)
        store.create_topic(topic)  # 不抛异常

        topics = store.list_topics()
        assert sum(1 for t in topics if t["id"] == "dup-topic") == 1

    def test_publish_example_with_topic_id_persists_label(self, store: TreeInsightStore) -> None:
        """add card 带 topic_id 时，label 字段被正确写入 md."""
        card = {
            "id": "test-card-topic-1",
            "title": "Card with Topic",
            "author": "tester",
            "confidence": 0.8,
            "tags": ["test"],
            "topic_id": "test-topic-xy",
            "label": "good",
            "raw_log_type": "jsonl",
            "context": "test context",
            "symptom": "test symptom",
            "fix": "test fix",
        }
        store.add(card, wiki_type="general")

        # 重新加载验证
        cards = store.load()
        found = next((c for c in cards if c["id"] == "test-card-topic-1"), None)
        assert found is not None
        assert found["topic_id"] == "test-topic-xy"
        assert found["label"] == "good"

    def test_list_examples_by_label_filters_correctly(self, store: TreeInsightStore) -> None:
        """list_examples(topic_id, label=...) 能正确过滤 good/bad."""
        # 先创建一个带 topic_id 的测试 topic 和 card
        topic = {
            "id": "test-filter-topic",
            "title": "Filter Test Topic",
            "tags": ["test"],
            "created_by": "tester",
        }
        store.create_topic(topic)

        # 创建两个 label 不同的 card，都指向同一 topic
        card_good = {
            "id": "test-filter-good",
            "title": "Good Example",
            "author": "tester",
            "confidence": 0.8,
            "tags": ["test"],
            "topic_id": "test-filter-topic",
            "label": "good",
            "raw_log_type": "jsonl",
            "context": "ctx",
            "symptom": "sym",
            "fix": "fix",
        }
        card_bad = {
            "id": "test-filter-bad",
            "title": "Bad Example",
            "author": "tester",
            "confidence": 0.8,
            "tags": ["test"],
            "topic_id": "test-filter-topic",
            "label": "bad",
            "raw_log_type": "jsonl",
            "context": "ctx",
            "symptom": "sym",
            "fix": "fix",
        }
        store.add(card_good, wiki_type="general")
        store.add(card_bad, wiki_type="general")

        all_examples = store.list_examples("test-filter-topic")
        assert len(all_examples) == 2

        good_examples = store.list_examples("test-filter-topic", label="good")
        bad_examples = store.list_examples("test-filter-topic", label="bad")
        assert len(good_examples) == 1
        assert len(bad_examples) == 1
        assert good_examples[0]["effective_label"] == "good"
        assert bad_examples[0]["effective_label"] == "bad"

    def test_relabel_sets_override_fields_preserves_raw_log(self, store: TreeInsightStore) -> None:
        """relabel 只修改 override 字段，不碰 raw_log."""
        card_id = "alice-pgpool-2026-04-10"
        original_cards = store.load()
        orig_card = next((c for c in original_cards if c["id"] == card_id), None)
        assert orig_card is not None
        orig_raw_log = orig_card.get("raw_log", "")

        result = store.relabel(card_id, "bad", "admin")
        assert result is not None
        assert result["label_override"] == "bad"
        assert result["label_override_by"] == "admin"
        assert result["label_override_at"] is not None
        assert result["raw_log"] == orig_raw_log  # raw_log 未变

    def test_effective_label_in_search_results(self, store: TreeInsightStore) -> None:
        """search 返回的卡片包含 effective_label 字段."""
        hits = store.search("postgres", k=3)
        assert len(hits) > 0
        for hit in hits:
            assert "effective_label" in hit
            # effective_label = label_override or label
            expected = hit.get("label_override") or hit.get("label", "good")
            assert hit["effective_label"] == expected

    def test_raw_log_txt_written_for_export_type(self, tmp_path: Path) -> None:
        """raw_log_type=export 时 raw 目录写入 .txt，内容为 raw_log_export_content."""
        store = TreeInsightStore(tmp_path / "wiki_tree")
        (tmp_path / "wiki_tree").mkdir(parents=True)

        card = {
            "id": "test-export-card",
            "title": "Export Test Card",
            "author": "tester",
            "confidence": 0.7,
            "tags": ["test"],
            "topic_id": "test-topic",
            "label": "good",
            "raw_log_type": "export",
            "raw_log_export_content": "原始日志行1\n原始日志行2\n",
            "context": "ctx",
            "symptom": "sym",
            "fix": "fix",
        }
        store.add(card, wiki_type="general")

        raw_txt = tmp_path / "wiki_tree" / "general" / "raw" / "test-export-card.txt"
        assert raw_txt.exists()
        content = raw_txt.read_text(encoding="utf-8")
        assert "原始日志行1" in content

    def test_raw_log_jsonl_copied_verbatim_for_jsonl_type(self, tmp_path: Path) -> None:
        """raw_log_type=jsonl（默认）时写入 .jsonl，内容为卡片字段 JSON."""
        store = TreeInsightStore(tmp_path / "wiki_tree")
        (tmp_path / "wiki_tree").mkdir(parents=True)

        card = {
            "id": "test-jsonl-card",
            "title": "JSONL Test Card",
            "author": "tester",
            "confidence": 0.7,
            "tags": ["test"],
            "topic_id": "test-topic",
            "label": "good",
            "raw_log_type": "jsonl",
            "context": "ctx",
            "symptom": "sym",
            "fix": "fix",
        }
        store.add(card, wiki_type="general")

        raw_jsonl = tmp_path / "wiki_tree" / "general" / "raw" / "test-jsonl-card.jsonl"
        assert raw_jsonl.exists()
        lines = raw_jsonl.read_text(encoding="utf-8").splitlines()
        assert len(lines) == 1
        parsed = json.loads(lines[0])
        assert parsed["id"] == "test-jsonl-card"
        assert "wiki_type" not in parsed  # raw 中不含 wiki_type

    def test_legacy_card_without_new_fields_still_readable(self, store: TreeInsightStore) -> None:
        """老卡片（无 topic_id/label/raw_log_type）能被正常加载，不抛异常."""
        cards = store.load()
        assert len(cards) > 0
        # 每个卡片至少有 id
        for card in cards:
            assert card.get("id")
            # topic_id 默认应有值
            assert "topic_id" in card
