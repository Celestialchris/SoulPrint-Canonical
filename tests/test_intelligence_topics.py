"""Tests for cross-conversation topic detection."""

from __future__ import annotations

import unittest
from dataclasses import dataclass

from src.intelligence.provider import StubProvider
from src.intelligence.topics import TopicScan, extract_topics


@dataclass
class FakeMessage:
    role: str
    content: str
    sequence_index: int


@dataclass
class FakeConversation:
    id: int
    title: str
    messages: list


class ExtractTopicsWithStubTest(unittest.TestCase):
    def setUp(self):
        self.conversations = [
            FakeConversation(
                id=1,
                title="Python development tips",
                messages=[FakeMessage("user", "How do I use decorators?", 0)],
            ),
            FakeConversation(
                id=2,
                title="Python testing best practices",
                messages=[FakeMessage("user", "What testing framework?", 0)],
            ),
            FakeConversation(
                id=3,
                title="Travel planning for Europe",
                messages=[FakeMessage("user", "Best cities to visit?", 0)],
            ),
        ]
        self.provider = StubProvider()

    def test_extract_topics_returns_topic_scan(self):
        result = extract_topics(self.conversations, self.provider)
        self.assertIsInstance(result, TopicScan)

    def test_scan_has_required_fields(self):
        result = extract_topics(self.conversations, self.provider)
        self.assertTrue(result.scan_id.startswith("topic_scan:"))
        self.assertTrue(len(result.generation_timestamp) > 0)
        self.assertEqual(result.conversation_count, 3)
        self.assertEqual(result.derived_from, "canonical_imported_conversations")
        self.assertEqual(result.artifact_kind, "topic_scan_v1")

    def test_empty_conversations_returns_empty_clusters(self):
        result = extract_topics([], self.provider)
        self.assertEqual(result.clusters, [])
        self.assertEqual(result.conversation_count, 0)


class KeywordFallbackTest(unittest.TestCase):
    def test_fallback_detects_shared_keywords(self):
        conversations = [
            FakeConversation(id=1, title="Python development tips", messages=[]),
            FakeConversation(id=2, title="Python testing guide", messages=[]),
            FakeConversation(id=3, title="Travel planning Europe", messages=[]),
            FakeConversation(id=4, title="Travel budget tips", messages=[]),
        ]

        result = extract_topics(conversations, provider=None)
        self.assertEqual(result.llm_provider_used, "keyword_fallback")
        self.assertTrue(len(result.clusters) > 0)

        # Check that clusters reference correct stable IDs
        for cluster in result.clusters:
            for sid in cluster["conversation_stable_ids"]:
                self.assertTrue(sid.startswith("imported_conversation:"))

    def test_fallback_marks_confidence_low(self):
        conversations = [
            FakeConversation(id=1, title="Python development", messages=[]),
            FakeConversation(id=2, title="Python testing", messages=[]),
        ]

        result = extract_topics(conversations, provider=None)
        for cluster in result.clusters:
            self.assertEqual(cluster["confidence"], "low")

    def test_fallback_no_shared_keywords_returns_empty(self):
        conversations = [
            FakeConversation(id=1, title="Alpha", messages=[]),
            FakeConversation(id=2, title="Beta", messages=[]),
        ]

        result = extract_topics(conversations, provider=None)
        self.assertEqual(result.clusters, [])

    def test_fallback_empty_list_returns_empty(self):
        result = extract_topics([], provider=None)
        self.assertEqual(result.clusters, [])
        self.assertEqual(result.conversation_count, 0)

    def test_cluster_stable_ids_match_conversations(self):
        conversations = [
            FakeConversation(id=10, title="Cooking recipes dinner", messages=[]),
            FakeConversation(id=20, title="Cooking tips breakfast", messages=[]),
        ]

        result = extract_topics(conversations, provider=None)
        self.assertTrue(len(result.clusters) > 0)
        cooking_cluster = result.clusters[0]
        self.assertIn("imported_conversation:10", cooking_cluster["conversation_stable_ids"])
        self.assertIn("imported_conversation:20", cooking_cluster["conversation_stable_ids"])


if __name__ == "__main__":
    unittest.main()
