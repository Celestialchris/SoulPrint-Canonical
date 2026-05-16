"""Tests for the record_capture persistence service."""

from __future__ import annotations

import sqlite3
import unittest
from unittest.mock import patch

from flask import Flask

from src.app.models import Capture
from src.app.models.db import db
from src.capture.content_hash import (
    CONTENT_HASH_RECIPE_VERSION,
    canonical_json,
    content_hash,
    sha256_hex,
)
from src.capture.paths import new_dir, tmp_dir
from src.capture.registry import CaptureContractError, validate_envelope
from src.capture.service import CaptureEnvelope, CaptureResult, record_capture
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
        envelope = _make_envelope()
        expected_hash = content_hash(
            envelope.adapter_id,
            envelope.payload_kind,
            envelope.body_text,
            envelope.source_url,
            envelope.captured_at_unix,
        )

        def racing_validate(env):
            # Runs in the window between the dedup pre-check and the insert:
            # commit a row with the same content_hash, exactly as a concurrent
            # capture would, so record_capture's own insert loses the race.
            validate_envelope(env)
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

        with self.app.app_context():
            with patch("src.capture.service.validate_envelope", racing_validate):
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


if __name__ == "__main__":
    unittest.main()
