"""Tests for the /chats route — starred imports section."""

from __future__ import annotations

import unittest
from datetime import datetime

from src.app import create_app
from src.app.models import ImportedConversation, MemoryEntry
from src.app.models.db import db
from src.config import Config
from tests.temp_helpers import make_test_temp_dir, release_app_db_handles


def _seed_conversation(
    app,
    title: str = "Test Conversation",
    starred: bool = False,
    source_id: str = "src-001",
    tags: str = "",
) -> int:
    with app.app_context():
        conv = ImportedConversation(
            source="chatgpt",
            source_conversation_id=source_id,
            title=title,
            created_at_unix=1710000000.0,
            updated_at_unix=1710001000.0,
            is_starred=starred,
            tags=tags,
        )
        db.session.add(conv)
        db.session.commit()
        return conv.id


def _seed_memory(
    app,
    content: str = "Test note",
    tags: str = "",
) -> int:
    with app.app_context():
        entry = MemoryEntry(
            timestamp=datetime(2024, 3, 1, 12, 0, 0),
            role="user",
            content=content,
            tags=tags,
        )
        db.session.add(entry)
        db.session.commit()
        return entry.id


class ChatsRouteTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = make_test_temp_dir(self, "chats-route")
        self.db_path = str(self.tmpdir / "test.db")
        self._old_uri = Config.SQLALCHEMY_DATABASE_URI
        Config.SQLALCHEMY_DATABASE_URI = f"sqlite:///{self.db_path}"
        self.app = create_app()
        self.client = self.app.test_client()
        self.addCleanup(release_app_db_handles, self.app, drop_all=True)
        self.addCleanup(self._restore_uri)

    def _restore_uri(self):
        Config.SQLALCHEMY_DATABASE_URI = self._old_uri

    def test_chats_shows_starred_imported_conversation(self):
        _seed_conversation(self.app, title="Starred Chat", starred=True)
        resp = self.client.get("/chats")
        self.assertEqual(resp.status_code, 200)
        body = resp.data.decode()
        self.assertIn("Starred Chat", body)
        self.assertIn("/imported/", body)
        self.assertIn("/explorer", body)

    def test_chats_does_not_show_unstarred_imported_conversation(self):
        _seed_conversation(self.app, title="Unstarred Chat", starred=False)
        resp = self.client.get("/chats")
        self.assertEqual(resp.status_code, 200)
        body = resp.data.decode()
        self.assertNotIn("Unstarred Chat", body)

    def test_chats_shows_existing_notes_alongside_starred_imports(self):
        _seed_memory(self.app, content="My personal note")
        _seed_conversation(self.app, title="Starred Import", starred=True, source_id="src-002")
        resp = self.client.get("/chats")
        self.assertEqual(resp.status_code, 200)
        body = resp.data.decode()
        self.assertIn("My personal note", body)
        self.assertIn("Starred Import", body)

    def test_chats_tag_filter_applies_to_starred_imports(self):
        _seed_conversation(
            self.app, title="Tagged Convo", starred=True, source_id="src-003", tags="foo"
        )
        resp_match = self.client.get("/chats?tag=foo")
        self.assertEqual(resp_match.status_code, 200)
        self.assertIn("Tagged Convo", resp_match.data.decode())

        resp_no_match = self.client.get("/chats?tag=bar")
        self.assertEqual(resp_no_match.status_code, 200)
        self.assertNotIn("Tagged Convo", resp_no_match.data.decode())

    def test_chats_empty_state_when_no_notes_and_no_starred_imports(self):
        resp = self.client.get("/chats")
        self.assertEqual(resp.status_code, 200)
        body = resp.data.decode()
        self.assertIn("No notes yet", body)

    def test_chats_starred_imports_empty_state_when_only_notes(self):
        _seed_memory(self.app, content="Just a note")
        resp = self.client.get("/chats")
        self.assertEqual(resp.status_code, 200)
        body = resp.data.decode()
        self.assertIn("No starred conversations yet", body)
