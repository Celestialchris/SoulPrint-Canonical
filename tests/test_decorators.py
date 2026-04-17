"""Tests for the @require_license decorator."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from src.app import create_app
from src.app.models.db import db
from src.config import Config
from tests.temp_helpers import make_test_temp_dir, release_app_db_handles


class RequireLicenseDecoratorTest(unittest.TestCase):
    """Verify @require_license gates routes correctly."""

    def setUp(self):
        self.workdir = make_test_temp_dir(self, "decorator-test")
        self._old_uri = Config.SQLALCHEMY_DATABASE_URI
        Config.SQLALCHEMY_DATABASE_URI = f"sqlite:///{self.workdir}/test.db"
        self.addCleanup(self._restore_sqlite_uri)

        self.app = create_app()
        self.client = self.app.test_client()
        self.addCleanup(release_app_db_handles, self.app, drop_all=True)

    def _restore_sqlite_uri(self):
        Config.SQLALCHEMY_DATABASE_URI = self._old_uri

    @patch("src.app.is_licensed", return_value=True)
    def test_licensed_get_passes_through(self, _mock):
        """Licensed users reach the actual route handler."""
        response = self.client.get("/ask")
        self.assertEqual(response.status_code, 200)
        # The ask form should render, not the upgrade page.
        self.assertNotIn(b"Unlock Ask, themes, and continuity", response.data)

    @patch("src.app.is_licensed", return_value=True)
    def test_licensed_post_passes_through(self, _mock):
        """Licensed POST requests reach the route handler."""
        response = self.client.post("/intelligence/scan-topics")
        # Route will fail without LLM config, but should NOT be 403.
        self.assertNotEqual(response.status_code, 403)

    @patch("src.app.is_licensed", return_value=False)
    def test_unlicensed_get_renders_upgrade(self, _mock):
        """Unlicensed GET shows the upgrade page with 200."""
        response = self.client.get("/ask")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Unlock Ask, themes, and continuity", response.data)

    @patch("src.app.is_licensed", return_value=False)
    def test_unlicensed_post_returns_403(self, _mock):
        """Unlicensed POST returns 403 Forbidden."""
        response = self.client.post("/ask", data={"question": "test"})
        self.assertEqual(response.status_code, 403)

    @patch("src.app.is_licensed", return_value=False)
    def test_unlicensed_intelligence_post_returns_403(self, _mock):
        """Unlicensed POST to intelligence routes returns 403."""
        routes = [
            "/intelligence/summarize/1",
            "/intelligence/scan-topics",
        ]
        for route in routes:
            with self.subTest(route=route):
                response = self.client.post(route)
                self.assertEqual(response.status_code, 403)

    @patch("src.app.is_licensed", return_value=False)
    def test_unlicensed_distill_get_renders_upgrade(self, _mock):
        """Unlicensed GET /distill shows upgrade page."""
        response = self.client.get("/distill")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Unlock Ask, themes, and continuity", response.data)
