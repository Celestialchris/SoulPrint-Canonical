"""Tests for ChatGPT export normalization and SQLite persistence."""

import tempfile
import unittest
from pathlib import Path

from flask import Flask

from src.app.models import ImportedConversation, ImportedMessage
from src.app.models.db import db
from src.importers import parse_chatgpt_export_file, persist_normalized_conversations
from src.importers.cli import import_chatgpt_export_to_sqlite


class ChatGPTImporterTest(unittest.TestCase):
    def test_parse_chatgpt_fixture_normalizes_order_and_title(self):
        fixture = Path("sample_data/chatgpt_export_sample.json")
        conversations = parse_chatgpt_export_file(fixture)

        self.assertEqual(len(conversations), 2)

        first = conversations[0]
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
                db.create_all()
                persist_normalized_conversations([conversations[0]])

                stored_conv = ImportedConversation.query.one()
                self.assertEqual(stored_conv.source, "chatgpt")
                self.assertEqual(stored_conv.title, "Trip planning")

                stored_messages = ImportedMessage.query.order_by(ImportedMessage.sequence_index.asc()).all()
                self.assertEqual(len(stored_messages), 3)
                self.assertEqual(stored_messages[0].content, "Plan me a 2-day trip to Lisbon.")
                self.assertEqual(stored_messages[-1].role, "user")

    def test_cli_import_path_imports_fixture_into_sqlite(self):
        fixture = Path("sample_data/chatgpt_export_sample.json")

        with tempfile.TemporaryDirectory() as tmpdir:
            sqlite_path = Path(tmpdir) / "cli_import.db"
            conversation_count, message_count = import_chatgpt_export_to_sqlite(fixture, sqlite_path)

            self.assertEqual(conversation_count, 2)
            self.assertEqual(message_count, 4)

            verify_app = Flask(__name__)
            verify_app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{sqlite_path}"
            verify_app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

            db.init_app(verify_app)
            with verify_app.app_context():
                self.assertEqual(ImportedConversation.query.count(), 2)
                self.assertEqual(ImportedMessage.query.count(), 4)


if __name__ == "__main__":
    unittest.main()
