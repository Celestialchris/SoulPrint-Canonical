"""Tests for imported conversation list route."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.app import create_app
from src.app.models import ImportedConversation, ImportedMessage
from src.app.models.db import db
from src.config import Config


class ImportedListRouteTest(unittest.TestCase):
    def setUp(self):
        self._old_uri = Config.SQLALCHEMY_DATABASE_URI
        self.tmpdir = tempfile.TemporaryDirectory()
        sqlite_path = Path(self.tmpdir.name) / "imported_list_test.db"
        Config.SQLALCHEMY_DATABASE_URI = f"sqlite:///{sqlite_path}"

        self.app = create_app()
        self.client = self.app.test_client()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
            db.engine.dispose()
        Config.SQLALCHEMY_DATABASE_URI = self._old_uri
        self.tmpdir.cleanup()

    def _seed_conversation(
        self,
        title: str,
        source_id: str,
        message: str,
        *,
        source: str = "chatgpt",
    ) -> int:
        with self.app.app_context():
            conversation = ImportedConversation(
                source=source,
                source_conversation_id=source_id,
                title=title,
                created_at_unix=1710000000.0,
                updated_at_unix=1710000100.0,
            )
            db.session.add(conversation)
            db.session.flush()

            db.session.add(
                ImportedMessage(
                    conversation_id=conversation.id,
                    source_message_id=f"msg-{source_id}",
                    role="user",
                    content=message,
                    sequence_index=0,
                    created_at_unix=1710000001.0,
                )
            )
            db.session.commit()
            return conversation.id

    def test_imported_list_renders_in_descending_canonical_order_with_explorer_links(self):
        older_id = self._seed_conversation("Earlier conversation", "conv-1", "First message")
        newer_id = self._seed_conversation("Later conversation", "conv-2", "Second message")

        response = self.client.get("/imported")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("Imported Conversations", html)

        newer_index = html.index(f"/imported/{newer_id}/explorer")
        older_index = html.index(f"/imported/{older_id}/explorer")
        self.assertLess(newer_index, older_index)

    def test_imported_list_empty_state_is_safe(self):
        response = self.client.get("/imported")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("No imported conversations found.", html)


    def test_imported_list_shows_zero_message_count_for_empty_conversation(self):
        with self.app.app_context():
            conversation = ImportedConversation(
                source="chatgpt",
                source_conversation_id="conv-empty",
                title="No messages yet",
                created_at_unix=1710000000.0,
                updated_at_unix=1710000100.0,
            )
            db.session.add(conversation)
            db.session.commit()

        response = self.client.get("/imported")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("No messages yet", html)
        self.assertIn("Messages: 0", html)

    def test_imported_list_query_filters_by_title_and_message_content(self):
        self._seed_conversation("Lisbon plans", "conv-title", "Talk about travel")
        self._seed_conversation("Untitled", "conv-message", "Need pasta recommendations")

        title_response = self.client.get("/imported?q=lisbon")
        self.assertEqual(title_response.status_code, 200)
        title_html = title_response.get_data(as_text=True)
        self.assertIn("Lisbon plans", title_html)
        self.assertNotIn("Need pasta recommendations", title_html)

        content_response = self.client.get("/imported?q=pasta")
        self.assertEqual(content_response.status_code, 200)
        content_html = content_response.get_data(as_text=True)
        self.assertIn("Untitled", content_html)
        self.assertNotIn("Lisbon plans", content_html)

    def test_imported_list_shows_provider_identity_for_non_chatgpt_source(self):
        self._seed_conversation(
            "Claude notes",
            "claude-conv-1",
            "Cross-LLM continuity",
            source="claude",
        )

        response = self.client.get("/imported")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("Provider: claude", html)
        self.assertIn("Source Conversation ID: claude-conv-1", html)


if __name__ == "__main__":
    unittest.main()
