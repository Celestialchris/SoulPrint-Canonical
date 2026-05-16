"""Tests for the /inbox cockpit routes (Campaign 03, B3)."""

from __future__ import annotations

import unittest
import uuid
from unittest.mock import patch

from src.app import create_app
from src.app.models import Capture, MemoryEntry
from src.app.models.db import db
from src.capture.content_hash import CONTENT_HASH_RECIPE_VERSION
from src.capture.paths import new_dir
from src.capture.service import CaptureEnvelope, record_capture, triage_capture
from src.config import Config
from tests.temp_helpers import (
    make_test_temp_dir,
    release_app_db_handles,
    temp_soulprint_home,
)

_LOCAL_ORIGIN = "http://localhost"


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

    def _record_capture(self, **overrides):
        """Persist a capture via record_capture and return its id.

        Unlike _make_capture, this writes the real inbox/new/<uuid>.json
        mirror, which the filesystem-mirror retention tests inspect.
        """

        fields = dict(
            adapter_id="soulprint-cli",
            adapter_version="1",
            payload_kind="paste",
            body_text="recorded capture body",
            body_html=None,
            source_url="https://example.com/recorded",
            source_title="Recorded capture",
            metadata=None,
            hints=None,
            captured_at_unix=1747227615.5,
        )
        fields.update(overrides)
        with self.app.app_context():
            return record_capture(CaptureEnvelope(**fields)).capture_id


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


class InboxPromoteRouteTest(_InboxRouteTestBase):
    """Tests for POST /inbox/<id>/promote."""

    def test_promote_transitions_capture_and_redirects(self):
        cap_id = self._make_capture(status="pending", body_text="promote me")

        response = self.client.post(
            f"/inbox/{cap_id}/promote", headers={"Origin": _LOCAL_ORIGIN}
        )

        self.assertEqual(response.status_code, 303)
        with self.app.app_context():
            row = db.session.get(Capture, cap_id)
            self.assertEqual(row.status, "promoted")
            entry = db.session.get(MemoryEntry, row.promoted_to_id)
            self.assertIsNotNone(entry)
            self.assertEqual(entry.captured_via_id, cap_id)

    def test_promote_indexes_new_memory_in_fts(self):
        cap_id = self._make_capture(status="pending")

        with patch("src.retrieval.fts.index_new_note") as mock_index:
            response = self.client.post(
                f"/inbox/{cap_id}/promote", headers={"Origin": _LOCAL_ORIGIN}
            )

        self.assertEqual(response.status_code, 303)
        with self.app.app_context():
            memory_entry_id = db.session.get(Capture, cap_id).promoted_to_id
        mock_index.assert_called_once()
        self.assertEqual(mock_index.call_args[0][1], memory_entry_id)

    def test_promote_survives_fts_failure(self):
        cap_id = self._make_capture(status="pending")

        with patch(
            "src.retrieval.fts.index_new_note",
            side_effect=RuntimeError("FTS index unavailable"),
        ):
            response = self.client.post(
                f"/inbox/{cap_id}/promote", headers={"Origin": _LOCAL_ORIGIN}
            )

        self.assertEqual(response.status_code, 303)
        with self.app.app_context():
            self.assertEqual(db.session.get(Capture, cap_id).status, "promoted")

    def test_promote_terminal_capture_returns_409(self):
        cap_id = self._make_capture(status="promoted")

        response = self.client.post(
            f"/inbox/{cap_id}/promote", headers={"Origin": _LOCAL_ORIGIN}
        )

        self.assertEqual(response.status_code, 409)

    def test_promote_missing_capture_returns_404(self):
        response = self.client.post(
            "/inbox/999999/promote", headers={"Origin": _LOCAL_ORIGIN}
        )

        self.assertEqual(response.status_code, 404)

    def test_promote_race_loss_returns_409(self):
        cap_id = self._make_capture(status="pending")

        def racing_transition(*args):
            # A competing reject commits between the pre-flight read and the
            # compare-and-swap, exactly as a concurrent decision would.
            db.session.execute(
                db.update(Capture)
                .where(Capture.id == cap_id)
                .values(
                    status="rejected",
                    decided_at_unix=1.0,
                    decided_by="race-winner",
                    reject_reason="raced",
                )
            )
            db.session.commit()

        with patch("src.capture.service.transition", racing_transition):
            response = self.client.post(
                f"/inbox/{cap_id}/promote", headers={"Origin": _LOCAL_ORIGIN}
            )

        self.assertEqual(response.status_code, 409)
        with self.app.app_context():
            self.assertEqual(db.session.query(MemoryEntry).count(), 0)


class InboxRejectRouteTest(_InboxRouteTestBase):
    """Tests for POST /inbox/<id>/reject."""

    def test_reject_transitions_capture_and_redirects(self):
        cap_id = self._make_capture(status="pending")

        response = self.client.post(
            f"/inbox/{cap_id}/reject",
            data={"reason": "spam content"},
            headers={"Origin": _LOCAL_ORIGIN},
        )

        self.assertEqual(response.status_code, 303)
        with self.app.app_context():
            row = db.session.get(Capture, cap_id)
            self.assertEqual(row.status, "rejected")
            self.assertEqual(row.reject_reason, "spam content")
            self.assertEqual(row.decided_by, "operator")

    def test_reject_retains_filesystem_mirror(self):
        cap_id = self._record_capture()
        with self.app.app_context():
            self.assertEqual(len(list(new_dir().glob("*.json"))), 1)

        response = self.client.post(
            f"/inbox/{cap_id}/reject",
            data={"reason": "rejected after review"},
            headers={"Origin": _LOCAL_ORIGIN},
        )

        self.assertEqual(response.status_code, 303)
        with self.app.app_context():
            self.assertEqual(len(list(new_dir().glob("*.json"))), 1)

    def test_reject_without_reason_returns_400(self):
        cap_id = self._make_capture(status="pending")

        response = self.client.post(
            f"/inbox/{cap_id}/reject",
            data={"reason": "   "},
            headers={"Origin": _LOCAL_ORIGIN},
        )

        self.assertEqual(response.status_code, 400)
        with self.app.app_context():
            self.assertEqual(db.session.get(Capture, cap_id).status, "pending")

    def test_reject_terminal_capture_returns_409(self):
        cap_id = self._make_capture(status="promoted")

        response = self.client.post(
            f"/inbox/{cap_id}/reject",
            data={"reason": "too late"},
            headers={"Origin": _LOCAL_ORIGIN},
        )

        self.assertEqual(response.status_code, 409)


class InboxQuarantineRouteTest(_InboxRouteTestBase):
    """Tests for POST /inbox/<id>/quarantine."""

    def test_quarantine_transitions_capture_and_redirects(self):
        cap_id = self._make_capture(status="pending")

        response = self.client.post(
            f"/inbox/{cap_id}/quarantine",
            data={"reason": "needs review"},
            headers={"Origin": _LOCAL_ORIGIN},
        )

        self.assertEqual(response.status_code, 303)
        with self.app.app_context():
            row = db.session.get(Capture, cap_id)
            self.assertEqual(row.status, "quarantined")
            self.assertEqual(row.quarantine_reason, "needs review")
            self.assertEqual(row.decided_by, "operator")

    def test_quarantine_retains_filesystem_mirror(self):
        cap_id = self._record_capture()
        with self.app.app_context():
            self.assertEqual(len(list(new_dir().glob("*.json"))), 1)

        response = self.client.post(
            f"/inbox/{cap_id}/quarantine",
            data={"reason": "held for review"},
            headers={"Origin": _LOCAL_ORIGIN},
        )

        self.assertEqual(response.status_code, 303)
        with self.app.app_context():
            self.assertEqual(len(list(new_dir().glob("*.json"))), 1)

    def test_quarantined_capture_recoverable_via_triage_service(self):
        cap_id = self._make_capture(status="pending")
        self.client.post(
            f"/inbox/{cap_id}/quarantine",
            data={"reason": "hold"},
            headers={"Origin": _LOCAL_ORIGIN},
        )

        with self.app.app_context():
            triage_capture(cap_id)
            self.assertEqual(db.session.get(Capture, cap_id).status, "triaged")


class InboxOriginGuardTest(_InboxRouteTestBase):
    """Tests for the same-origin guard on the inbox action routes."""

    def test_action_with_matching_origin_is_allowed(self):
        cap_id = self._make_capture(status="pending")

        response = self.client.post(
            f"/inbox/{cap_id}/promote", headers={"Origin": _LOCAL_ORIGIN}
        )

        self.assertEqual(response.status_code, 303)

    def test_action_with_foreign_origin_returns_403(self):
        cap_id = self._make_capture(status="pending")

        response = self.client.post(
            f"/inbox/{cap_id}/promote",
            headers={"Origin": "http://evil.example.com"},
        )

        self.assertEqual(response.status_code, 403)
        with self.app.app_context():
            self.assertEqual(db.session.get(Capture, cap_id).status, "pending")

    def test_action_without_origin_header_returns_403(self):
        cap_id = self._make_capture(status="pending")

        response = self.client.post(f"/inbox/{cap_id}/promote")

        self.assertEqual(response.status_code, 403)
        with self.app.app_context():
            self.assertEqual(db.session.get(Capture, cap_id).status, "pending")


class InboxActionFormsTest(_InboxRouteTestBase):
    """Tests that GET /inbox renders the three per-row action forms."""

    def test_get_inbox_renders_action_forms(self):
        cap_id = self._make_capture(status="pending")

        response = self.client.get("/inbox")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn(f"/inbox/{cap_id}/promote", html)
        self.assertIn(f"/inbox/{cap_id}/reject", html)
        self.assertIn(f"/inbox/{cap_id}/quarantine", html)
        self.assertIn('name="reason"', html)


if __name__ == "__main__":
    unittest.main()
