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


class TestConversationExportEdgeCases(unittest.TestCase):
    """Edge cases: missing title, null timestamps, filename sanitization."""

    def setUp(self):
        self.workdir = make_test_temp_dir(self, "conv-export-edge")
        self._old_uri = Config.SQLALCHEMY_DATABASE_URI
        Config.SQLALCHEMY_DATABASE_URI = f"sqlite:///{self.workdir}/edge.db"
        self.addCleanup(self._restore_sqlite_uri)

        self.app = create_app()
        self.client = self.app.test_client()
        self.addCleanup(release_app_db_handles, self.app, drop_all=True)

    def _restore_sqlite_uri(self):
        Config.SQLALCHEMY_DATABASE_URI = self._old_uri

    def _create_conv(self, title: str, *, created=None, messages=None):
        with self.app.app_context():
            db.create_all()
            conv = ImportedConversation(
                source="chatgpt",
                source_conversation_id=f"edge-{title or 'empty'}",
                title=title,
                created_at_unix=1700000000,
                updated_at_unix=1700001000,
            )
            db.session.add(conv)
            db.session.flush()
            for i, (role, content, ts) in enumerate(messages or []):
                db.session.add(ImportedMessage(
                    conversation_id=conv.id,
                    source_message_id=f"m{i}",
                    role=role,
                    content=content,
                    sequence_index=i,
                    created_at_unix=ts,
                ))
            db.session.commit()
            return conv.id

    def test_empty_title_falls_back_to_untitled(self):
        conv_id = self._create_conv("", messages=[("user", "hi", 1700000000)])
        response = self.client.get(f"/imported/{conv_id}/export")
        self.assertEqual(response.status_code, 200)
        text = response.data.decode("utf-8")
        self.assertIn("# Untitled conversation", text)
        self.assertIn("Untitled conversation", response.headers["Content-Disposition"])

    def test_title_with_only_illegal_chars_uses_generic_filename(self):
        conv_id = self._create_conv("/<>", messages=[("user", "hi", 1700000000)])
        response = self.client.get(f"/imported/{conv_id}/export")
        self.assertEqual(response.status_code, 200)
        self.assertIn('filename="conversation.md"', response.headers["Content-Disposition"])

    def test_message_with_no_timestamp_has_no_italic_line(self):
        conv_id = self._create_conv("Plain", messages=[("user", "text", None)])
        response = self.client.get(f"/imported/{conv_id}/export")
        text = response.data.decode("utf-8")
        self.assertIn("### User", text)
        self.assertIn("text", text)
        lines = text.split("\n")
        user_idx = lines.index("### User")
        self.assertFalse(lines[user_idx + 1].startswith("*"))

    def test_epoch_zero_timestamp_still_emits_italic_line(self):
        conv_id = self._create_conv("Epoch", messages=[("user", "hi", 0)])
        response = self.client.get(f"/imported/{conv_id}/export")
        text = response.data.decode("utf-8")
        lines = text.split("\n")
        user_idx = lines.index("### User")
        self.assertTrue(
            lines[user_idx + 1].startswith("*"),
            f"Expected italic timestamp line for epoch=0, got: {lines[user_idx + 1]!r}",
        )

    def test_dots_in_title_are_preserved_in_filename(self):
        conv_id = self._create_conv(
            "My.notes.v2", messages=[("user", "hi", 1700000000)]
        )
        response = self.client.get(f"/imported/{conv_id}/export")
        dispo = response.headers["Content-Disposition"]
        self.assertIn("My.notes.v2.md", dispo)

    def test_special_chars_in_title_sanitized(self):
        conv_id = self._create_conv(
            "Project/Alpha: v2 <beta>",
            messages=[("user", "x", 1700000000)],
        )
        response = self.client.get(f"/imported/{conv_id}/export")
        dispo = response.headers["Content-Disposition"]
        self.assertNotIn("/", dispo.split("filename=")[1])
        self.assertNotIn("<", dispo)
        self.assertNotIn(">", dispo)
        self.assertIn(".md", dispo)
