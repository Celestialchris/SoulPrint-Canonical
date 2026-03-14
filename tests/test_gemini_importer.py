"""Tests for Gemini imported conversation support (both export shapes)."""

from __future__ import annotations

import io
import json
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from src.app import create_app
from src.app.models import ImportedConversation, ImportedMessage
from src.app.models.db import db
from src.config import Config
from src.importers.cli import import_conversation_export_to_sqlite, main
from src.importers.errors import MalformedImportFileError
from src.importers.gemini import (
    looks_like_gemini_conversations,
    looks_like_gemini_export,
    looks_like_gemini_takeout,
    parse_gemini_export,
    parse_gemini_export_file,
)
from src.importers.registry import parse_import_file
from tests.temp_helpers import make_test_temp_dir, release_app_db_handles


# ---------------------------------------------------------------------------
# Parser unit tests — Takeout shape
# ---------------------------------------------------------------------------


class GeminiTakeoutParserTest(unittest.TestCase):
    def test_parse_takeout_fixture_produces_one_conversation_per_activity_entry(self):
        conversations = parse_gemini_export_file(
            Path("sample_data/gemini_takeout_sample.json")
        )

        self.assertEqual(len(conversations), 4)

        for conv in conversations:
            self.assertEqual(conv.source_provider, "gemini")
            self.assertEqual(len(conv.messages), 1)
            self.assertEqual(conv.messages[0].role, "user")
            self.assertEqual(conv.messages[0].sequence_index, 0)
            self.assertIsNotNone(conv.created_at)
            self.assertEqual(conv.source_metadata.get("gemini_export_shape"), "takeout")

    def test_takeout_titles_are_truncated_from_prompt_text(self):
        conversations = parse_gemini_export_file(
            Path("sample_data/gemini_takeout_sample.json")
        )

        first = conversations[0]
        self.assertIn("hiking trails", first.title.lower())
        self.assertIn("hiking trails", first.messages[0].content.lower())

    def test_takeout_source_ids_are_stable_across_re_parses(self):
        first_run = parse_gemini_export_file(
            Path("sample_data/gemini_takeout_sample.json")
        )
        second_run = parse_gemini_export_file(
            Path("sample_data/gemini_takeout_sample.json")
        )

        first_ids = [conv.source_conversation_id for conv in first_run]
        second_ids = [conv.source_conversation_id for conv in second_run]
        self.assertEqual(first_ids, second_ids)

    def test_takeout_entries_with_non_gemini_header_are_skipped(self):
        payload = [
            {
                "header": "Google Search",
                "title": "This should be ignored",
                "time": "2024-11-15T08:00:00.000Z",
                "products": ["Google Search"],
            },
            {
                "header": "Gemini Apps",
                "title": "This should be included",
                "time": "2024-11-15T09:00:00.000Z",
                "products": ["Gemini Apps"],
            },
        ]

        conversations = parse_gemini_export(payload)
        self.assertEqual(len(conversations), 1)
        self.assertIn("included", conversations[0].title.lower())

    def test_takeout_entry_with_blank_title_is_skipped(self):
        payload = [
            {
                "header": "Gemini Apps",
                "title": "  ",
                "time": "2024-11-15T08:00:00.000Z",
            },
        ]

        conversations = parse_gemini_export(payload)
        self.assertEqual(len(conversations), 0)


# ---------------------------------------------------------------------------
# Parser unit tests — Conversational shape
# ---------------------------------------------------------------------------


class GeminiConversationalParserTest(unittest.TestCase):
    def test_parse_conversations_fixture_normalizes_provider_and_roles(self):
        conversations = parse_gemini_export_file(
            Path("sample_data/gemini_conversations_sample.json")
        )

        self.assertEqual(len(conversations), 2)

        first = conversations[0]
        self.assertEqual(first.source_provider, "gemini")
        self.assertEqual(first.title, "Hiking trails near Bucharest")
        self.assertEqual(len(first.messages), 4)
        self.assertEqual(
            [msg.role for msg in first.messages],
            ["user", "assistant", "user", "assistant"],
        )
        self.assertEqual(
            [msg.sequence_index for msg in first.messages],
            [0, 1, 2, 3],
        )
        self.assertEqual(first.source_metadata.get("gemini_export_shape"), "conversations")

    def test_conversation_id_derived_from_url_when_available(self):
        conversations = parse_gemini_export_file(
            Path("sample_data/gemini_conversations_sample.json")
        )

        self.assertEqual(conversations[0].source_conversation_id, "gemini-abc123def456")
        self.assertEqual(conversations[1].source_conversation_id, "gemini-xyz789ghi012")

    def test_single_conversation_object_is_accepted(self):
        single = {
            "title": "Solo conversation",
            "messages": [
                {"role": "user", "content": "Hello"},
                {"role": "model", "content": "Hi there"},
            ],
        }

        conversations = parse_gemini_export(single)
        self.assertEqual(len(conversations), 1)
        self.assertEqual(conversations[0].title, "Solo conversation")
        self.assertEqual(len(conversations[0].messages), 2)

    def test_model_role_normalized_to_assistant(self):
        payload = [
            {
                "title": "Role test",
                "messages": [
                    {"role": "user", "content": "Q"},
                    {"role": "model", "content": "A"},
                ],
            }
        ]

        conversations = parse_gemini_export(payload)
        self.assertEqual(conversations[0].messages[1].role, "assistant")

    def test_malformed_messages_field_raises_descriptive_error(self):
        payload = {
            "title": "Bad conversation",
            "messages": "not-a-list",
        }

        # This won't be detected as gemini conversation (messages not a list),
        # so it should raise a ValueError.
        with self.assertRaises(ValueError):
            parse_gemini_export(payload)

    def test_empty_messages_list_does_not_match_detector(self):
        payload = {"title": "Empty", "messages": []}
        self.assertFalse(looks_like_gemini_conversations(payload))

    def test_conversation_with_missing_title_uses_default(self):
        payload = [
            {
                "messages": [
                    {"role": "user", "content": "Quick question"},
                    {"role": "model", "content": "Sure"},
                ],
            }
        ]

        conversations = parse_gemini_export(payload)
        self.assertEqual(conversations[0].title, "Untitled Conversation")

    def test_parts_array_message_extraction(self):
        payload = [
            {
                "title": "Parts test",
                "messages": [
                    {"role": "user", "parts": ["Part one", "Part two"]},
                    {"role": "model", "parts": [{"text": "Response text"}]},
                ],
            }
        ]

        conversations = parse_gemini_export(payload)
        self.assertEqual(conversations[0].messages[0].content, "Part one\nPart two")
        self.assertEqual(conversations[0].messages[1].content, "Response text")


# ---------------------------------------------------------------------------
# Auto-detection tests
# ---------------------------------------------------------------------------


class GeminiDetectionTest(unittest.TestCase):
    def test_takeout_payload_detected(self):
        payload = [
            {
                "header": "Gemini Apps",
                "title": "Test",
                "time": "2024-11-15T08:00:00.000Z",
            }
        ]
        self.assertTrue(looks_like_gemini_takeout(payload))
        self.assertTrue(looks_like_gemini_export(payload))
        self.assertFalse(looks_like_gemini_conversations(payload))

    def test_conversational_payload_detected(self):
        payload = [
            {
                "title": "Test",
                "messages": [{"role": "user", "content": "Hi"}],
            }
        ]
        self.assertFalse(looks_like_gemini_takeout(payload))
        self.assertTrue(looks_like_gemini_conversations(payload))
        self.assertTrue(looks_like_gemini_export(payload))

    def test_chatgpt_payload_not_detected_as_gemini(self):
        payload = [{"id": "conv-1", "mapping": {"root": {}}}]
        self.assertFalse(looks_like_gemini_export(payload))

    def test_claude_payload_not_detected_as_gemini(self):
        payload = [{"uuid": "c1", "chat_messages": []}]
        self.assertFalse(looks_like_gemini_export(payload))

    def test_unknown_payload_not_detected(self):
        payload = {"hello": "world"}
        self.assertFalse(looks_like_gemini_export(payload))

    def test_payload_with_messages_and_chat_messages_prefers_claude(self):
        """A payload that has both 'messages' and 'chat_messages' should not
        match the Gemini detector to avoid cross-provider collisions."""
        payload = {
            "chat_messages": [{"sender": "human", "text": "Hi"}],
            "messages": [{"role": "user", "content": "Hi"}],
        }
        self.assertFalse(looks_like_gemini_conversations(payload))


# ---------------------------------------------------------------------------
# Fixture auto-detection integration
# ---------------------------------------------------------------------------


class GeminiAutoDetectImportTest(unittest.TestCase):
    def test_takeout_fixture_auto_detects_as_gemini(self):
        result = parse_import_file(Path("sample_data/gemini_takeout_sample.json"))
        self.assertEqual(result.provider_id, "gemini")
        self.assertEqual(len(result.conversations), 4)

    def test_conversations_fixture_auto_detects_as_gemini(self):
        result = parse_import_file(Path("sample_data/gemini_conversations_sample.json"))
        self.assertEqual(result.provider_id, "gemini")
        self.assertEqual(len(result.conversations), 2)


# ---------------------------------------------------------------------------
# Persistence and duplicate policy
# ---------------------------------------------------------------------------


class GeminiPersistenceTest(unittest.TestCase):
    def test_takeout_import_persists_and_deduplicates(self):
        fixture = Path("sample_data/gemini_takeout_sample.json")
        workdir = make_test_temp_dir(self, "gemini-persist")
        sqlite_path = workdir / "gemini_takeout.db"

        first = import_conversation_export_to_sqlite(fixture, sqlite_path, provider="gemini")
        second = import_conversation_export_to_sqlite(fixture, sqlite_path, provider="gemini")

        self.assertEqual(first.provider_id, "gemini")
        self.assertEqual(first.imported_conversations, 4)
        self.assertEqual(first.imported_messages, 4)
        self.assertEqual(second.imported_conversations, 0)
        self.assertEqual(second.skipped_conversations, 4)

    def test_conversations_import_persists_full_messages(self):
        fixture = Path("sample_data/gemini_conversations_sample.json")
        workdir = make_test_temp_dir(self, "gemini-persist")
        sqlite_path = workdir / "gemini_conversations.db"

        result = import_conversation_export_to_sqlite(fixture, sqlite_path, provider="gemini")

        self.assertEqual(result.provider_id, "gemini")
        self.assertEqual(result.imported_conversations, 2)
        self.assertEqual(result.imported_messages, 6)  # 4 + 2


# ---------------------------------------------------------------------------
# CLI integration
# ---------------------------------------------------------------------------


class GeminiCliTest(unittest.TestCase):
    def test_cli_auto_detects_gemini_takeout_and_reports_provider(self):
        workdir = make_test_temp_dir(self, "gemini-cli")
        sqlite_path = workdir / "cli_gemini.db"
        argv = [
            "importers.cli",
            "sample_data/gemini_takeout_sample.json",
            "--db",
            str(sqlite_path),
        ]
        old_argv = sys.argv
        stdout = io.StringIO()
        try:
            sys.argv = argv
            with redirect_stdout(stdout):
                exit_code = main()
        finally:
            sys.argv = old_argv

        self.assertEqual(exit_code, 0)
        output = stdout.getvalue()
        self.assertIn("Provider: gemini", output)
        self.assertIn("Imported 4 conversations", output)

    def test_cli_explicit_gemini_provider_for_conversations_fixture(self):
        workdir = make_test_temp_dir(self, "gemini-cli")
        sqlite_path = workdir / "cli_gemini_conv.db"
        argv = [
            "importers.cli",
            "sample_data/gemini_conversations_sample.json",
            "--db",
            str(sqlite_path),
            "--provider",
            "gemini",
        ]
        old_argv = sys.argv
        stdout = io.StringIO()
        try:
            sys.argv = argv
            with redirect_stdout(stdout):
                exit_code = main()
        finally:
            sys.argv = old_argv

        self.assertEqual(exit_code, 0)
        output = stdout.getvalue()
        self.assertIn("Provider: gemini", output)
        self.assertIn("Imported 2 conversations", output)
        self.assertIn("6 messages", output)


# ---------------------------------------------------------------------------
# Web browser integration
# ---------------------------------------------------------------------------


class GeminiBrowserIntegrationTest(unittest.TestCase):
    def setUp(self):
        self.workdir = make_test_temp_dir(self, "gemini-browser")
        self._old_uri = Config.SQLALCHEMY_DATABASE_URI
        self.addCleanup(self._restore_sqlite_uri)
        self.sqlite_path = self.workdir / "gemini_browser.db"
        Config.SQLALCHEMY_DATABASE_URI = f"sqlite:///{self.sqlite_path}"

        import_conversation_export_to_sqlite(
            Path("sample_data/gemini_conversations_sample.json"),
            self.sqlite_path,
            provider="gemini",
        )

        self.app = create_app()
        self.client = self.app.test_client()
        self.addCleanup(release_app_db_handles, self.app, drop_all=True)

    def _restore_sqlite_uri(self):
        Config.SQLALCHEMY_DATABASE_URI = self._old_uri

    def test_imported_gemini_conversation_appears_in_list_and_explorer(self):
        list_response = self.client.get("/imported")
        self.assertEqual(list_response.status_code, 200)
        list_html = list_response.get_data(as_text=True)
        self.assertIn("Provider: gemini", list_html)
        self.assertIn("Hiking trails near Bucharest", list_html)

        with self.app.app_context():
            conversation = ImportedConversation.query.filter_by(
                source="gemini",
            ).first()
            self.assertIsNotNone(conversation)
            assert conversation is not None

        detail_response = self.client.get(f"/imported/{conversation.id}/explorer")
        self.assertEqual(detail_response.status_code, 200)
        detail_html = detail_response.get_data(as_text=True)
        self.assertIn("Provider: gemini", detail_html)
        self.assertIn("Hiking trails near Bucharest", detail_html)

    def test_imported_gemini_records_appear_in_federated_search(self):
        response = self.client.get("/federated?q=hiking")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("hiking", html.lower())

    def test_imported_gemini_records_use_canonical_tables(self):
        with self.app.app_context():
            self.assertEqual(
                ImportedConversation.query.filter_by(source="gemini").count(),
                2,
            )
            self.assertEqual(
                ImportedMessage.query.join(ImportedConversation).filter(
                    ImportedConversation.source == "gemini"
                ).count(),
                6,
            )


# ---------------------------------------------------------------------------
# Contract conformance
# ---------------------------------------------------------------------------


class GeminiContractTest(unittest.TestCase):
    def test_gemini_importer_conforms_to_contract(self):
        from src.importers.gemini import GeminiImporter

        importer = GeminiImporter()
        self.assertEqual(importer.provider_id, "gemini")
        self.assertTrue(callable(importer.parse_payload))

    def test_gemini_provider_id_is_recognized_and_validated(self):
        from src.importers.contracts import validate_provider_id

        self.assertEqual(validate_provider_id("gemini"), "gemini")
        self.assertEqual(validate_provider_id("  GEMINI  "), "gemini")


if __name__ == "__main__":
    unittest.main()
