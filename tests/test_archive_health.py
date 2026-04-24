"""Render tests for the /archive/health page."""

from __future__ import annotations

import sqlite3
import time
import unittest

from src.app import create_app
from src.app.models import ImportRun
from src.app.models.db import db
from src.config import Config
from tests.temp_helpers import make_test_temp_dir, release_app_db_handles


class ArchiveHealthRouteTest(unittest.TestCase):
    def setUp(self):
        self.workdir = make_test_temp_dir(self, "archive-health-route")
        self.db_path = str(self.workdir / "test.db")
        self._old_uri = Config.SQLALCHEMY_DATABASE_URI
        Config.SQLALCHEMY_DATABASE_URI = f"sqlite:///{self.db_path}"
        self.addCleanup(self._restore_sqlite_uri)
        self.app = create_app()
        self.client = self.app.test_client()
        self.addCleanup(release_app_db_handles, self.app, drop_all=True)

    def _restore_sqlite_uri(self):
        Config.SQLALCHEMY_DATABASE_URI = self._old_uri

    def test_archive_health_renders_200(self):
        response = self.client.get("/archive/health")
        self.assertEqual(response.status_code, 200)

    def test_archive_health_shows_each_check_label(self):
        response = self.client.get("/archive/health")
        html = response.get_data(as_text=True)
        for label in [
            "Database file exists",
            "SQLite integrity check",
            "Core tables present",
            "FTS tables present",
            "No orphan messages",
        ]:
            self.assertIn(label, html, msg=f"Missing check label: {label}")

    def test_archive_health_shows_all_five_providers(self):
        from src.importers.contracts import PROVIDER_DISPLAY_NAMES
        response = self.client.get("/archive/health")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        for display_name in PROVIDER_DISPLAY_NAMES.values():
            self.assertIn(display_name, html, msg=f"Missing provider display name: {display_name}")

    def test_archive_health_shows_never_imported_for_empty_provider(self):
        response = self.client.get("/archive/health")
        html = response.get_data(as_text=True)
        self.assertIn("Never imported", html)

    def test_archive_health_shows_last_import_row_when_history_exists(self):
        with self.app.app_context():
            db.session.add(ImportRun(
                provider="chatgpt",
                filename="export.json",
                imported_at=time.time() - 3600,
                status="success",
                conversations_imported=5,
                messages_imported=42,
                conversations_skipped=1,
                conversations_failed=0,
                error_message=None,
            ))
            db.session.commit()
        response = self.client.get("/archive/health")
        html = response.get_data(as_text=True)
        self.assertIn("success", html)
        self.assertIn("5 imported", html)

    def test_archive_health_shows_fail_when_fts_tables_missing(self):
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("DROP TABLE IF EXISTS fts_messages")
            conn.execute("DROP TABLE IF EXISTS fts_notes")
            conn.commit()
        finally:
            conn.close()
        response = self.client.get("/archive/health")
        html = response.get_data(as_text=True)
        self.assertIn("FAIL", html)

    def test_archive_health_shows_db_path(self):
        response = self.client.get("/archive/health")
        html = response.get_data(as_text=True)
        # normalize to forward slashes: normalize_sqlite_uri converts the URI to forward
        # slashes on Windows, so the rendered path uses "/" not "\\"
        db_path_normalized = self.db_path.replace("\\", "/")
        self.assertIn(db_path_normalized, html)

    def test_archive_health_shows_not_tracked_for_pre_instrumentation_provider(self):
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                "INSERT INTO imported_conversation "
                "(source, source_conversation_id, title, created_at_unix, updated_at_unix, is_archived, is_starred, tags) "
                "VALUES (?, ?, ?, ?, ?, 0, 0, '')",
                ("chatgpt", "test-conv-001", "Test convo", 1700000000.0, 1700000000.0),
            )
            conn.commit()
        finally:
            conn.close()
        response = self.client.get("/archive/health")
        html = response.get_data(as_text=True)
        self.assertIn("Not tracked", html)
        self.assertIn("1 conversations", html)

    def test_archive_health_shows_never_imported_for_zero_conversation_provider(self):
        response = self.client.get("/archive/health")
        html = response.get_data(as_text=True)
        self.assertIn("Never imported", html)
        # "Archive has N conversations" only appears in the pre-instrumentation branch
        self.assertNotIn("Archive has", html)

    def test_archive_health_mixed_state_renders_all_three_branches(self):
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                "INSERT INTO imported_conversation "
                "(source, source_conversation_id, title, created_at_unix, updated_at_unix, is_archived, is_starred, tags) "
                "VALUES (?, ?, ?, ?, ?, 0, 0, '')",
                ("chatgpt", "pre-track-001", "Old chat", 1700000000.0, 1700000000.0),
            )
            conn.commit()
        finally:
            conn.close()
        with self.app.app_context():
            db.session.add(ImportRun(
                provider="gemini",
                filename="gemini.json",
                imported_at=time.time(),
                status="success",
                conversations_imported=3,
                messages_imported=12,
                conversations_skipped=0,
                conversations_failed=0,
                error_message=None,
            ))
            db.session.commit()
        response = self.client.get("/archive/health")
        html = response.get_data(as_text=True)
        self.assertIn("Not tracked", html)
        self.assertIn("success", html)
        self.assertIn("Never imported", html)


if __name__ == "__main__":
    unittest.main()
