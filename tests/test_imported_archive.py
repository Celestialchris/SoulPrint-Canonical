"""Tests for archive/unarchive of imported conversations and related UI behavior."""

from __future__ import annotations

import sqlite3
import unittest

from src.app import create_app
from src.app.models import ImportedConversation, ImportedMessage
from src.app.models.db import db
from src.config import Config
from src.retrieval.fts import ensure_fts_tables, index_new_messages
from tests.temp_helpers import make_test_temp_dir, release_app_db_handles


def _seed_conversation(
    app,
    title: str = "Test conv",
    archived: bool = False,
    source_id: str = "src-001",
    content: str = "Hello world",
) -> int:
    """Insert one conversation + one message; return the conversation id."""
    with app.app_context():
        conv = ImportedConversation(
            source="chatgpt",
            source_conversation_id=source_id,
            title=title,
            created_at_unix=1710000000.0,
            updated_at_unix=1710001000.0,
            is_archived=archived,
        )
        db.session.add(conv)
        db.session.flush()
        db.session.add(ImportedMessage(
            conversation_id=conv.id,
            source_message_id="msg-1",
            role="user",
            content=content,
            sequence_index=0,
            created_at_unix=1710000100.0,
        ))
        db.session.commit()
        return conv.id


class ArchiveRouteTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = make_test_temp_dir(self, "archive-route")
        self.db_path = str(self.tmpdir / "test.db")
        self._old_uri = Config.SQLALCHEMY_DATABASE_URI
        Config.SQLALCHEMY_DATABASE_URI = f"sqlite:///{self.db_path}"
        self.app = create_app()
        self.client = self.app.test_client()
        self.conv_id = _seed_conversation(self.app, title="Archive Me")
        self.addCleanup(release_app_db_handles, self.app, drop_all=True)
        self.addCleanup(self._restore_uri)

    def _restore_uri(self):
        Config.SQLALCHEMY_DATABASE_URI = self._old_uri

    def test_archive_sets_flag(self):
        self.client.post(f"/imported/{self.conv_id}/archive")
        with self.app.app_context():
            conv = ImportedConversation.query.get(self.conv_id)
        self.assertTrue(conv.is_archived)

    def test_archive_is_idempotent(self):
        self.client.post(f"/imported/{self.conv_id}/archive")
        resp = self.client.post(f"/imported/{self.conv_id}/archive")
        self.assertEqual(resp.status_code, 302)
        with self.app.app_context():
            conv = ImportedConversation.query.get(self.conv_id)
        self.assertTrue(conv.is_archived)

    def test_archive_redirects_to_imported(self):
        resp = self.client.post(f"/imported/{self.conv_id}/archive")
        self.assertEqual(resp.status_code, 302)
        location = resp.headers.get("Location", "")
        self.assertIn("/imported", location)
        self.assertNotIn("/imported/archived", location)


class UnarchiveRouteTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = make_test_temp_dir(self, "unarchive-route")
        self.db_path = str(self.tmpdir / "test.db")
        self._old_uri = Config.SQLALCHEMY_DATABASE_URI
        Config.SQLALCHEMY_DATABASE_URI = f"sqlite:///{self.db_path}"
        self.app = create_app()
        self.client = self.app.test_client()
        self.conv_id = _seed_conversation(self.app, title="Already Archived", archived=True)
        self.addCleanup(release_app_db_handles, self.app, drop_all=True)
        self.addCleanup(self._restore_uri)

    def _restore_uri(self):
        Config.SQLALCHEMY_DATABASE_URI = self._old_uri

    def test_unarchive_clears_flag(self):
        self.client.post(f"/imported/{self.conv_id}/unarchive")
        with self.app.app_context():
            conv = ImportedConversation.query.get(self.conv_id)
        self.assertFalse(conv.is_archived)

    def test_unarchive_redirects_to_archived(self):
        resp = self.client.post(f"/imported/{self.conv_id}/unarchive")
        self.assertEqual(resp.status_code, 302)
        location = resp.headers.get("Location", "")
        self.assertIn("/imported/archived", location)


class ImportedListFilterTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = make_test_temp_dir(self, "list-filter")
        self.db_path = str(self.tmpdir / "test.db")
        self._old_uri = Config.SQLALCHEMY_DATABASE_URI
        Config.SQLALCHEMY_DATABASE_URI = f"sqlite:///{self.db_path}"
        self.app = create_app()
        self.client = self.app.test_client()
        self.visible_id = _seed_conversation(
            self.app, title="Visible Conv", archived=False, source_id="src-visible"
        )
        self.hidden_id = _seed_conversation(
            self.app, title="Hidden Conv", archived=True, source_id="src-hidden"
        )
        self.addCleanup(release_app_db_handles, self.app, drop_all=True)
        self.addCleanup(self._restore_uri)

    def _restore_uri(self):
        Config.SQLALCHEMY_DATABASE_URI = self._old_uri

    def test_default_view_excludes_archived(self):
        resp = self.client.get("/imported")
        self.assertEqual(resp.status_code, 200)
        html = resp.get_data(as_text=True)
        self.assertIn("Visible Conv", html)
        self.assertNotIn("Hidden Conv", html)


class ImportedArchivedViewTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = make_test_temp_dir(self, "archived-view")
        self.db_path = str(self.tmpdir / "test.db")
        self._old_uri = Config.SQLALCHEMY_DATABASE_URI
        Config.SQLALCHEMY_DATABASE_URI = f"sqlite:///{self.db_path}"
        self.app = create_app()
        self.client = self.app.test_client()
        self.addCleanup(release_app_db_handles, self.app, drop_all=True)
        self.addCleanup(self._restore_uri)

    def _restore_uri(self):
        Config.SQLALCHEMY_DATABASE_URI = self._old_uri

    def test_archived_page_shows_only_archived(self):
        _seed_conversation(self.app, title="Active Conv", archived=False, source_id="src-a")
        _seed_conversation(self.app, title="Archived Conv", archived=True, source_id="src-b")
        resp = self.client.get("/imported/archived")
        self.assertEqual(resp.status_code, 200)
        html = resp.get_data(as_text=True)
        self.assertIn("Archived Conv", html)
        self.assertNotIn("Active Conv", html)

    def test_empty_state_when_no_archived(self):
        resp = self.client.get("/imported/archived")
        self.assertEqual(resp.status_code, 200)
        html = resp.get_data(as_text=True)
        self.assertIn("Nothing archived yet", html)


class ArchiveDeleteFlowTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = make_test_temp_dir(self, "archive-delete-flow")
        self.db_path = str(self.tmpdir / "test.db")
        self._old_uri = Config.SQLALCHEMY_DATABASE_URI
        Config.SQLALCHEMY_DATABASE_URI = f"sqlite:///{self.db_path}"
        self.app = create_app()
        self.client = self.app.test_client()
        self.conv_id = _seed_conversation(self.app, title="Delete From Archive", archived=True)
        self.addCleanup(release_app_db_handles, self.app, drop_all=True)
        self.addCleanup(self._restore_uri)

    def _restore_uri(self):
        Config.SQLALCHEMY_DATABASE_URI = self._old_uri

    def test_delete_from_archive_shows_confirm(self):
        resp = self.client.get(
            f"/imported/{self.conv_id}/delete?return_url=/imported/archived"
        )
        self.assertEqual(resp.status_code, 200)
        html = resp.get_data(as_text=True)
        self.assertIn('href="/imported/archived"', html)


class ArchiveFtsInvariantTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = make_test_temp_dir(self, "archive-fts")
        self.db_path = str(self.tmpdir / "test.db")
        self._old_uri = Config.SQLALCHEMY_DATABASE_URI
        Config.SQLALCHEMY_DATABASE_URI = f"sqlite:///{self.db_path}"
        self.app = create_app()
        self.client = self.app.test_client()
        self.conv_id = _seed_conversation(
            self.app,
            title="FTS Searchable Conv",
            archived=False,
            source_id="src-fts",
            content="xyzarchiveunique token for fts",
        )
        ensure_fts_tables(self.db_path)
        index_new_messages(self.db_path, self.conv_id)
        self.addCleanup(release_app_db_handles, self.app, drop_all=True)
        self.addCleanup(self._restore_uri)

    def _restore_uri(self):
        Config.SQLALCHEMY_DATABASE_URI = self._old_uri

    def test_archived_conversation_still_searchable(self):
        self.client.post(f"/imported/{self.conv_id}/archive")
        with self.app.app_context():
            conv = ImportedConversation.query.get(self.conv_id)
        self.assertTrue(conv.is_archived)

        resp = self.client.get("/federated?q=xyzarchiveunique")
        self.assertEqual(resp.status_code, 200)
        html = resp.get_data(as_text=True)
        self.assertIn("FTS Searchable Conv", html)


if __name__ == "__main__":
    unittest.main()
