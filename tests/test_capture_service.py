"""Tests for the record_capture persistence service."""

from __future__ import annotations

import sqlite3
import time
import unittest
import uuid
from unittest.mock import patch

from flask import Flask

from src.app.models import Capture, MemoryEntry
from src.app.models.db import db
from src.capture.content_hash import (
    CONTENT_HASH_RECIPE_VERSION,
    canonical_json,
    content_hash,
    sha256_hex,
)
from src.capture.lifecycle import InvalidTransitionError
from src.capture.paths import ensure_inbox_layout, new_dir, tmp_dir
from src.capture.registry import CaptureContractError
from src.capture.service import (
    CaptureEnvelope,
    CaptureNotFoundError,
    CaptureResult,
    LifecycleResult,
    PromoteResult,
    promote_capture,
    quarantine_capture,
    record_capture,
    reject_capture,
    triage_capture,
)
from tests.temp_helpers import (
    make_test_temp_dir,
    release_app_db_handles,
    temp_soulprint_home,
)


def _make_envelope(**overrides) -> CaptureEnvelope:
    """Build a valid default capture envelope; keyword overrides replace fields."""

    fields = dict(
        adapter_id="soulprint-cli",
        adapter_version="1",
        payload_kind="paste",
        body_text="hello world",
        body_html=None,
        source_url="https://example.com/a",
        source_title="Example",
        metadata=None,
        hints=None,
        captured_at_unix=1747227615.5,
    )
    fields.update(overrides)
    return CaptureEnvelope(**fields)


class RecordCaptureTest(unittest.TestCase):
    def setUp(self):
        # Inbox is redirected under a temp SOULPRINT_HOME; the DB lives in its
        # own temp dir. release_app_db_handles is registered after both temp
        # dirs so it runs first (LIFO) and frees SQLite handles before cleanup.
        self.home = temp_soulprint_home(self, "capture-service-home")
        self.workdir = make_test_temp_dir(self, "capture-service-db")
        self.db_path = str(self.workdir / "capture-service.db")

        self.app = Flask(__name__)
        self.app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{self.db_path}"
        self.app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        db.init_app(self.app)
        with self.app.app_context():
            db.create_all()
        self.addCleanup(release_app_db_handles, self.app, drop_all=True)

    def test_record_capture_persists_pending_row(self):
        with self.app.app_context():
            result = record_capture(_make_envelope())
            row = db.session.get(Capture, result.capture_id)

            self.assertIsNotNone(row)
            self.assertEqual(row.status, "pending")

    def test_record_capture_returns_capture_result(self):
        with self.app.app_context():
            result = record_capture(_make_envelope())

        self.assertIsInstance(result, CaptureResult)
        self.assertFalse(result.existed)
        self.assertIsInstance(result.capture_id, int)
        self.assertTrue(result.content_hash)
        self.assertTrue(result.raw_payload_hash)
        self.assertTrue(result.filesystem_path.startswith("new/"))
        self.assertTrue(result.filesystem_path.endswith(".json"))

    def test_record_capture_sets_content_hash_recipe_version(self):
        with self.app.app_context():
            result = record_capture(_make_envelope())
            row = db.session.get(Capture, result.capture_id)

            self.assertEqual(
                row.content_hash_recipe_version, CONTENT_HASH_RECIPE_VERSION
            )

    def test_record_capture_computes_content_hash(self):
        envelope = _make_envelope()
        expected = content_hash(
            envelope.adapter_id,
            envelope.payload_kind,
            envelope.body_text,
            envelope.source_url,
            envelope.captured_at_unix,
        )

        with self.app.app_context():
            result = record_capture(envelope)
            row = db.session.get(Capture, result.capture_id)

            self.assertEqual(result.content_hash, expected)
            self.assertEqual(row.content_hash, expected)

    def test_record_capture_computes_raw_payload_hash(self):
        envelope = _make_envelope()
        expected = sha256_hex(canonical_json(envelope))

        with self.app.app_context():
            result = record_capture(envelope)
            row = db.session.get(Capture, result.capture_id)

            self.assertEqual(result.raw_payload_hash, expected)
            self.assertEqual(row.raw_payload_hash, expected)

    def test_record_capture_dedup_returns_existing(self):
        envelope = _make_envelope()

        with self.app.app_context():
            first = record_capture(envelope)
            second = record_capture(envelope)
            row_count = db.session.query(Capture).count()

        self.assertFalse(first.existed)
        self.assertTrue(second.existed)
        self.assertEqual(first.capture_id, second.capture_id)
        self.assertEqual(row_count, 1)

    def test_record_capture_dedup_skips_filesystem_write(self):
        envelope = _make_envelope()

        with self.app.app_context():
            record_capture(envelope)
        after_first = list(new_dir().glob("*.json"))

        with self.app.app_context():
            second = record_capture(envelope)
        after_second = list(new_dir().glob("*.json"))

        self.assertEqual(len(after_first), 1)
        self.assertEqual(len(after_second), 1)
        self.assertTrue(second.existed)

    def test_record_capture_dedup_absorbs_insert_race(self):
        # A duplicate content_hash committed between the dedup pre-check and
        # the insert is absorbed by the unique-index IntegrityError fallback.
        # ensure_inbox_layout is the seam: it runs in that exact window.
        envelope = _make_envelope()
        expected_hash = content_hash(
            envelope.adapter_id,
            envelope.payload_kind,
            envelope.body_text,
            envelope.source_url,
            envelope.captured_at_unix,
        )

        def racing_layout():
            # Commit a row with the same content_hash, exactly as a concurrent
            # capture would, so record_capture's own insert loses the race;
            # then run the real layout the patched call stands in for.
            db.session.add(
                Capture(
                    adapter_id="soulprint-cli",
                    adapter_version="1",
                    payload_kind="paste",
                    body_text="winning body",
                    content_hash=expected_hash,
                    content_hash_recipe_version=CONTENT_HASH_RECIPE_VERSION,
                    raw_payload_hash="winner-raw-payload-hash",
                    captured_at_unix=1.0,
                    received_at_unix=2.0,
                    status="pending",
                )
            )
            db.session.commit()
            ensure_inbox_layout()

        with self.app.app_context():
            with patch("src.capture.service.ensure_inbox_layout", racing_layout):
                result = record_capture(envelope)
            winner = (
                db.session.query(Capture)
                .filter_by(content_hash=expected_hash)
                .one()
            )
            winner_id = winner.id
            row_count = db.session.query(Capture).count()

        self.assertTrue(result.existed)
        self.assertEqual(result.capture_id, winner_id)
        self.assertEqual(result.content_hash, expected_hash)
        # The dedup result carries the stored winner's raw_payload_hash, never
        # the rejected incoming envelope's.
        self.assertEqual(result.raw_payload_hash, "winner-raw-payload-hash")
        # The winner row stored no filesystem mirror; the result mirrors that.
        self.assertIsNone(result.filesystem_path)
        # The losing insert left no extra row behind...
        self.assertEqual(row_count, 1)
        # ...and removed its own filesystem mirror instead of orphaning it.
        self.assertEqual(len(list(new_dir().glob("*.json"))), 0)

    def test_record_capture_writes_inbox_new_json(self):
        with self.app.app_context():
            result = record_capture(_make_envelope())

        new_files = list(new_dir().glob("*.json"))
        tmp_files = list(tmp_dir().glob("*.json"))

        self.assertEqual(len(new_files), 1)
        self.assertEqual(len(tmp_files), 0)
        self.assertEqual(result.filesystem_path, f"new/{new_files[0].name}")

    def test_record_capture_rejects_unknown_adapter(self):
        envelope = _make_envelope(adapter_id="does-not-exist")

        with self.app.app_context():
            with self.assertRaises(CaptureContractError):
                record_capture(envelope)

    def test_record_capture_rejects_disallowed_payload_kind(self):
        # soulprint-app-clip permits only the "clip-from-message" payload kind.
        envelope = _make_envelope(
            adapter_id="soulprint-app-clip", payload_kind="paste"
        )

        with self.app.app_context():
            with self.assertRaises(CaptureContractError):
                record_capture(envelope)

    def test_record_capture_rejects_oversized_body(self):
        # soulprint-app-save caps the body at 64 KiB.
        oversized = "a" * (64 * 1024 + 1)
        envelope = _make_envelope(
            adapter_id="soulprint-app-save",
            payload_kind="paste",
            body_text=oversized,
        )

        with self.app.app_context():
            with self.assertRaises(CaptureContractError):
                record_capture(envelope)

    def test_record_capture_validates_before_hashing(self):
        # An oversized body must be rejected by validate_envelope before any
        # hashing or canonicalization runs, so the adapter size cap actually
        # protects the capture path from doomed-payload CPU and allocations.
        oversized = "a" * (64 * 1024 + 1)
        envelope = _make_envelope(
            adapter_id="soulprint-app-save",
            payload_kind="paste",
            body_text=oversized,
        )

        def explode(*args, **kwargs):
            raise AssertionError("hashing ran before validation")

        with self.app.app_context():
            with (
                patch("src.capture.service.content_hash", explode),
                patch("src.capture.service.canonical_json", explode),
                self.assertRaises(CaptureContractError),
            ):
                record_capture(envelope)

            row_count = db.session.query(Capture).count()

        self.assertEqual(row_count, 0)
        self.assertEqual(len(list(new_dir().glob("*.json"))), 0)

    def test_capture_table_uses_sqlite_autoincrement(self):
        # The live app builds the capture schema via db.create_all(), so the
        # model must emit AUTOINCREMENT to match migration 001 and keep
        # capture ids monotonic (SQLite reuses plain rowids after a delete).
        conn = sqlite3.connect(self.db_path)
        self.addCleanup(conn.close)
        row = conn.execute(
            "SELECT sql FROM sqlite_master "
            "WHERE type='table' AND name='capture'"
        ).fetchone()

        self.assertIsNotNone(row)
        self.assertIn("AUTOINCREMENT", row[0])

    def test_capture_timestamp_indexes_preserve_desc_ordering(self):
        # The model is the create_all schema source; its timestamp indexes
        # must emit DESC to match migration 001. The migration uses
        # CREATE INDEX IF NOT EXISTS, so it cannot repair an ASC index the
        # model path already created under the same name.
        conn = sqlite3.connect(self.db_path)
        self.addCleanup(conn.close)
        index_sql = dict(
            conn.execute(
                "SELECT name, sql FROM sqlite_master WHERE type='index' "
                "AND name IN ('idx_capture_received_at', 'idx_capture_adapter')"
            ).fetchall()
        )

        self.assertIn(
            "received_at_unix DESC", index_sql["idx_capture_received_at"]
        )
        self.assertIn(
            "captured_at_unix DESC", index_sql["idx_capture_adapter"]
        )


def _make_capture(**overrides) -> Capture:
    """Build and persist a Capture ORM row; keyword overrides replace fields.

    A unique content_hash is generated per row unless overridden, because
    idx_capture_content_hash is a unique index. Callers must hold an active
    Flask application context.
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
    row = Capture(**fields)
    db.session.add(row)
    db.session.commit()
    return row


class _LifecycleServiceTestBase(unittest.TestCase):
    """Bare-Flask + temp-home setUp shared by the lifecycle service tests."""

    def setUp(self):
        self.home = temp_soulprint_home(self, "capture-lifecycle-home")
        self.workdir = make_test_temp_dir(self, "capture-lifecycle-db")
        self.db_path = str(self.workdir / "capture-lifecycle.db")

        self.app = Flask(__name__)
        self.app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{self.db_path}"
        self.app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        db.init_app(self.app)
        with self.app.app_context():
            db.create_all()
        self.addCleanup(release_app_db_handles, self.app, drop_all=True)


class RejectCaptureTest(_LifecycleServiceTestBase):
    def test_reject_capture_sets_terminal_state(self):
        with self.app.app_context():
            cap_id = _make_capture(status="pending").id

            result = reject_capture(cap_id, "spam content", decided_by="tester")

            row = db.session.get(Capture, cap_id)
            self.assertEqual(row.status, "rejected")
            self.assertIsInstance(result, LifecycleResult)
            self.assertEqual(result.from_status, "pending")
            self.assertEqual(result.to_status, "rejected")

    def test_reject_capture_sets_decision_metadata(self):
        with self.app.app_context():
            cap_id = _make_capture(status="pending").id

            before = time.time()
            result = reject_capture(cap_id, "low quality", decided_by="curator")
            after = time.time()

            row = db.session.get(Capture, cap_id)
            self.assertEqual(row.reject_reason, "low quality")
            self.assertEqual(row.decided_by, "curator")
            self.assertIsNotNone(row.decided_at_unix)
            self.assertGreaterEqual(row.decided_at_unix, before)
            self.assertLessEqual(row.decided_at_unix, after)
            # A rejected row carries no quarantine reason.
            self.assertIsNone(row.quarantine_reason)
            self.assertEqual(result.decided_by, "curator")
            self.assertEqual(result.decided_at_unix, row.decided_at_unix)

    def test_reject_capture_from_quarantined(self):
        # quarantined -> rejected is a valid matrix edge: a held capture can
        # be rejected outright without first returning to triaged.
        with self.app.app_context():
            cap_id = _make_capture(status="quarantined").id

            result = reject_capture(cap_id, "decided junk", decided_by="curator")

            row = db.session.get(Capture, cap_id)
            self.assertEqual(row.status, "rejected")
            self.assertEqual(result.from_status, "quarantined")

    def test_reject_capture_retains_filesystem_mirror(self):
        # A rejected payload is audit-trail evidence; the inbox file stays.
        with self.app.app_context():
            cap_id = record_capture(_make_envelope()).capture_id
            self.assertEqual(len(list(new_dir().glob("*.json"))), 1)

            reject_capture(cap_id, "rejected after review", decided_by="tester")

            self.assertEqual(len(list(new_dir().glob("*.json"))), 1)

    def test_reject_capture_raises_on_terminal_source(self):
        with self.app.app_context():
            cap_id = _make_capture(status="promoted").id

            with self.assertRaises(InvalidTransitionError):
                reject_capture(cap_id, "too late", decided_by="tester")

    def test_reject_capture_raises_on_missing_id(self):
        with self.app.app_context():
            with self.assertRaises(CaptureNotFoundError):
                reject_capture(999999, "no such row", decided_by="tester")

    def test_reject_capture_requires_decided_by_keyword(self):
        # decided_by is keyword-only: a positional third argument is rejected.
        with self.app.app_context():
            cap_id = _make_capture(status="pending").id

            with self.assertRaises(TypeError):
                reject_capture(cap_id, "reason", "tester")

    def test_reject_capture_concurrent_safe(self):
        # A competing terminal transition commits between the pre-flight read
        # and the compare-and-swap; the loser sees rowcount 0 and raises
        # rather than overwriting the winner or mixing reason columns.
        with self.app.app_context():
            cap_id = _make_capture(status="pending").id

            def racing_transition(*args):
                db.session.execute(
                    db.update(Capture)
                    .where(Capture.id == cap_id)
                    .values(
                        status="rejected",
                        decided_at_unix=111.0,
                        decided_by="race-winner",
                        reject_reason="winner reason",
                    )
                )
                db.session.commit()

            with patch("src.capture.service.transition", racing_transition):
                with self.assertRaises(InvalidTransitionError):
                    reject_capture(cap_id, "loser reason", decided_by="loser")

            row = db.session.get(Capture, cap_id)
            self.assertEqual(row.status, "rejected")
            self.assertEqual(row.reject_reason, "winner reason")
            self.assertEqual(row.decided_by, "race-winner")
            self.assertIsNone(row.quarantine_reason)


class QuarantineCaptureTest(_LifecycleServiceTestBase):
    def test_quarantine_capture_sets_terminal_state(self):
        with self.app.app_context():
            cap_id = _make_capture(status="pending").id

            result = quarantine_capture(
                cap_id, "needs review", decided_by="curator"
            )

            row = db.session.get(Capture, cap_id)
            self.assertEqual(row.status, "quarantined")
            self.assertEqual(row.quarantine_reason, "needs review")
            self.assertEqual(row.decided_by, "curator")
            self.assertIsNotNone(row.decided_at_unix)
            # A quarantined row carries no reject reason.
            self.assertIsNone(row.reject_reason)
            self.assertEqual(result.to_status, "quarantined")
            self.assertEqual(result.decided_by, "curator")

    def test_quarantine_capture_retains_filesystem_mirror(self):
        with self.app.app_context():
            cap_id = record_capture(_make_envelope()).capture_id
            self.assertEqual(len(list(new_dir().glob("*.json"))), 1)

            quarantine_capture(cap_id, "held for review", decided_by="tester")

            self.assertEqual(len(list(new_dir().glob("*.json"))), 1)

    def test_quarantine_capture_recoverable_via_triage(self):
        # quarantined -> triaged is the documented recovery edge.
        with self.app.app_context():
            cap_id = _make_capture(status="pending").id
            quarantine_capture(cap_id, "hold", decided_by="curator")

            result = triage_capture(cap_id)

            row = db.session.get(Capture, cap_id)
            self.assertEqual(row.status, "triaged")
            self.assertEqual(result.from_status, "quarantined")
            self.assertEqual(result.to_status, "triaged")


class TriageCaptureTest(_LifecycleServiceTestBase):
    def test_triage_capture_from_pending(self):
        with self.app.app_context():
            cap_id = _make_capture(status="pending").id

            result = triage_capture(cap_id)

            row = db.session.get(Capture, cap_id)
            self.assertEqual(row.status, "triaged")
            self.assertEqual(result.from_status, "pending")
            self.assertEqual(result.to_status, "triaged")

    def test_triage_capture_from_quarantined(self):
        with self.app.app_context():
            cap_id = _make_capture(status="quarantined").id

            result = triage_capture(cap_id)

            row = db.session.get(Capture, cap_id)
            self.assertEqual(row.status, "triaged")
            self.assertEqual(result.from_status, "quarantined")

    def test_triage_capture_raises_on_invalid_source(self):
        with self.app.app_context():
            cap_id = _make_capture(status="promoted").id

            with self.assertRaises(InvalidTransitionError):
                triage_capture(cap_id)

    def test_triage_sets_triaged_at_unix_only(self):
        with self.app.app_context():
            cap_id = _make_capture(status="pending").id

            before = time.time()
            triage_capture(cap_id)
            after = time.time()

            row = db.session.get(Capture, cap_id)
            self.assertIsNotNone(row.triaged_at_unix)
            self.assertGreaterEqual(row.triaged_at_unix, before)
            self.assertLessEqual(row.triaged_at_unix, after)
            # Triage is not a decision: decided columns stay NULL.
            self.assertIsNone(row.decided_at_unix)
            self.assertIsNone(row.decided_by)

    def test_triage_returns_none_for_decided_fields(self):
        with self.app.app_context():
            cap_id = _make_capture(status="pending").id

            result = triage_capture(cap_id)

            self.assertIsNone(result.decided_at_unix)
            self.assertIsNone(result.decided_by)


class PromoteCaptureTest(_LifecycleServiceTestBase):
    def test_promote_capture_creates_memory_entry(self):
        with self.app.app_context():
            cap_id = _make_capture(status="pending", body_text="promote me").id

            result = promote_capture(cap_id, decided_by="curator")

            self.assertIsInstance(result, PromoteResult)
            entry = db.session.get(MemoryEntry, result.memory_entry_id)
            self.assertIsNotNone(entry)
            self.assertEqual(entry.content, "promote me")
            self.assertEqual(entry.role, "user")
            self.assertIsNotNone(entry.timestamp)

    def test_promote_capture_links_captured_via_id(self):
        with self.app.app_context():
            cap_id = _make_capture(status="pending").id

            result = promote_capture(cap_id, decided_by="curator")

            entry = db.session.get(MemoryEntry, result.memory_entry_id)
            self.assertEqual(entry.captured_via_id, cap_id)

    def test_promote_capture_sets_promotion_metadata(self):
        with self.app.app_context():
            cap_id = _make_capture(status="triaged").id

            before = time.time()
            result = promote_capture(cap_id, decided_by="curator")
            after = time.time()

            row = db.session.get(Capture, cap_id)
            self.assertEqual(row.status, "promoted")
            self.assertEqual(row.promoted_to_kind, "memory_entry")
            self.assertEqual(row.promoted_to_id, result.memory_entry_id)
            self.assertEqual(row.decided_by, "curator")
            self.assertGreaterEqual(row.decided_at_unix, before)
            self.assertLessEqual(row.decided_at_unix, after)
            self.assertEqual(result.from_status, "triaged")

    def test_promote_capture_carries_tags_parameter(self):
        with self.app.app_context():
            cap_id = _make_capture(status="pending", tags="capture-tag").id

            result = promote_capture(
                cap_id, decided_by="curator", tags="explicit-tag"
            )

            entry = db.session.get(MemoryEntry, result.memory_entry_id)
            self.assertEqual(entry.tags, "explicit-tag")

    def test_promote_capture_falls_back_to_capture_tags(self):
        with self.app.app_context():
            cap_id = _make_capture(status="pending", tags="capture-tag").id

            result = promote_capture(cap_id, decided_by="curator")

            entry = db.session.get(MemoryEntry, result.memory_entry_id)
            self.assertEqual(entry.tags, "capture-tag")

    def test_promote_capture_falls_back_to_null_tags(self):
        with self.app.app_context():
            cap_id = _make_capture(status="pending", tags=None).id

            result = promote_capture(cap_id, decided_by="curator")

            entry = db.session.get(MemoryEntry, result.memory_entry_id)
            self.assertIsNone(entry.tags)

    def test_promote_capture_allows_empty_body_text(self):
        # B1 permits captures with empty body_text; B2 adds no stricter rule.
        with self.app.app_context():
            cap_id = _make_capture(status="pending", body_text="").id

            result = promote_capture(cap_id, decided_by="curator")

            entry = db.session.get(MemoryEntry, result.memory_entry_id)
            self.assertEqual(entry.content, "")

    def test_promote_capture_raises_on_terminal_source(self):
        with self.app.app_context():
            cap_id = _make_capture(status="rejected").id

            with self.assertRaises(InvalidTransitionError):
                promote_capture(cap_id, decided_by="curator")

    def test_promote_capture_raises_on_missing_id(self):
        with self.app.app_context():
            with self.assertRaises(CaptureNotFoundError):
                promote_capture(999999, decided_by="curator")

    def test_promote_capture_requires_decided_by_keyword(self):
        # decided_by is keyword-only: a positional second argument is rejected.
        with self.app.app_context():
            cap_id = _make_capture(status="pending").id

            with self.assertRaises(TypeError):
                promote_capture(cap_id, "curator")

    def test_promote_capture_concurrent_safe(self):
        # A competing reject commits between the pre-flight read and the
        # compare-and-swap; the promote loser rolls back, leaves no orphan
        # MemoryEntry, and raises.
        with self.app.app_context():
            cap_id = _make_capture(status="pending").id

            def racing_transition(*args):
                db.session.execute(
                    db.update(Capture)
                    .where(Capture.id == cap_id)
                    .values(
                        status="rejected",
                        decided_at_unix=111.0,
                        decided_by="race-winner",
                        reject_reason="winner reason",
                    )
                )
                db.session.commit()

            with patch("src.capture.service.transition", racing_transition):
                with self.assertRaises(InvalidTransitionError):
                    promote_capture(cap_id, decided_by="loser")

            row = db.session.get(Capture, cap_id)
            self.assertEqual(row.status, "rejected")
            self.assertEqual(db.session.query(MemoryEntry).count(), 0)

    def test_promote_capture_does_not_call_fts_index(self):
        # B2 does not index promoted memories; B3 wires FTS at the route.
        with self.app.app_context():
            cap_id = _make_capture(status="pending").id

            with patch("src.retrieval.fts.index_new_note") as mock_index:
                promote_capture(cap_id, decided_by="curator")

            mock_index.assert_not_called()


if __name__ == "__main__":
    unittest.main()
