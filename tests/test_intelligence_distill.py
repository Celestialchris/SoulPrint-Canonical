"""Tests for multi-conversation distillation."""

from __future__ import annotations

import unittest
from dataclasses import dataclass, field

from src.intelligence.distill import (
    DistillationResult,
    _build_multi_transcript,
    distill_conversations,
)
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
    source: str = "chatgpt"
    created_at_unix: int = 0


def _make_conv(id: int, title: str, body: str, ts: int = 0) -> FakeConversation:
    return FakeConversation(
        id=id,
        title=title,
        source="chatgpt",
        created_at_unix=ts,
        messages=[
            FakeMessage("user", f"Question about {body}", 0),
            FakeMessage("assistant", f"Answer about {body}", 1),
        ],
    )


class BuildMultiTranscriptTest(unittest.TestCase):
    def test_returns_transcript_and_bool(self):
        conv = _make_conv(1, "Test", "python")
        result = _build_multi_transcript([conv], max_chars=100_000)
        transcript, truncated = result
        self.assertIsInstance(transcript, str)
        self.assertIsInstance(truncated, bool)

    def test_no_truncation_when_fits(self):
        convs = [_make_conv(i, f"Conv {i}", f"topic {i}") for i in range(3)]
        _, truncated = _build_multi_transcript(convs, max_chars=100_000)
        self.assertFalse(truncated)

    def test_truncation_fires_when_budget_exceeded(self):
        convs = [_make_conv(i, f"Conv {i}", "x" * 30, ts=i) for i in range(5)]
        _, truncated = _build_multi_transcript(convs, max_chars=50)
        self.assertTrue(truncated)

    def test_most_recent_conv_survives_truncation(self):
        # ts=100 is newest, ts=1 is oldest
        old_conv = _make_conv(1, "OldConversation", "old stuff", ts=1)
        new_conv = _make_conv(2, "NewConversation", "new stuff", ts=100)
        # Each block is ~126 chars; budget fits one but not two (126+2+126=254)
        transcript, truncated = _build_multi_transcript(
            [old_conv, new_conv], max_chars=150
        )
        self.assertTrue(truncated)
        self.assertIn("NewConversation", transcript)
        self.assertNotIn("OldConversation", transcript)

    def test_no_separator_before_first_block(self):
        conv = _make_conv(1, "Solo", "solo")
        transcript, _ = _build_multi_transcript([conv], max_chars=100_000)
        self.assertFalse(transcript.startswith("\n\n"))

    def test_blocks_joined_with_double_newline(self):
        convs = [_make_conv(i, f"Conv{i}", f"t{i}", ts=i) for i in range(2)]
        transcript, _ = _build_multi_transcript(convs, max_chars=100_000)
        self.assertIn("\n\n", transcript)

    def test_oversized_single_block_still_included(self):
        # A single conversation larger than max_chars must still appear in the
        # transcript — the first block is always included to avoid empty LLM input.
        conv = _make_conv(1, "HugeConversation", "x" * 500, ts=1)
        transcript, truncated = _build_multi_transcript([conv], max_chars=10)
        self.assertTrue(len(transcript) > 0)
        self.assertIn("HugeConversation", transcript)
        self.assertTrue(truncated)

    def test_empty_conversations_returns_empty_string(self):
        transcript, truncated = _build_multi_transcript([], max_chars=100_000)
        self.assertEqual(transcript, "")
        self.assertFalse(truncated)

    def test_conversations_missing_created_at_unix_handled(self):
        # FakeConversation without created_at_unix attr
        @dataclass
        class MinimalConv:
            id: int
            title: str
            source: str
            messages: list

        conv = MinimalConv(
            id=1,
            title="NoTimestamp",
            source="chatgpt",
            messages=[FakeMessage("user", "hi", 0)],
        )
        transcript, _ = _build_multi_transcript([conv], max_chars=100_000)
        self.assertIn("NoTimestamp", transcript)


class DistillConversationsTest(unittest.TestCase):
    def setUp(self):
        self.provider = StubProvider()
        self.convs = [_make_conv(i, f"Conv {i}", f"topic {i}", ts=i) for i in range(3)]

    def test_returns_distillation_result(self):
        result = distill_conversations(self.convs, self.provider)
        self.assertIsInstance(result, DistillationResult)

    def test_fields_populated(self):
        result = distill_conversations(self.convs, self.provider)
        self.assertTrue(result.distillation_id.startswith("distillation:"))
        self.assertEqual(result.conversation_count, 3)
        self.assertEqual(result.total_message_count, 6)
        self.assertEqual(result.llm_provider_used, "stub")
        self.assertEqual(result.prompt_template_version, "distill-v1")
        self.assertIsInstance(result.distilled_text, str)
        self.assertTrue(len(result.distilled_text) > 0)

    def test_input_truncated_false_when_fits(self):
        result = distill_conversations(self.convs, self.provider)
        self.assertFalse(result.input_truncated)

    def test_input_truncated_true_when_overflow(self):
        import src.intelligence.distill as distill_mod
        original = distill_mod.MAX_INPUT_CHARS
        try:
            distill_mod.MAX_INPUT_CHARS = 50
            result = distill_conversations(self.convs, self.provider)
            self.assertTrue(result.input_truncated)
        finally:
            distill_mod.MAX_INPUT_CHARS = original

    def test_empty_conversations_returns_early(self):
        result = distill_conversations([], self.provider)
        self.assertEqual(result.conversation_count, 0)
        self.assertIn("No conversations", result.distilled_text)

    def test_source_stable_ids_prefixed(self):
        result = distill_conversations(self.convs, self.provider)
        for sid in result.source_conversation_stable_ids:
            self.assertTrue(sid.startswith("imported_conversation:"))

    def test_single_conversation(self):
        result = distill_conversations([self.convs[0]], self.provider)
        self.assertEqual(result.conversation_count, 1)
        self.assertFalse(result.input_truncated)


if __name__ == "__main__":
    unittest.main()
