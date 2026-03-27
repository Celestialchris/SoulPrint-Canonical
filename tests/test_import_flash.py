"""Tests for the post-import flash page."""

from __future__ import annotations

import io
import unittest
from pathlib import Path

from src.app import create_app
from src.config import Config
from tests.temp_helpers import make_test_temp_dir, release_app_db_handles


class ImportFlashRouteTest(unittest.TestCase):
    def setUp(self):
        self.workdir = make_test_temp_dir(self, "import-flash")
        self._old_uri = Config.SQLALCHEMY_DATABASE_URI
        self.addCleanup(self._restore_sqlite_uri)
        self.sqlite_path = self.workdir / "import_flash_test.db"
        Config.SQLALCHEMY_DATABASE_URI = f"sqlite:///{self.sqlite_path}"

        self.app = create_app()
        self.client = self.app.test_client()
        self.addCleanup(release_app_db_handles, self.app, drop_all=True)

    def _restore_sqlite_uri(self):
        Config.SQLALCHEMY_DATABASE_URI = self._old_uri

    def _seed_initial_import(self):
        """Import the fixture once so the DB is non-empty."""
        fixture_bytes = Path("sample_data/chatgpt_export_sample.json").read_bytes()
        self.client.post(
            "/import",
            data={"export_file": (io.BytesIO(fixture_bytes), "chatgpt_export_sample.json")},
            content_type="multipart/form-data",
        )

    # ── Core flash behavior ──────────────────────────────────────

    def test_get_import_complete_without_session_redirects_to_import(self):
        response = self.client.get("/import/complete")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/import", response.headers["Location"])

    def test_get_import_complete_with_session_renders_flash(self):
        with self.client.session_transaction() as sess:
            sess["import_stats"] = {
                "messages_imported": 42,
                "conversations_imported": 3,
                "provider_name": "claude",
            }

        response = self.client.get("/import/complete")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("Brought home.", html)
        self.assertIn("42", html)
        self.assertIn("3", html)

    def test_session_data_consumed_second_get_redirects(self):
        with self.client.session_transaction() as sess:
            sess["import_stats"] = {
                "messages_imported": 10,
                "conversations_imported": 1,
                "provider_name": "chatgpt",
            }

        first = self.client.get("/import/complete")
        self.assertEqual(first.status_code, 200)

        second = self.client.get("/import/complete")
        self.assertEqual(second.status_code, 302)
        self.assertIn("/import", second.headers["Location"])

    # ── Integration with real import ─────────────────────────────

    def test_successful_import_redirects_to_flash(self):
        # Seed so DB is non-empty (first import redirects to /summary)
        self._seed_initial_import()

        # Import a different provider fixture
        fixture_bytes = Path("sample_data/claude_export_sample.json").read_bytes()
        response = self.client.post(
            "/import",
            data={"export_file": (io.BytesIO(fixture_bytes), "claude_export_sample.json")},
            content_type="multipart/form-data",
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn("/import/complete", response.headers["Location"])

    def test_duplicate_import_does_not_redirect_to_flash(self):
        self._seed_initial_import()

        fixture_bytes = Path("sample_data/chatgpt_export_sample.json").read_bytes()
        response = self.client.post(
            "/import",
            data={"export_file": (io.BytesIO(fixture_bytes), "chatgpt_export_sample.json")},
            content_type="multipart/form-data",
        )

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("No new conversations were imported", html)

    def test_flash_page_has_explore_link(self):
        with self.client.session_transaction() as sess:
            sess["import_stats"] = {
                "messages_imported": 100,
                "conversations_imported": 5,
                "provider_name": "gemini",
            }

        response = self.client.get("/import/complete")
        html = response.get_data(as_text=True)
        self.assertIn("/imported", html)
        self.assertIn("Explore your archive", html)

    def test_flash_page_has_summary_link(self):
        with self.client.session_transaction() as sess:
            sess["import_stats"] = {
                "messages_imported": 50,
                "conversations_imported": 2,
                "provider_name": "chatgpt",
            }

        response = self.client.get("/import/complete")
        html = response.get_data(as_text=True)
        self.assertIn("/summary", html)
        self.assertIn("See your summary", html)


if __name__ == "__main__":
    unittest.main()
