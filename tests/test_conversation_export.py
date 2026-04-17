"""Tests for single-conversation markdown export."""

from __future__ import annotations

import unittest

from src.app import create_app
from src.app.models import ImportedConversation, ImportedMessage
from src.app.models.db import db
from src.config import Config
from tests.temp_helpers import make_test_temp_dir, release_app_db_handles


class TestConversationExport(unittest.TestCase):
    def setUp(self):
        self.workdir = make_test_temp_dir(self, "conv-export")
        self._old_uri = Config.SQLALCHEMY_DATABASE_URI
        Config.SQLALCHEMY_DATABASE_URI = f"sqlite:///{self.workdir}/export_test.db"
        self.addCleanup(self._restore_sqlite_uri)

        self.app = create_app()
        self.client = self.app.test_client()
        self.addCleanup(release_app_db_handles, self.app, drop_all=True)

        with self.app.app_context():
            db.create_all()
            conv = ImportedConversation(
                source="chatgpt",
                source_conversation_id="export-test-1",
                title="Test Export Conversation",
                created_at_unix=1700000000,
                updated_at_unix=1700001000,
            )
            db.session.add(conv)
            db.session.flush()
            msg1 = ImportedMessage(
                conversation_id=conv.id,
                source_message_id="m1",
                role="user",
                content="Hello, how are you?",
                sequence_index=0,
                created_at_unix=1700000000,
            )
            msg2 = ImportedMessage(
                conversation_id=conv.id,
                source_message_id="m2",
                role="assistant",
                content="I'm doing well, thanks for asking!",
                sequence_index=1,
                created_at_unix=1700000100,
            )
            db.session.add_all([msg1, msg2])
            db.session.commit()
            self.conv_id = conv.id

    def _restore_sqlite_uri(self):
        Config.SQLALCHEMY_DATABASE_URI = self._old_uri

    def test_export_returns_markdown(self):
        response = self.client.get(f"/imported/{self.conv_id}/export")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/markdown", response.content_type)

    def test_export_contains_title(self):
        response = self.client.get(f"/imported/{self.conv_id}/export")
        text = response.data.decode("utf-8")
        self.assertIn("# Test Export Conversation", text)

    def test_export_contains_messages(self):
        response = self.client.get(f"/imported/{self.conv_id}/export")
        text = response.data.decode("utf-8")
        self.assertIn("Hello, how are you?", text)
        self.assertIn("I'm doing well, thanks for asking!", text)

    def test_export_contains_provider(self):
        response = self.client.get(f"/imported/{self.conv_id}/export")
        text = response.data.decode("utf-8")
        self.assertIn("**Provider:** chatgpt", text)

    def test_export_has_download_header(self):
        response = self.client.get(f"/imported/{self.conv_id}/export")
        self.assertIn("attachment", response.headers.get("Content-Disposition", ""))

    def test_export_404_for_nonexistent(self):
        response = self.client.get("/imported/99999/export")
        self.assertEqual(response.status_code, 404)
