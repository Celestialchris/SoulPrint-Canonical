"""Tests for the /inbox cockpit routes (Campaign 03, B3)."""

from __future__ import annotations

import unittest
import uuid

from src.app import create_app
from src.app.models import Capture
from src.app.models.db import db
from src.capture.content_hash import CONTENT_HASH_RECIPE_VERSION
from src.config import Config
from tests.temp_helpers import (
    make_test_temp_dir,
    release_app_db_handles,
    temp_soulprint_home,
)


class _InboxRouteTestBase(unittest.TestCase):
    """Full-app setUp shared by every /inbox route test."""

    def setUp(self):
        self.home = temp_soulprint_home(self, "inbox-route-home")
        self.workdir = make_test_temp_dir(self, "inbox-route-db")
        self.db_path = str(self.workdir / "inbox-route.db")
        self._old_uri = Config.SQLALCHEMY_DATABASE_URI
        Config.SQLALCHEMY_DATABASE_URI = f"sqlite:///{self.db_path}"
        self.app = create_app()
        self.addCleanup(release_app_db_handles, self.app, drop_all=True)
        self.addCleanup(self._restore_uri)
        self.client = self.app.test_client()

    def _restore_uri(self):
        Config.SQLALCHEMY_DATABASE_URI = self._old_uri

    def _make_capture(self, **overrides):
        """Insert a Capture row directly and return its id.

        A unique content_hash is generated per row because the capture table
        carries a unique index on it.
        """

        fields = dict(
            adapter_id="soulprint-cli",
            adapter_version="1",
            payload_kind="paste",
            body_text="capture body text",
            content_hash=uuid.uuid4().hex,
            content_hash_recipe_version=CONTENT_HASH_RECIPE_VERSION,
            raw_payload_hash="raw-payload-hash",
            captured_at_unix=1747227600.0,
            received_at_unix=1747227601.0,
            status="pending",
        )
        fields.update(overrides)
        with self.app.app_context():
            row = Capture(**fields)
            db.session.add(row)
            db.session.commit()
            return row.id


class InboxGetRouteTest(_InboxRouteTestBase):
    """Tests for GET /inbox, the read-only cockpit view."""

    def test_get_inbox_renders_pending_rows(self):
        self._make_capture(body_text="first pending capture")
        self._make_capture(body_text="second pending capture")

        response = self.client.get("/inbox")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("first pending capture", html)
        self.assertIn("second pending capture", html)

    def test_get_inbox_filters_out_terminal_states(self):
        self._make_capture(body_text="visible pending capture", status="pending")
        self._make_capture(body_text="hidden promoted capture", status="promoted")
        self._make_capture(body_text="hidden rejected capture", status="rejected")

        response = self.client.get("/inbox")

        html = response.get_data(as_text=True)
        self.assertIn("visible pending capture", html)
        self.assertNotIn("hidden promoted capture", html)
        self.assertNotIn("hidden rejected capture", html)

    def test_get_inbox_orders_by_received_at_desc(self):
        self._make_capture(body_text="older capture", received_at_unix=1000.0)
        self._make_capture(body_text="newer capture", received_at_unix=2000.0)

        response = self.client.get("/inbox")

        html = response.get_data(as_text=True)
        self.assertLess(
            html.index("newer capture"), html.index("older capture")
        )

    def test_get_inbox_empty_renders_terse_message(self):
        response = self.client.get("/inbox")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("Inbox empty", html)
        # The terse line is a metadata-note paragraph, not the empty_state macro.
        self.assertNotIn("empty-state", html)


if __name__ == "__main__":
    unittest.main()
