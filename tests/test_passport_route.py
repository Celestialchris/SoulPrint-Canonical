"""Render tests for the `/passport` web surface."""

from __future__ import annotations

import unittest

from src.app import create_app
from src.config import Config
from tests.temp_helpers import make_test_temp_dir, release_app_db_handles


class PassportRouteTest(unittest.TestCase):
    def setUp(self):
        self.workdir = make_test_temp_dir(self, "passport-route")
        self._old_uri = Config.SQLALCHEMY_DATABASE_URI
        Config.SQLALCHEMY_DATABASE_URI = f"sqlite:///{self.workdir}/passport_route.db"
        self.addCleanup(self._restore_sqlite_uri)
        self.app = create_app()
        self.client = self.app.test_client()
        self.addCleanup(release_app_db_handles, self.app, drop_all=True)

    def _restore_sqlite_uri(self):
        Config.SQLALCHEMY_DATABASE_URI = self._old_uri

    def test_passport_route_renders_capability_oriented_sections(self):
        response = self.client.get("/passport")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("What Memory Passport is", html)
        self.assertIn("What export does", html)
        self.assertIn("What validation does", html)
        self.assertIn("Current capability / status", html)
        self.assertIn("Next actions", html)
        self.assertIn("Export is currently available through the existing CLI.", html)
        self.assertIn("Valid with warnings", html)

    def test_passport_route_honestly_reports_no_active_web_artifact_inspection(self):
        response = self.client.get("/passport")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("Artifact inspection in web app:", html)
        self.assertIn("not active", html)
        self.assertIn("not currently inspecting a specific passport artifact path", html)


if __name__ == "__main__":
    unittest.main()
