"""Tests for the migration runner and migration 001 (capture table)."""

from __future__ import annotations

import sqlite3
import time
import unittest

from src.migrations.runner import run_migrations
from tests.temp_helpers import make_test_temp_dir


_MIGRATION_ID = "001_create_capture_table"

# Expected capture columns per the B1 frozen schema (VF2).
# name -> (declared sql type, notnull flag from PRAGMA table_info).
_EXPECTED_COLUMNS: dict[str, tuple[str, int]] = {
    "id": ("INTEGER", 0),
    "adapter_id": ("TEXT", 1),
    "adapter_version": ("TEXT", 1),
    "payload_kind": ("TEXT", 1),
    "body_text": ("TEXT", 1),
    "body_html": ("TEXT", 0),
    "source_url": ("TEXT", 0),
    "source_title": ("TEXT", 0),
    "metadata_json": ("TEXT", 0),
    "hints_json": ("TEXT", 0),
    "content_hash": ("TEXT", 1),
    "content_hash_recipe_version": ("INTEGER", 1),
    "raw_payload_hash": ("TEXT", 1),
    "captured_at_unix": ("REAL", 1),
    "received_at_unix": ("REAL", 1),
    "status": ("TEXT", 1),
    "triaged_at_unix": ("REAL", 0),
    "decided_at_unix": ("REAL", 0),
    "decided_by": ("TEXT", 0),
    "reject_reason": ("TEXT", 0),
    "quarantine_reason": ("TEXT", 0),
    "promoted_to_kind": ("TEXT", 0),
    "promoted_to_id": ("INTEGER", 0),
    "tags": ("TEXT", 0),
    "filesystem_path": ("TEXT", 0),
}

_EXPECTED_INDEXES = {
    "idx_capture_status",
    "idx_capture_content_hash",
    "idx_capture_received_at",
    "idx_capture_adapter",
}


def _insert_capture(conn: sqlite3.Connection, status: str) -> None:
    """Insert a minimal capture row with the given status (parameterized)."""

    conn.execute(
        "INSERT INTO capture "
        "(adapter_id, adapter_version, payload_kind, body_text, content_hash, "
        "content_hash_recipe_version, raw_payload_hash, captured_at_unix, "
        "received_at_unix, status) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("soulprint-cli", "1", "paste", "hello", "h", 1, "r", 1.0, 2.0, status),
    )


class CaptureMigrationTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = make_test_temp_dir(self, "capture-migration")
        self.db_path = str(self.tmpdir / "migration-test.db")

    def _connect(self) -> sqlite3.Connection:
        """Open a fresh connection and register its close before tempdir cleanup."""

        conn = sqlite3.connect(self.db_path)
        self.addCleanup(conn.close)
        return conn

    def test_runner_creates_schema_migrations_table(self):
        run_migrations(self.db_path)

        conn = self._connect()
        rows = conn.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name='schema_migrations'"
        ).fetchall()

        self.assertEqual(len(rows), 1)

    def test_runner_applies_001(self):
        run_migrations(self.db_path)

        conn = self._connect()
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='capture'"
        ).fetchall()

        self.assertEqual(len(rows), 1)

    def test_runner_is_idempotent(self):
        first = run_migrations(self.db_path)
        second = run_migrations(self.db_path)

        self.assertIn(_MIGRATION_ID, first)
        self.assertEqual(second, [])

        conn = self._connect()
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='capture'"
        ).fetchall()
        self.assertEqual(len(tables), 1)

    def test_runner_records_applied_timestamp(self):
        before = time.time()
        run_migrations(self.db_path)
        after = time.time()

        conn = self._connect()
        row = conn.execute(
            "SELECT applied_at_unix FROM schema_migrations WHERE id=?",
            (_MIGRATION_ID,),
        ).fetchone()

        self.assertIsNotNone(row)
        self.assertGreaterEqual(row[0], before)
        self.assertLessEqual(row[0], after)

    def test_runner_returns_applied_ids(self):
        applied = run_migrations(self.db_path)

        self.assertEqual(applied, [_MIGRATION_ID])

    def test_001_creates_vc2_columns(self):
        run_migrations(self.db_path)

        conn = self._connect()
        info = conn.execute("PRAGMA table_info(capture)").fetchall()
        # PRAGMA table_info row layout: cid, name, type, notnull, dflt_value, pk.
        actual = {row[1]: (row[2], row[3]) for row in info}

        self.assertEqual(set(actual), set(_EXPECTED_COLUMNS))
        for name, (sql_type, notnull) in _EXPECTED_COLUMNS.items():
            self.assertEqual(actual[name][0], sql_type, f"type mismatch for {name}")
            self.assertEqual(actual[name][1], notnull, f"notnull mismatch for {name}")

    def test_001_enforces_status_check_constraint(self):
        run_migrations(self.db_path)
        conn = self._connect()

        # A status outside the allowed set violates capture_status_chk.
        with self.assertRaises(sqlite3.IntegrityError):
            _insert_capture(conn, "bogus")
        conn.rollback()

        # Each of the five valid statuses inserts cleanly.
        for status in ("pending", "triaged", "promoted", "rejected", "quarantined"):
            _insert_capture(conn, status)
        conn.commit()

        count = conn.execute("SELECT COUNT(*) FROM capture").fetchone()[0]
        self.assertEqual(count, 5)

    def test_001_creates_all_four_indexes(self):
        run_migrations(self.db_path)

        conn = self._connect()
        index_list = conn.execute("PRAGMA index_list(capture)").fetchall()
        # PRAGMA index_list row layout: seq, name, unique, origin, partial.
        names = {row[1] for row in index_list}

        self.assertTrue(_EXPECTED_INDEXES.issubset(names))


if __name__ == "__main__":
    unittest.main()
