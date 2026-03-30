"""Tests for Google Takeout MyActivity.json parser (time-grouped conversations)."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from src.importers.cli import import_conversation_export_to_sqlite
from src.importers.gemini import (
    DEFAULT_ACTIVITY_GAP_SECONDS,
    looks_like_gemini_export,
    looks_like_gemini_myactivity,
    looks_like_gemini_takeout,
    parse_gemini_export,
    parse_gemini_export_file,
)
from src.importers.registry import parse_import_file
from tests.temp_helpers import make_test_temp_dir, release_app_db_handles


FIXTURE = Path("sample_data/gemini_takeout_myactivity.json")


# ---------------------------------------------------------------------------
# Detection tests
# ---------------------------------------------------------------------------


class MyActivityDetectionTest(unittest.TestCase):
    def test_myactivity_fixture_detected(self):
        with FIXTURE.open() as f:
            payload = json.load(f)
        self.assertTrue(looks_like_gemini_myactivity(payload))
        self.assertTrue(looks_like_gemini_export(payload))

    def test_myactivity_also_matches_broader_takeout_detector(self):
        """MyActivity entries also match the broader takeout detector since they
        have the same header/title structure."""
        with FIXTURE.open() as f:
            payload = json.load(f)
        self.assertTrue(looks_like_gemini_takeout(payload))

    def test_chatgpt_payload_not_detected_as_myactivity(self):
        payload = [{"id": "conv-1", "mapping": {"root": {}}}]
        self.assertFalse(looks_like_gemini_myactivity(payload))

    def test_claude_payload_not_detected_as_myactivity(self):
        payload = [{"uuid": "c1", "chat_messages": []}]
        self.assertFalse(looks_like_gemini_myactivity(payload))

    def test_old_takeout_fixture_not_detected_as_myactivity(self):
        """The old takeout fixture (no 'Prompted ' prefix) should NOT match
        the myactivity detector."""
        with Path("sample_data/gemini_takeout.json").open() as f:
            payload = json.load(f)
        self.assertFalse(looks_like_gemini_myactivity(payload))

    def test_empty_list_not_detected(self):
        self.assertFalse(looks_like_gemini_myactivity([]))

    def test_non_list_not_detected(self):
        self.assertFalse(looks_like_gemini_myactivity({"header": "Gemini Apps"}))


# ---------------------------------------------------------------------------
# Parser tests
# ---------------------------------------------------------------------------


class MyActivityParserTest(unittest.TestCase):
    def test_fixture_produces_six_entries_in_two_conversations(self):
        conversations = parse_gemini_export_file(FIXTURE)

        self.assertEqual(len(conversations), 2)

        # Conversation 1: 3 entries about capitals → 3 user + 3 assistant = 6 messages
        conv1 = conversations[0]
        self.assertEqual(len(conv1.messages), 6)
        self.assertEqual(conv1.source_provider, "gemini")
        self.assertEqual(conv1.source_metadata.get("gemini_export_shape"), "myactivity")

        # Conversation 2: 3 entries about photosynthesis → 6 messages
        conv2 = conversations[1]
        self.assertEqual(len(conv2.messages), 6)

    def test_prompt_extraction_strips_prompted_prefix(self):
        conversations = parse_gemini_export_file(FIXTURE)

        first_msg = conversations[0].messages[0]
        self.assertEqual(first_msg.role, "user")
        self.assertEqual(first_msg.content, "What is the capital of France?")
        self.assertFalse(first_msg.content.startswith("Prompted"))

    def test_response_extraction_strips_html(self):
        conversations = parse_gemini_export_file(FIXTURE)

        # First assistant response
        assistant_msg = conversations[0].messages[1]
        self.assertEqual(assistant_msg.role, "assistant")
        self.assertEqual(assistant_msg.content, "The capital of France is Paris.")
        self.assertNotIn("<p>", assistant_msg.content)

    def test_multi_paragraph_html_converted_to_newline_separated_text(self):
        conversations = parse_gemini_export_file(FIXTURE)

        # Entry 4 (first in conv2) has two <p> tags
        assistant_msg = conversations[1].messages[1]
        self.assertIn("Photosynthesis is the process", assistant_msg.content)
        self.assertIn("It occurs primarily", assistant_msg.content)
        self.assertNotIn("<p>", assistant_msg.content)

    def test_conversation_titles_derived_from_first_prompt(self):
        conversations = parse_gemini_export_file(FIXTURE)

        self.assertIn("capital of France", conversations[0].title)
        self.assertIn("photosynthesis", conversations[1].title.lower())

    def test_message_roles_alternate_user_assistant(self):
        conversations = parse_gemini_export_file(FIXTURE)

        for conv in conversations:
            roles = [msg.role for msg in conv.messages]
            self.assertEqual(roles, ["user", "assistant"] * (len(roles) // 2))

    def test_sequence_indices_are_contiguous(self):
        conversations = parse_gemini_export_file(FIXTURE)

        for conv in conversations:
            indices = [msg.sequence_index for msg in conv.messages]
            self.assertEqual(indices, list(range(len(conv.messages))))

    def test_timestamps_are_present_on_all_messages(self):
        conversations = parse_gemini_export_file(FIXTURE)

        for conv in conversations:
            self.assertIsNotNone(conv.created_at)
            self.assertIsNotNone(conv.updated_at)
            for msg in conv.messages:
                self.assertIsNotNone(msg.created_at)


# ---------------------------------------------------------------------------
# Deterministic ID tests
# ---------------------------------------------------------------------------


class MyActivityDeterministicIdTest(unittest.TestCase):
    def test_same_fixture_produces_identical_ids_across_parses(self):
        first_run = parse_gemini_export_file(FIXTURE)
        second_run = parse_gemini_export_file(FIXTURE)

        first_ids = [c.source_conversation_id for c in first_run]
        second_ids = [c.source_conversation_id for c in second_run]
        self.assertEqual(first_ids, second_ids)

    def test_conversation_ids_have_expected_prefix(self):
        conversations = parse_gemini_export_file(FIXTURE)

        for conv in conversations:
            self.assertTrue(
                conv.source_conversation_id.startswith("gemini_activity_"),
                f"Expected 'gemini_activity_' prefix, got: {conv.source_conversation_id}",
            )

    def test_different_content_produces_different_ids(self):
        payload1 = [
            {
                "header": "Gemini Apps",
                "title": "Prompted Hello",
                "time": "2026-01-01T00:00:00.000Z",
                "products": ["Gemini Apps"],
            }
        ]
        payload2 = [
            {
                "header": "Gemini Apps",
                "title": "Prompted Goodbye",
                "time": "2026-01-01T00:00:00.000Z",
                "products": ["Gemini Apps"],
            }
        ]

        convs1 = parse_gemini_export(payload1)
        convs2 = parse_gemini_export(payload2)

        self.assertNotEqual(
            convs1[0].source_conversation_id,
            convs2[0].source_conversation_id,
        )


# ---------------------------------------------------------------------------
# Time-proximity grouping tests
# ---------------------------------------------------------------------------


class MyActivityTimeGroupingTest(unittest.TestCase):
    def test_entries_within_gap_grouped_together(self):
        payload = [
            {
                "header": "Gemini Apps",
                "title": "Prompted A",
                "time": "2026-01-01T10:00:00.000Z",
                "products": ["Gemini Apps"],
            },
            {
                "header": "Gemini Apps",
                "title": "Prompted B",
                "time": "2026-01-01T10:05:00.000Z",
                "products": ["Gemini Apps"],
            },
        ]

        conversations = parse_gemini_export(payload)
        self.assertEqual(len(conversations), 1)
        # 2 user messages, no responses (no safeHtmlItem)
        self.assertEqual(len(conversations[0].messages), 2)

    def test_entries_beyond_gap_split_into_separate_conversations(self):
        payload = [
            {
                "header": "Gemini Apps",
                "title": "Prompted A",
                "time": "2026-01-01T10:00:00.000Z",
                "products": ["Gemini Apps"],
            },
            {
                "header": "Gemini Apps",
                "title": "Prompted B",
                "time": "2026-01-01T11:00:00.000Z",  # 60 min gap > 30 min default
                "products": ["Gemini Apps"],
            },
        ]

        conversations = parse_gemini_export(payload)
        self.assertEqual(len(conversations), 2)

    def test_custom_gap_threshold(self):
        payload = [
            {
                "header": "Gemini Apps",
                "title": "Prompted A",
                "time": "2026-01-01T10:00:00.000Z",
                "products": ["Gemini Apps"],
            },
            {
                "header": "Gemini Apps",
                "title": "Prompted B",
                "time": "2026-01-01T10:10:00.000Z",  # 10 min gap
                "products": ["Gemini Apps"],
            },
        ]

        # With 5-minute gap → should split
        conversations = parse_gemini_export(payload, activity_gap_seconds=300)
        self.assertEqual(len(conversations), 2)

        # With 15-minute gap → should group
        conversations = parse_gemini_export(payload, activity_gap_seconds=900)
        self.assertEqual(len(conversations), 1)

    def test_single_entry_produces_single_conversation(self):
        payload = [
            {
                "header": "Gemini Apps",
                "title": "Prompted Solo question",
                "time": "2026-01-01T10:00:00.000Z",
                "products": ["Gemini Apps"],
            },
        ]

        conversations = parse_gemini_export(payload)
        self.assertEqual(len(conversations), 1)
        self.assertEqual(conversations[0].messages[0].content, "Solo question")

    def test_unsorted_entries_are_sorted_before_grouping(self):
        payload = [
            {
                "header": "Gemini Apps",
                "title": "Prompted Third",
                "time": "2026-01-01T10:10:00.000Z",
                "products": ["Gemini Apps"],
            },
            {
                "header": "Gemini Apps",
                "title": "Prompted First",
                "time": "2026-01-01T10:00:00.000Z",
                "products": ["Gemini Apps"],
            },
            {
                "header": "Gemini Apps",
                "title": "Prompted Second",
                "time": "2026-01-01T10:05:00.000Z",
                "products": ["Gemini Apps"],
            },
        ]

        conversations = parse_gemini_export(payload)
        self.assertEqual(len(conversations), 1)

        user_messages = [m for m in conversations[0].messages if m.role == "user"]
        self.assertEqual(user_messages[0].content, "First")
        self.assertEqual(user_messages[1].content, "Second")
        self.assertEqual(user_messages[2].content, "Third")


# ---------------------------------------------------------------------------
# Edge case tests
# ---------------------------------------------------------------------------


class MyActivityEdgeCaseTest(unittest.TestCase):
    def test_entry_without_safe_html_item_has_empty_response(self):
        payload = [
            {
                "header": "Gemini Apps",
                "title": "Prompted What is life?",
                "time": "2026-01-01T10:00:00.000Z",
                "products": ["Gemini Apps"],
                # No safeHtmlItem
            },
        ]

        conversations = parse_gemini_export(payload)
        self.assertEqual(len(conversations), 1)
        # Only user message, no assistant (empty response skipped)
        self.assertEqual(len(conversations[0].messages), 1)
        self.assertEqual(conversations[0].messages[0].role, "user")

    def test_entry_with_empty_safe_html_item_list(self):
        payload = [
            {
                "header": "Gemini Apps",
                "title": "Prompted Test",
                "time": "2026-01-01T10:00:00.000Z",
                "products": ["Gemini Apps"],
                "safeHtmlItem": [],
            },
        ]

        conversations = parse_gemini_export(payload)
        self.assertEqual(len(conversations[0].messages), 1)

    def test_entry_with_empty_html_string(self):
        payload = [
            {
                "header": "Gemini Apps",
                "title": "Prompted Test",
                "time": "2026-01-01T10:00:00.000Z",
                "products": ["Gemini Apps"],
                "safeHtmlItem": [{"html": "  "}],
            },
        ]

        conversations = parse_gemini_export(payload)
        self.assertEqual(len(conversations[0].messages), 1)

    def test_non_gemini_header_entries_are_filtered_out(self):
        payload = [
            {
                "header": "Google Search",
                "title": "Prompted Ignored",
                "time": "2026-01-01T10:00:00.000Z",
                "products": ["Google Search"],
            },
            {
                "header": "Gemini Apps",
                "title": "Prompted Included",
                "time": "2026-01-01T10:01:00.000Z",
                "products": ["Gemini Apps"],
            },
        ]

        conversations = parse_gemini_export(payload)
        self.assertEqual(len(conversations), 1)
        self.assertEqual(conversations[0].messages[0].content, "Included")

    def test_entry_with_blank_prompt_after_prefix_is_skipped(self):
        payload = [
            {
                "header": "Gemini Apps",
                "title": "Prompted ",
                "time": "2026-01-01T10:00:00.000Z",
                "products": ["Gemini Apps"],
            },
        ]

        conversations = parse_gemini_export(payload)
        self.assertEqual(len(conversations), 0)


# ---------------------------------------------------------------------------
# Auto-detection integration
# ---------------------------------------------------------------------------


class MyActivityAutoDetectTest(unittest.TestCase):
    def test_myactivity_fixture_auto_detects_as_gemini(self):
        result = parse_import_file(FIXTURE)
        self.assertEqual(result.provider_id, "gemini")
        self.assertEqual(len(result.conversations), 2)

    def test_old_takeout_fixture_still_auto_detects(self):
        """Existing takeout fixture still works through the registry."""
        result = parse_import_file(Path("sample_data/gemini_takeout.json"))
        self.assertEqual(result.provider_id, "gemini")
        self.assertEqual(len(result.conversations), 4)


# ---------------------------------------------------------------------------
# Persistence and duplicate policy
# ---------------------------------------------------------------------------


class MyActivityPersistenceTest(unittest.TestCase):
    def test_myactivity_import_persists_and_deduplicates(self):
        workdir = make_test_temp_dir(self, "gemini-myactivity")
        sqlite_path = workdir / "gemini_myactivity.db"

        first = import_conversation_export_to_sqlite(FIXTURE, sqlite_path, provider="gemini")
        second = import_conversation_export_to_sqlite(FIXTURE, sqlite_path, provider="gemini")

        self.assertEqual(first.provider_id, "gemini")
        self.assertEqual(first.imported_conversations, 2)
        self.assertEqual(first.imported_messages, 12)  # 6 user + 6 assistant

        self.assertEqual(second.imported_conversations, 0)
        self.assertEqual(second.skipped_conversations, 2)


if __name__ == "__main__":
    unittest.main()
