"""Tests for freemium route gating — Ask and Intelligence require a license."""

from __future__ import annotations

import os
import unittest

from src.app import create_app
from src.app.models.db import db
from src.config import Config
from tests.temp_helpers import make_test_temp_dir, release_app_db_handles


class _FreemiumTestBase(unittest.TestCase):
    """Base class that creates an app with a controlled license state."""

    license_override: str = "false"

    def setUp(self):
        self.workdir = make_test_temp_dir(self, "freemium-gate")
        self._old_uri = Config.SQLALCHEMY_DATABASE_URI
        Config.SQLALCHEMY_DATABASE_URI = f"sqlite:///{self.workdir}/test.db"
        self.addCleanup(self._restore_sqlite_uri)

        self._old_override = os.environ.get("SOULPRINT_LICENSE_OVERRIDE")
        os.environ["SOULPRINT_LICENSE_OVERRIDE"] = self.license_override

        self.app = create_app()
        self.client = self.app.test_client()
        self.addCleanup(release_app_db_handles, self.app, drop_all=True)
        self.addCleanup(self._restore_license_override)

    def _restore_sqlite_uri(self):
        Config.SQLALCHEMY_DATABASE_URI = self._old_uri

    def _restore_license_override(self):
        if self._old_override is None:
            os.environ.pop("SOULPRINT_LICENSE_OVERRIDE", None)
        else:
            os.environ["SOULPRINT_LICENSE_OVERRIDE"] = self._old_override


class UnlicensedAskGatingTest(_FreemiumTestBase):
    """GET /ask shows upgrade page when unlicensed; POST /ask returns 403."""

    license_override = "false"

    def test_ask_get_shows_upgrade_when_unlicensed(self):
        response = self.client.get("/ask")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Go deeper", response.data)

    def test_ask_post_returns_403_when_unlicensed(self):
        response = self.client.post("/ask", data={"question": "test"})
        self.assertEqual(response.status_code, 403)


class UnlicensedIntelligenceGatingTest(_FreemiumTestBase):
    """Intelligence POST routes return 403 when unlicensed."""

    license_override = "false"

    def test_intelligence_summarize_returns_403_when_unlicensed(self):
        response = self.client.post("/intelligence/summarize/1")
        self.assertEqual(response.status_code, 403)

    def test_intelligence_scan_topics_returns_403_when_unlicensed(self):
        response = self.client.post("/intelligence/scan-topics")
        self.assertEqual(response.status_code, 403)


class FreeRoutesUnaffectedTest(_FreemiumTestBase):
    """Free routes return 200 without a license."""

    license_override = "false"

    def test_free_routes_accessible_without_license(self):
        free_routes = [
            "/", "/imported", "/chats", "/federated", "/passport",
            "/answer-traces", "/summary", "/intelligence",
        ]
        for route in free_routes:
            with self.subTest(route=route):
                response = self.client.get(route)
                self.assertEqual(response.status_code, 200, f"{route} returned {response.status_code}")


class WorkspaceTierBadgeTest(_FreemiumTestBase):
    """Workspace page is accessible regardless of license tier."""

    license_override = "false"

    def test_workspace_accessible_when_unlicensed(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("SoulPrint", html)


class WorkspaceProBadgeTest(_FreemiumTestBase):
    """Workspace page is accessible when licensed."""

    license_override = "true"

    def test_workspace_accessible_when_licensed(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("SoulPrint", html)
