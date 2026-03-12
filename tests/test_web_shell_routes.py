"""Focused render tests for the shared web shell routes."""

from __future__ import annotations

import unittest
from datetime import datetime

from src.app import create_app
from src.app.models import MemoryEntry
from src.app.models.db import db
from src.config import Config
from tests.temp_helpers import make_test_temp_dir, release_app_db_handles


class WebShellRouteTest(unittest.TestCase):
    def setUp(self):
        self.workdir = make_test_temp_dir(self, "web-shell")
        self._old_uri = Config.SQLALCHEMY_DATABASE_URI
        self.addCleanup(self._restore_sqlite_uri)
        sqlite_path = self.workdir / "web_shell_test.db"
        Config.SQLALCHEMY_DATABASE_URI = f"sqlite:///{sqlite_path}"

        self.app = create_app()
        self.client = self.app.test_client()
        self.addCleanup(release_app_db_handles, self.app, drop_all=True)

    def _restore_sqlite_uri(self):
        Config.SQLALCHEMY_DATABASE_URI = self._old_uri

    def test_home_route_renders_shared_navigation_shell(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("app-topbar", html)
        self.assertIn("Workspace", html)
        self.assertIn('href="/chats"', html)
        self.assertIn('href="/imported"', html)
        self.assertIn('href="/import"', html)
        self.assertIn('href="/federated"', html)
        self.assertIn('href="/answer-traces"', html)

    def test_chats_route_renders_shared_shell_and_memory_detail_links(self):
        with self.app.app_context():
            entry = MemoryEntry(
                timestamp=datetime(2026, 3, 10, 9, 0, 0),
                role="user",
                content="Track the bakery shortlist in the native lane.",
                tags="bakery,planning",
            )
            db.session.add(entry)
            db.session.commit()
            entry_id = entry.id

        response = self.client.get("/chats")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("app-topbar", html)
        self.assertIn("Native Memory", html)
        self.assertIn('href="/memory/{}"'.format(entry_id), html)
        self.assertIn("Filter by tag", html)


if __name__ == "__main__":
    unittest.main()
