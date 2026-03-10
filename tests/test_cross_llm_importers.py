"""Tests for cross-provider imported conversation continuity."""

from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from src.app import create_app
from src.app.models import ImportedConversation, ImportedMessage
from src.app.models.db import db
from src.config import Config
from src.importers.cli import import_conversation_export_to_sqlite, main
from src.importers.claude import parse_claude_export_file
from src.importers.errors import (
    ImportProviderDetectionError,
    MalformedImportFileError,
    UnsupportedImportFormatError,
)
from src.importers.registry import parse_import_file


class ClaudeImporterTest(unittest.TestCase):
    def test_parse_claude_fixture_normalizes_provider_ids_timestamps_and_order(self):
        fixture = Path("sample_data/claude_export_sample.json")

        conversations = parse_claude_export_file(fixture)

        self.assertEqual(len(conversations), 2)

        first = conversations[0]
        self.assertEqual(first.source_provider, "claude")
        self.assertEqual(first.source_conversation_id, "claude-conv-1")
        self.assertEqual(first.title, "Bakery planning")
        self.assertEqual([message.role for message in first.messages], ["user", "assistant"])
        self.assertEqual([message.sequence_index for message in first.messages], [0, 1])
        self.assertEqual(
            [message.source_message_id for message in first.messages],
            ["claude-msg-1", "claude-msg-2"],
        )
        self.assertIsNotNone(first.created_at)
        self.assertIsNotNone(first.updated_at)

    def test_claude_partial_payload_import_succeeds_with_warnings(self):
        partial_payload = [
            {
                "uuid": "claude-partial-1",
                "name": "",
                "created_at": "2024-12-03T09:00:00Z",
                "chat_messages": [
                    {
                        "uuid": "claude-partial-msg-1",
                        "sender": "human",
                        "text": "Keep this conversation even without timestamps.",
                    }
                ],
            }
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            export_path = Path(tmpdir) / "claude_partial.json"
            sqlite_path = Path(tmpdir) / "claude_partial.db"
            export_path.write_text(json.dumps(partial_payload), encoding="utf-8")

            result = import_conversation_export_to_sqlite(
                export_path,
                sqlite_path,
                provider="claude",
            )

            self.assertEqual(result.provider_id, "claude")
            self.assertEqual(result.imported_conversations, 1)
            self.assertEqual(result.imported_messages, 1)
            self.assertTrue(result.warnings)
            self.assertTrue(
                any("fallback title" in warning.lower() for warning in result.warnings)
            )
            self.assertTrue(
                any("missing create/update timestamps" in warning.lower() for warning in result.warnings)
            )
            self.assertTrue(
                any("missing created_at timestamps" in warning.lower() for warning in result.warnings)
            )

    def test_claude_malformed_payload_raises_provider_specific_error(self):
        malformed_payload = {
            "uuid": "claude-bad-1",
            "name": "Malformed Claude conversation",
            "chat_messages": "not-a-list",
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            export_path = Path(tmpdir) / "claude_bad.json"
            export_path.write_text(json.dumps(malformed_payload), encoding="utf-8")

            with self.assertRaises(MalformedImportFileError) as error:
                parse_import_file(export_path, provider_hint="claude")

            self.assertIn("claude import payload is malformed", str(error.exception))

    def test_claude_duplicate_import_policy_remains_source_aware(self):
        fixture = Path("sample_data/claude_export_sample.json")

        with tempfile.TemporaryDirectory() as tmpdir:
            sqlite_path = Path(tmpdir) / "claude_duplicate.db"

            first = import_conversation_export_to_sqlite(fixture, sqlite_path, provider="claude")
            second = import_conversation_export_to_sqlite(fixture, sqlite_path, provider="claude")

            self.assertEqual(first.imported_conversations, 2)
            self.assertEqual(first.skipped_conversations, 0)
            self.assertEqual(second.imported_conversations, 0)
            self.assertEqual(second.skipped_conversations, 2)

    def test_auto_detected_chatgpt_path_still_imports(self):
        fixture = Path("sample_data/chatgpt_export_sample.json")

        with tempfile.TemporaryDirectory() as tmpdir:
            sqlite_path = Path(tmpdir) / "chatgpt_auto.db"

            result = import_conversation_export_to_sqlite(fixture, sqlite_path)

            self.assertEqual(result.provider_id, "chatgpt")
            self.assertEqual(result.imported_conversations, 2)
            self.assertEqual(result.imported_messages, 4)


class GeminiBoundaryTest(unittest.TestCase):
    def test_unknown_payload_fails_detection_cleanly(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            export_path = Path(tmpdir) / "unknown.json"
            export_path.write_text(json.dumps({"hello": "world"}), encoding="utf-8")

            with self.assertRaises(ImportProviderDetectionError) as error:
                parse_import_file(export_path)

            self.assertIn("Could not detect import provider", str(error.exception))

    def test_gemini_provider_slot_is_recognized_but_unsupported(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            export_path = Path(tmpdir) / "gemini.json"
            export_path.write_text(json.dumps({"conversations": []}), encoding="utf-8")

            with self.assertRaises(UnsupportedImportFormatError) as error:
                parse_import_file(export_path, provider_hint="gemini")

            self.assertIn("Gemini provider is recognized", str(error.exception))


class ClaudeImportedBrowserIntegrationTest(unittest.TestCase):
    def setUp(self):
        self._old_uri = Config.SQLALCHEMY_DATABASE_URI
        self.tmpdir = tempfile.TemporaryDirectory()
        self.sqlite_path = Path(self.tmpdir.name) / "claude_browser.db"
        Config.SQLALCHEMY_DATABASE_URI = f"sqlite:///{self.sqlite_path}"

        import_conversation_export_to_sqlite(
            Path("sample_data/claude_export_sample.json"),
            self.sqlite_path,
            provider="claude",
        )

        self.app = create_app()
        self.client = self.app.test_client()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
            db.engine.dispose()
        Config.SQLALCHEMY_DATABASE_URI = self._old_uri
        self.tmpdir.cleanup()

    def test_imported_claude_conversation_appears_in_list_and_explorer(self):
        list_response = self.client.get("/imported")
        self.assertEqual(list_response.status_code, 200)
        list_html = list_response.get_data(as_text=True)
        self.assertIn("Provider: claude", list_html)
        self.assertIn("Bakery planning", list_html)

        with self.app.app_context():
            conversation = ImportedConversation.query.filter_by(
                source="claude",
                source_conversation_id="claude-conv-1",
            ).first()
            self.assertIsNotNone(conversation)
            assert conversation is not None

        detail_response = self.client.get(f"/imported/{conversation.id}/explorer")
        self.assertEqual(detail_response.status_code, 200)
        detail_html = detail_response.get_data(as_text=True)
        self.assertIn("Provider: claude", detail_html)
        self.assertIn("Bakery planning", detail_html)
        self.assertIn("Help me plan a bakery opening checklist.", detail_html)

    def test_imported_claude_records_flow_into_existing_canonical_tables(self):
        with self.app.app_context():
            self.assertEqual(
                ImportedConversation.query.filter_by(source="claude").count(),
                2,
            )
            self.assertEqual(
                ImportedMessage.query.join(ImportedConversation).filter(
                    ImportedConversation.source == "claude"
                ).count(),
                6,
            )


class ImportCliOutputTest(unittest.TestCase):
    def test_cli_summary_includes_detected_provider_identity(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            sqlite_path = Path(tmpdir) / "cli_claude.db"
            argv = [
                "importers.cli",
                "sample_data/claude_export_sample.json",
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
        self.assertIn("Provider: claude", output)
        self.assertIn("Imported 2 conversations", output)


if __name__ == "__main__":
    unittest.main()
