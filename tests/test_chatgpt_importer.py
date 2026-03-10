"""Tests for ChatGPT export normalization and SQLite persistence."""

import tempfile
import unittest
from pathlib import Path

from flask import Flask

from src.app.models import ImportedConversation, ImportedMessage
from src.app.models.db import db
from src.importers import parse_chatgpt_export_file, persist_normalized_conversations
from src.importers.cli import import_chatgpt_export_to_sqlite
from src.importers.query import (
    export_imported_conversation_markdown,
    get_imported_conversation,
    list_imported_conversations,
    render_imported_conversation_markdown,
    search_imported_conversations,
)


class ChatGPTImporterTest(unittest.TestCase):
    def test_parse_chatgpt_fixture_normalizes_order_and_title(self):
        fixture = Path("sample_data/chatgpt_export_sample.json")
        conversations = parse_chatgpt_export_file(fixture)

        self.assertEqual(len(conversations), 2)

        first = conversations[0]
        self.assertEqual(first.source_provider, "chatgpt")
        self.assertEqual(first.source_conversation_id, "conv-1")
        self.assertEqual(first.title, "Trip planning")
        self.assertEqual([m.role for m in first.messages], ["user", "assistant", "user"])
        self.assertEqual([m.sequence_index for m in first.messages], [0, 1, 2])

        second = conversations[1]
        self.assertEqual(second.title, "Untitled Conversation")
        self.assertEqual(len(second.messages), 1)

    def test_persist_normalized_conversation_to_sqlite(self):
        fixture = Path("sample_data/chatgpt_export_sample.json")
        conversations = parse_chatgpt_export_file(fixture)

        with tempfile.TemporaryDirectory() as tmpdir:
            app = Flask(__name__)
            app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{Path(tmpdir) / 'import_test.db'}"
            app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

            db.init_app(app)
            with app.app_context():
                try:
                    db.create_all()
                    result = persist_normalized_conversations([conversations[0]])

                    self.assertEqual(result.imported_conversations, 1)
                    self.assertEqual(result.imported_messages, 3)
                    self.assertEqual(result.skipped_conversations, 0)

                    stored_conv = ImportedConversation.query.one()
                    self.assertEqual(stored_conv.source, "chatgpt")
                    self.assertEqual(stored_conv.title, "Trip planning")

                    stored_messages = ImportedMessage.query.order_by(ImportedMessage.sequence_index.asc()).all()
                    self.assertEqual(len(stored_messages), 3)
                    self.assertEqual(stored_messages[0].content, "Plan me a 2-day trip to Lisbon.")
                    self.assertEqual(stored_messages[-1].role, "user")
                finally:
                    db.session.remove()
                    db.engine.dispose()

    def test_cli_import_path_imports_fixture_into_sqlite(self):
        fixture = Path("sample_data/chatgpt_export_sample.json")

        with tempfile.TemporaryDirectory() as tmpdir:
            sqlite_path = Path(tmpdir) / "cli_import.db"
            result = import_chatgpt_export_to_sqlite(fixture, sqlite_path)

            self.assertEqual(result.imported_conversations, 2)
            self.assertEqual(result.imported_messages, 4)
            self.assertEqual(result.skipped_conversations, 0)

            verify_app = Flask(__name__)
            verify_app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{sqlite_path}"
            verify_app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

            db.init_app(verify_app)
            with verify_app.app_context():
                try:
                    self.assertEqual(ImportedConversation.query.count(), 2)
                    self.assertEqual(ImportedMessage.query.count(), 4)
                finally:
                    db.session.remove()
                    db.engine.dispose()

    def test_list_imported_conversations_returns_rows(self):
        fixture = Path("sample_data/chatgpt_export_sample.json")

        with tempfile.TemporaryDirectory() as tmpdir:
            sqlite_path = Path(tmpdir) / "query_list.db"
            import_chatgpt_export_to_sqlite(fixture, sqlite_path)

            rows = list_imported_conversations(sqlite_path)

            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0].source, "chatgpt")
            self.assertEqual(rows[1].source_conversation_id, "conv-1")

    def test_get_imported_conversation_returns_messages_in_sequence_order(self):
        fixture = Path("sample_data/chatgpt_export_sample.json")

        with tempfile.TemporaryDirectory() as tmpdir:
            sqlite_path = Path(tmpdir) / "query_show.db"
            import_chatgpt_export_to_sqlite(fixture, sqlite_path)

            rows = list_imported_conversations(sqlite_path)
            conversation_id = next(
                row.id for row in rows if row.source_conversation_id == "conv-1"
            )

            detail = get_imported_conversation(sqlite_path, conversation_id)

            self.assertIsNotNone(detail)
            assert detail is not None
            self.assertEqual(detail.title, "Trip planning")
            self.assertEqual([m.sequence_index for m in detail.messages], [0, 1, 2])
            self.assertEqual([m.role for m in detail.messages], ["user", "assistant", "user"])

    def test_search_imported_conversations_matches_title_and_content(self):
        fixture = Path("sample_data/chatgpt_export_sample.json")

        with tempfile.TemporaryDirectory() as tmpdir:
            sqlite_path = Path(tmpdir) / "query_search.db"
            import_chatgpt_export_to_sqlite(fixture, sqlite_path)

            title_matches = search_imported_conversations(sqlite_path, "trip")
            self.assertEqual([row.source_conversation_id for row in title_matches], ["conv-1"])

            content_matches = search_imported_conversations(sqlite_path, "No title")
            self.assertEqual([row.source_conversation_id for row in content_matches], ["conv-2"])

    def test_search_imported_conversations_is_case_insensitive_and_deterministic(self):
        fixture = Path("sample_data/chatgpt_export_sample.json")

        with tempfile.TemporaryDirectory() as tmpdir:
            sqlite_path = Path(tmpdir) / "query_search_order.db"
            first = import_chatgpt_export_to_sqlite(fixture, sqlite_path)
            second = import_chatgpt_export_to_sqlite(fixture, sqlite_path)

            self.assertEqual(first.imported_conversations, 2)
            self.assertEqual(first.skipped_conversations, 0)
            self.assertEqual(second.imported_conversations, 0)
            self.assertEqual(second.skipped_conversations, 2)

            rows = search_imported_conversations(sqlite_path, "TRIP")
            self.assertEqual([row.source_conversation_id for row in rows], ["conv-1"])

            empty = search_imported_conversations(sqlite_path, "   ")
            self.assertEqual(empty, [])


    def test_duplicate_import_policy_skips_existing_source_conversation_ids(self):
        fixture = Path("sample_data/chatgpt_export_sample.json")

        with tempfile.TemporaryDirectory() as tmpdir:
            sqlite_path = Path(tmpdir) / "duplicate_policy.db"

            first = import_chatgpt_export_to_sqlite(fixture, sqlite_path)
            second = import_chatgpt_export_to_sqlite(fixture, sqlite_path)

            self.assertEqual(first.imported_conversations, 2)
            self.assertEqual(first.imported_messages, 4)
            self.assertEqual(first.skipped_conversations, 0)

            self.assertEqual(second.imported_conversations, 0)
            self.assertEqual(second.imported_messages, 0)
            self.assertEqual(second.skipped_conversations, 2)

            verify_app = Flask(__name__)
            verify_app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{sqlite_path}"
            verify_app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

            db.init_app(verify_app)
            with verify_app.app_context():
                try:
                    self.assertEqual(ImportedConversation.query.count(), 2)
                    self.assertEqual(ImportedMessage.query.count(), 4)
                finally:
                    db.session.remove()
                    db.engine.dispose()

    def test_render_imported_conversation_markdown_includes_metadata_and_ordered_messages(self):
        fixture = Path("sample_data/chatgpt_export_sample.json")

        with tempfile.TemporaryDirectory() as tmpdir:
            sqlite_path = Path(tmpdir) / "query_export_render.db"
            import_chatgpt_export_to_sqlite(fixture, sqlite_path)

            rows = list_imported_conversations(sqlite_path)
            conversation_id = next(
                row.id for row in rows if row.source_conversation_id == "conv-1"
            )

            detail = get_imported_conversation(sqlite_path, conversation_id)
            self.assertIsNotNone(detail)
            assert detail is not None

            rendered = render_imported_conversation_markdown(detail)

            expected = """# Trip planning

## Conversation Metadata
- Source: chatgpt
- Source Conversation ID: conv-1
- Created At: 1710000000.000 (2024-03-09T16:00:00Z)
- Updated At: 1710000300.000 (2024-03-09T16:05:00Z)

## Messages

### [0] user
- Source Message ID: msg-user-1
- Created At: 1710000001.000 (2024-03-09T16:00:01Z)

Plan me a 2-day trip to Lisbon.

### [1] assistant
- Source Message ID: msg-assistant-1
- Created At: 1710000002.000 (2024-03-09T16:00:02Z)

Day 1: Alfama and Baixa.
Day 2: Belém and LX Factory.

### [2] user
- Source Message ID: msg-user-2
- Created At: 1710000003.000 (2024-03-09T16:00:03Z)

Add food suggestions.
"""
            self.assertEqual(rendered, expected)

    def test_export_imported_conversation_markdown_writes_file(self):
        fixture = Path("sample_data/chatgpt_export_sample.json")

        with tempfile.TemporaryDirectory() as tmpdir:
            sqlite_path = Path(tmpdir) / "query_export_write.db"
            output_path = Path(tmpdir) / "exports" / "conversation.md"
            import_chatgpt_export_to_sqlite(fixture, sqlite_path)

            rows = list_imported_conversations(sqlite_path)
            conversation_id = next(
                row.id for row in rows if row.source_conversation_id == "conv-2"
            )

            output = export_imported_conversation_markdown(sqlite_path, conversation_id, output_path)

            self.assertEqual(output, output_path)
            self.assertTrue(output_path.exists())
            content = output_path.read_text(encoding="utf-8")
            self.assertIn("# Untitled Conversation", content)
            self.assertIn("- Source Conversation ID: conv-2", content)
            self.assertIn("### [0] user", content)

            missing = export_imported_conversation_markdown(sqlite_path, 999999, output_path)
            self.assertIsNone(missing)

if __name__ == "__main__":
    unittest.main()
