"""Tests for intelligence conversation summarizer."""

from __future__ import annotations

import unittest
from dataclasses import dataclass

from src.intelligence.provider import StubProvider
from src.intelligence.summarizer import DerivedSummary, summarize_conversation


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


class SummarizeConversationTest(unittest.TestCase):
    def setUp(self):
        self.conversation = FakeConversation(
            id=42,
            title="Test chat about groceries",
            messages=[
                FakeMessage(role="user", content="What should I buy?", sequence_index=0),
                FakeMessage(role="assistant", content="Apples and bread.", sequence_index=1),
            ],
        )
        self.provider = StubProvider()

    def test_returns_derived_summary(self):
        result = summarize_conversation(self.conversation, self.provider)
        self.assertIsInstance(result, DerivedSummary)

    def test_all_fields_populated(self):
        result = summarize_conversation(self.conversation, self.provider)

        self.assertTrue(result.summary_id.startswith("derived_summary:"))
        self.assertEqual(result.source_conversation_stable_id, "imported_conversation:42")
        self.assertEqual(result.source_conversation_title, "Test chat about groceries")
        self.assertTrue(len(result.generation_timestamp) > 0)
        self.assertEqual(result.llm_provider_used, "stub")
        self.assertEqual(result.prompt_template_version, "v1")
        self.assertTrue(len(result.summary_text) > 0)
        self.assertEqual(result.derived_from, "canonical_imported_conversation")
        self.assertEqual(result.artifact_kind, "derived_summary_v1")

    def test_stable_id_format(self):
        result = summarize_conversation(self.conversation, self.provider)
        self.assertTrue(result.source_conversation_stable_id.startswith("imported_conversation:"))

    def test_prompt_template_version_is_v1(self):
        result = summarize_conversation(self.conversation, self.provider)
        self.assertEqual(result.prompt_template_version, "v1")


if __name__ == "__main__":
    unittest.main()
