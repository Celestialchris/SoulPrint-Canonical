"""Tests for the GET /healthz route."""

from __future__ import annotations

import json
import unittest

from src.app import create_app
from src.config import Config
from tests.temp_helpers import make_test_temp_dir, release_app_db_handles


class HealthzRouteTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = make_test_temp_dir(self, "healthz-route")
        self.db_path = str(self.tmpdir / "test.db")
        self._old_uri = Config.SQLALCHEMY_DATABASE_URI
        Config.SQLALCHEMY_DATABASE_URI = f"sqlite:///{self.db_path}"
        self.app = create_app()
        self.client = self.app.test_client()
        self.addCleanup(release_app_db_handles, self.app, drop_all=True)
        self.addCleanup(self._restore_uri)

    def _restore_uri(self):
        Config.SQLALCHEMY_DATABASE_URI = self._old_uri

    def test_healthz_returns_status_200(self):
        resp = self.client.get("/healthz")
        self.assertEqual(resp.status_code, 200)

    def test_healthz_response_json_has_ok_true(self):
        resp = self.client.get("/healthz")
        data = json.loads(resp.data)
        self.assertTrue(data.get("ok"))

    def test_healthz_does_not_require_database_contents(self):
        # No seeding; route should still report healthy.
        resp = self.client.get("/healthz")
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertTrue(data.get("ok"))


if __name__ == "__main__":
    unittest.main()
