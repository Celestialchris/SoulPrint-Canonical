"""Tests for cross-conversation digest generation."""

from __future__ import annotations

import unittest
from dataclasses import dataclass

from src.intelligence.digest import DerivedDigest, generate_digest
from src.intelligence.provider import StubProvider


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


class GenerateDigestTest(unittest.TestCase):
    def setUp(self):
        self.conversations = [
            FakeConversation(
                id=1,
                title="Python decorators",
                messages=[
                    FakeMessage("user", "How do decorators work?", 0),
                    FakeMessage("assistant", "They wrap functions.", 1),
                ],
            ),
            FakeConversation(
                id=2,
                title="Python testing",
                messages=[
                    FakeMessage("user", "Best testing frameworks?", 0),
                    FakeMessage("assistant", "pytest is popular.", 1),
                ],
            ),
        ]
        self.provider = StubProvider()

    def test_returns_derived_digest(self):
        result = generate_digest("Python development", self.conversations, self.provider)
        self.assertIsInstance(result, DerivedDigest)

    def test_all_fields_populated(self):
        result = generate_digest("Python development", self.conversations, self.provider)

        self.assertTrue(result.digest_id.startswith("derived_digest:"))
        self.assertEqual(result.topic_label, "Python development")
        self.assertEqual(
            result.source_conversation_stable_ids,
            ["imported_conversation:1", "imported_conversation:2"],
        )
        self.assertEqual(
            result.source_conversation_titles,
            ["Python decorators", "Python testing"],
        )
        self.assertTrue(len(result.generation_timestamp) > 0)
        self.assertEqual(result.llm_provider_used, "stub")
        self.assertEqual(result.prompt_template_version, "v1")
        self.assertTrue(len(result.digest_text) > 0)
        self.assertEqual(result.derived_from, "canonical_imported_conversations")
        self.assertEqual(result.artifact_kind, "derived_digest_v1")

    def test_digest_references_source_stable_ids(self):
        result = generate_digest("Topic", self.conversations, self.provider)
        for sid in result.source_conversation_stable_ids:
            self.assertTrue(sid.startswith("imported_conversation:"))

    def test_stub_provider_works_without_api_keys(self):
        # Should not raise
        result = generate_digest("Topic", self.conversations, StubProvider())
        self.assertIsInstance(result.digest_text, str)
        self.assertTrue(len(result.digest_text) > 0)

    def test_single_conversation_digest(self):
        result = generate_digest(
            "Solo topic",
            [self.conversations[0]],
            self.provider,
        )
        self.assertEqual(len(result.source_conversation_stable_ids), 1)
        self.assertEqual(result.source_conversation_stable_ids[0], "imported_conversation:1")


if __name__ == "__main__":
    unittest.main()
