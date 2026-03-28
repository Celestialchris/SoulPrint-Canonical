"""Tests for web-triggered passport export and validation."""

from __future__ import annotations

import json
import unittest
from datetime import datetime

from src.app import create_app
from src.app.models import ImportedConversation, ImportedMessage, MemoryEntry
from src.app.models.db import db
from src.config import Config, sqlite_uri_from_path
from tests.temp_helpers import make_test_temp_dir, release_app_db_handles


class PassportWebTest(unittest.TestCase):
    def setUp(self):
        self.workdir = make_test_temp_dir(self, "passport-web")
        self._old_uri = Config.SQLALCHEMY_DATABASE_URI
        self.sqlite_path = self.workdir / "passport_web_test.db"
        Config.SQLALCHEMY_DATABASE_URI = sqlite_uri_from_path(self.sqlite_path)
        self.addCleanup(self._restore_sqlite_uri)

        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.addCleanup(release_app_db_handles, self.app, drop_all=True)

    def _restore_sqlite_uri(self):
        Config.SQLALCHEMY_DATABASE_URI = self._old_uri

    def _seed_data(self):
        """Insert minimal canonical data so export produces a non-empty passport."""
        with self.app.app_context():
            conv = ImportedConversation(
                source="chatgpt",
                source_conversation_id="conv-web-1",
                title="Passport test conversation",
                created_at_unix=1700000000.0,
                updated_at_unix=1700000300.0,
            )
            db.session.add(conv)
            db.session.flush()
            db.session.add(
                ImportedMessage(
                    conversation_id=conv.id,
                    source_message_id="msg-1",
                    role="user",
                    content="Testing passport export from the web.",
                    sequence_index=0,
                    created_at_unix=1700000001.0,
                )
            )
            db.session.add(
                MemoryEntry(
                    timestamp=datetime(2026, 3, 10, 9, 0, 0),
                    role="user",
                    content="Native note for passport test.",
                    tags="test",
                )
            )
            db.session.commit()

    def test_export_returns_200_with_status_ok(self):
        """1. POST /passport/export returns 200 with status ok."""
        self._seed_data()
        response = self.client.post("/passport/export")

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.get_data(as_text=True))
        self.assertEqual(data["status"], "ok")

    def test_export_creates_passport_directory(self):
        """2. POST /passport/export creates a passport directory on disk."""
        self._seed_data()
        response = self.client.post("/passport/export")

        data = json.loads(response.get_data(as_text=True))
        from pathlib import Path

        package_dir = Path(data["path"])
        self.assertTrue(package_dir.exists())
        self.assertTrue((package_dir / "manifest.json").exists())

    def test_export_response_includes_path(self):
        """3. POST /passport/export response includes the output path."""
        self._seed_data()
        response = self.client.post("/passport/export")

        data = json.loads(response.get_data(as_text=True))
        self.assertIn("path", data)
        self.assertIn("memory-passport-v1", data["path"])

    def test_validate_without_export_returns_404(self):
        """4. POST /passport/validate with no prior export returns 404."""
        response = self.client.post("/passport/validate")

        self.assertEqual(response.status_code, 404)
        data = json.loads(response.get_data(as_text=True))
        self.assertEqual(data["status"], "error")
        self.assertIn("No exported passport found", data["message"])

    def test_validate_after_export_returns_result(self):
        """5. POST /passport/validate after export returns validation result."""
        self._seed_data()
        self.client.post("/passport/export")
        response = self.client.post("/passport/validate")

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.get_data(as_text=True))
        self.assertEqual(data["status"], "ok")

    def test_validate_result_includes_valid_boolean(self):
        """6. POST /passport/validate result includes valid boolean."""
        self._seed_data()
        self.client.post("/passport/export")
        response = self.client.post("/passport/validate")

        data = json.loads(response.get_data(as_text=True))
        self.assertIn("valid", data)
        self.assertIsInstance(data["valid"], bool)

    def test_passport_page_has_export_button(self):
        """7. GET /passport page contains 'Export passport' button."""
        response = self.client.get("/passport")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("Export passport", html)
        self.assertIn('id="export-btn"', html)

    def test_passport_page_has_validate_button(self):
        """8. GET /passport page contains 'Validate passport' button."""
        response = self.client.get("/passport")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("Validate passport", html)
        self.assertIn('id="validate-btn"', html)


if __name__ == "__main__":
    unittest.main()
