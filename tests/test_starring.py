"""Tests for star/unstar routes on imported conversations and memory notes."""

from __future__ import annotations

import unittest
from datetime import datetime

from src.app import create_app
from src.app.models import ImportedConversation, ImportedMessage, MemoryEntry
from src.app.models.db import db
from src.config import Config
from tests.temp_helpers import make_test_temp_dir, release_app_db_handles


def _seed_conversation(
    app,
    title: str = "Test conv",
    starred: bool = False,
    source_id: str = "src-001",
) -> int:
    """Insert one conversation + one message; return the conversation id."""
    with app.app_context():
        conv = ImportedConversation(
            source="chatgpt",
            source_conversation_id=source_id,
            title=title,
            created_at_unix=1710000000.0,
            updated_at_unix=1710001000.0,
            is_starred=starred,
        )
        db.session.add(conv)
        db.session.flush()
        db.session.add(
            ImportedMessage(
                conversation_id=conv.id,
                source_message_id="msg-1",
                role="user",
                content="Hello world",
                sequence_index=0,
                created_at_unix=1710000100.0,
            )
        )
        db.session.commit()
        return conv.id


def _seed_memory(
    app,
    content: str = "Test note",
    starred: bool = False,
) -> int:
    """Insert one memory entry; return its id."""
    with app.app_context():
        entry = MemoryEntry(
            timestamp=datetime(2024, 1, 1, 12, 0, 0),
            role="user",
            content=content,
            is_starred=starred,
        )
        db.session.add(entry)
        db.session.commit()
        return entry.id


class StarImportedRouteTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = make_test_temp_dir(self, "star-imported")
        self.db_path = str(self.tmpdir / "test.db")
        self._old_uri = Config.SQLALCHEMY_DATABASE_URI
        Config.SQLALCHEMY_DATABASE_URI = f"sqlite:///{self.db_path}"
        self.app = create_app()
        self.client = self.app.test_client()
        self.conv_id = _seed_conversation(self.app, title="Star Me", source_id="src-star")
        self.addCleanup(release_app_db_handles, self.app, drop_all=True)
        self.addCleanup(self._restore_uri)

    def _restore_uri(self):
        Config.SQLALCHEMY_DATABASE_URI = self._old_uri

    def test_star_sets_flag(self):
        self.client.post(f"/imported/{self.conv_id}/star")
        with self.app.app_context():
            conv = ImportedConversation.query.get(self.conv_id)
        self.assertTrue(conv.is_starred)

    def test_star_is_idempotent(self):
        self.client.post(f"/imported/{self.conv_id}/star")
        resp = self.client.post(f"/imported/{self.conv_id}/star")
        self.assertEqual(resp.status_code, 302)
        with self.app.app_context():
            conv = ImportedConversation.query.get(self.conv_id)
        self.assertTrue(conv.is_starred)

    def test_star_respects_next(self):
        resp = self.client.post(
            f"/imported/{self.conv_id}/star",
            data={"next": "/federated?q=hello"},
        )
        self.assertEqual(resp.status_code, 302)
        location = resp.headers.get("Location", "")
        self.assertIn("/federated", location)

    def test_star_rejects_bad_next(self):
        bad_inputs = (
            "//evil.com",
            "http://evil.com",
            "https://evil.com/path",
            "\\\\evil.com",
            "/\\evil.com",
            "javascript:alert(1)",
            "",
        )
        for bad in bad_inputs:
            with self.subTest(next=bad):
                resp = self.client.post(
                    f"/imported/{self.conv_id}/star",
                    data={"next": bad},
                )
                self.assertEqual(resp.status_code, 302)
                location = resp.headers.get("Location", "")
                self.assertNotIn("evil.com", location)
                self.assertNotIn("javascript", location)
                self.assertIn("/federated", location)


class UnstarImportedRouteTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = make_test_temp_dir(self, "unstar-imported")
        self.db_path = str(self.tmpdir / "test.db")
        self._old_uri = Config.SQLALCHEMY_DATABASE_URI
        Config.SQLALCHEMY_DATABASE_URI = f"sqlite:///{self.db_path}"
        self.app = create_app()
        self.client = self.app.test_client()
        self.conv_id = _seed_conversation(
            self.app, title="Already Starred", starred=True, source_id="src-unstar"
        )
        self.addCleanup(release_app_db_handles, self.app, drop_all=True)
        self.addCleanup(self._restore_uri)

    def _restore_uri(self):
        Config.SQLALCHEMY_DATABASE_URI = self._old_uri

    def test_unstar_clears_flag(self):
        self.client.post(f"/imported/{self.conv_id}/unstar")
        with self.app.app_context():
            conv = ImportedConversation.query.get(self.conv_id)
        self.assertFalse(conv.is_starred)

    def test_unstar_default_redirect(self):
        resp = self.client.post(f"/imported/{self.conv_id}/unstar")
        self.assertEqual(resp.status_code, 302)
        location = resp.headers.get("Location", "")
        self.assertIn("/federated", location)


class StarMemoryRouteTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = make_test_temp_dir(self, "star-memory")
        self.db_path = str(self.tmpdir / "test.db")
        self._old_uri = Config.SQLALCHEMY_DATABASE_URI
        Config.SQLALCHEMY_DATABASE_URI = f"sqlite:///{self.db_path}"
        self.app = create_app()
        self.client = self.app.test_client()
        self.memory_id = _seed_memory(self.app, content="A note to star")
        self.addCleanup(release_app_db_handles, self.app, drop_all=True)
        self.addCleanup(self._restore_uri)

    def _restore_uri(self):
        Config.SQLALCHEMY_DATABASE_URI = self._old_uri

    def test_star_sets_flag(self):
        self.client.post(f"/memory/{self.memory_id}/star")
        with self.app.app_context():
            entry = MemoryEntry.query.get(self.memory_id)
        self.assertTrue(entry.is_starred)

    def test_star_is_idempotent(self):
        self.client.post(f"/memory/{self.memory_id}/star")
        resp = self.client.post(f"/memory/{self.memory_id}/star")
        self.assertEqual(resp.status_code, 302)
        with self.app.app_context():
            entry = MemoryEntry.query.get(self.memory_id)
        self.assertTrue(entry.is_starred)

    def test_star_respects_next(self):
        resp = self.client.post(
            f"/memory/{self.memory_id}/star",
            data={"next": "/chats?tag=important"},
        )
        self.assertEqual(resp.status_code, 302)
        location = resp.headers.get("Location", "")
        self.assertIn("/chats", location)

    def test_star_rejects_bad_next(self):
        bad_inputs = (
            "//evil.com",
            "http://evil.com",
            "https://evil.com/path",
            "\\\\evil.com",
            "/\\evil.com",
            "javascript:alert(1)",
            "",
        )
        for bad in bad_inputs:
            with self.subTest(next=bad):
                resp = self.client.post(
                    f"/memory/{self.memory_id}/star",
                    data={"next": bad},
                )
                self.assertEqual(resp.status_code, 302)
                location = resp.headers.get("Location", "")
                self.assertNotIn("evil.com", location)
                self.assertNotIn("javascript", location)
                self.assertIn("/chats", location)


class UnstarMemoryRouteTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = make_test_temp_dir(self, "unstar-memory")
        self.db_path = str(self.tmpdir / "test.db")
        self._old_uri = Config.SQLALCHEMY_DATABASE_URI
        Config.SQLALCHEMY_DATABASE_URI = f"sqlite:///{self.db_path}"
        self.app = create_app()
        self.client = self.app.test_client()
        self.memory_id = _seed_memory(self.app, content="A starred note", starred=True)
        self.addCleanup(release_app_db_handles, self.app, drop_all=True)
        self.addCleanup(self._restore_uri)

    def _restore_uri(self):
        Config.SQLALCHEMY_DATABASE_URI = self._old_uri

    def test_unstar_clears_flag(self):
        self.client.post(f"/memory/{self.memory_id}/unstar")
        with self.app.app_context():
            entry = MemoryEntry.query.get(self.memory_id)
        self.assertFalse(entry.is_starred)

    def test_unstar_default_redirect(self):
        resp = self.client.post(f"/memory/{self.memory_id}/unstar")
        self.assertEqual(resp.status_code, 302)
        location = resp.headers.get("Location", "")
        self.assertIn("/chats", location)


class StarRenderingTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = make_test_temp_dir(self, "star-rendering")
        self.db_path = str(self.tmpdir / "test.db")
        self._old_uri = Config.SQLALCHEMY_DATABASE_URI
        Config.SQLALCHEMY_DATABASE_URI = f"sqlite:///{self.db_path}"
        self.app = create_app()
        self.client = self.app.test_client()
        _seed_conversation(self.app, title="Browse Conv", source_id="src-render")
        _seed_memory(self.app, content="Browse note")
        self.addCleanup(release_app_db_handles, self.app, drop_all=True)
        self.addCleanup(self._restore_uri)

    def _restore_uri(self):
        Config.SQLALCHEMY_DATABASE_URI = self._old_uri

    def test_star_glyph_appears_on_federated_browse(self):
        resp = self.client.get("/federated")
        self.assertEqual(resp.status_code, 200)
        html = resp.get_data(as_text=True)
        self.assertIn("☆ Star", html)


if __name__ == "__main__":
    unittest.main()
