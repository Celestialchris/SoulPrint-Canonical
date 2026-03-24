"""Tests for read-only native memory detail route."""

from __future__ import annotations

import unittest
from datetime import datetime

from src.app import create_app
from src.app.models import MemoryEntry
from src.app.models.db import db
from src.config import Config
from tests.temp_helpers import make_test_temp_dir, release_app_db_handles


class MemoryDetailRouteTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = make_test_temp_dir(self, "memory-detail")
        self._old_uri = Config.SQLALCHEMY_DATABASE_URI
        self.addCleanup(self._restore_sqlite_uri)
        sqlite_path = self.tmpdir / "memory_detail_test.db"
        Config.SQLALCHEMY_DATABASE_URI = f"sqlite:///{sqlite_path}"

        self.app = create_app()
        self.client = self.app.test_client()
        self.addCleanup(release_app_db_handles, self.app, drop_all=True)

    def _restore_sqlite_uri(self):
        Config.SQLALCHEMY_DATABASE_URI = self._old_uri

    def _seed_entry(self) -> int:
        with self.app.app_context():
            entry = MemoryEntry(
                timestamp=datetime(2026, 3, 10, 12, 30, 0),
                role="assistant",
                content="Remember the Lisbon bakery shortlist and budget notes.",
                tags="travel,food",
            )
            db.session.add(entry)
            db.session.commit()
            return entry.id

    def test_memory_detail_route_renders_successfully(self):
        entry_id = self._seed_entry()

        response = self.client.get(f"/memory/{entry_id}")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("Your note", html)
        self.assertIn(f"memory:{entry_id}", html)

    def test_missing_memory_entry_returns_404(self):
        response = self.client.get("/memory/9999")
        self.assertEqual(response.status_code, 404)

    def test_memory_detail_renders_stable_id_and_metadata(self):
        entry_id = self._seed_entry()

        response = self.client.get(f"/memory/{entry_id}?from=federated&q=lisbon")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn(f"memory:{entry_id}", html)
        self.assertIn("2026-03-10T12:30:00Z", html)
        self.assertIn("assistant", html)
        self.assertIn("travel,food", html)
        self.assertIn("Remember the Lisbon bakery shortlist and budget notes.", html)
        self.assertIn('href="/federated?q=lisbon"', html)
        self.assertIn('href="/chats"', html)


if __name__ == "__main__":
    unittest.main()
