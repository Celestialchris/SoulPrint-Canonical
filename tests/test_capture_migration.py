"""Tests for the migration runner and migration 001 (capture table)."""

from __future__ import annotations

import sqlite3
import time
import unittest

from flask import Flask

from src.app.models.db import db
from src.migrations.runner import run_migrations
from tests.temp_helpers import make_test_temp_dir, release_app_db_handles


_MIGRATION_ID = "001_create_capture_table"
_MIGRATION_ID_002 = "002_add_captured_via_id_to_memory_entry"

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


def _insert_capture(
    conn: sqlite3.Connection, status: str, content_hash: str = "h"
) -> None:
    """Insert a minimal capture row with the given status (parameterized).

    ``content_hash`` is a parameter because idx_capture_content_hash is a
    unique index: callers inserting more than one row must vary it.
    """

    conn.execute(
        "INSERT INTO capture "
        "(adapter_id, adapter_version, payload_kind, body_text, content_hash, "
        "content_hash_recipe_version, raw_payload_hash, captured_at_unix, "
        "received_at_unix, status) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("soulprint-cli", "1", "paste", "hello", content_hash, 1, "r", 1.0, 2.0, status),
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

        self.assertEqual(applied, [_MIGRATION_ID, _MIGRATION_ID_002])

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

        # Each of the five valid statuses inserts cleanly. content_hash varies
        # per row because idx_capture_content_hash is a unique index.
        for status in ("pending", "triaged", "promoted", "rejected", "quarantined"):
            _insert_capture(conn, status, content_hash=f"hash-{status}")
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

    def test_001_content_hash_index_is_unique(self):
        run_migrations(self.db_path)
        conn = self._connect()

        # PRAGMA index_list row layout: seq, name, unique, origin, partial.
        index_list = conn.execute("PRAGMA index_list(capture)").fetchall()
        unique_flag = {row[1]: row[2] for row in index_list}
        self.assertEqual(unique_flag["idx_capture_content_hash"], 1)

        # The unique index is enforced: a duplicate content_hash is rejected
        # at INSERT time, which is what makes record_capture's dedup atomic.
        _insert_capture(conn, "pending", content_hash="dup")
        with self.assertRaises(sqlite3.IntegrityError):
            _insert_capture(conn, "pending", content_hash="dup")
        conn.rollback()


class Migration002Test(unittest.TestCase):
    """Tests for migration 002 (captured_via_id provenance on memory_entry)."""

    def setUp(self):
        self.tmpdir = make_test_temp_dir(self, "migration-002")
        self.db_path = str(self.tmpdir / "migration-002.db")

    def _connect(self) -> sqlite3.Connection:
        """Open a fresh connection and register its close before tempdir cleanup."""

        conn = sqlite3.connect(self.db_path)
        self.addCleanup(conn.close)
        return conn

    def _create_stub_memory_entry(
        self, *, with_column: bool = False, with_index: bool = False
    ) -> None:
        """Create a minimal memory_entry table standing in for a deployed install.

        Migration 002 only touches ``captured_via_id``, so the stub carries
        just enough columns to be a valid table. ``with_column`` and
        ``with_index`` pre-create the migration's own additions so the
        idempotence and partial-apply guards can be exercised.
        """

        conn = sqlite3.connect(self.db_path)
        try:
            columns = "id INTEGER PRIMARY KEY, role TEXT"
            if with_column:
                columns += ", captured_via_id INTEGER"
            conn.execute(f"CREATE TABLE memory_entry ({columns})")
            if with_index:
                conn.execute(
                    "CREATE INDEX idx_memory_entry_captured_via_id "
                    "ON memory_entry(captured_via_id)"
                )
            conn.commit()
        finally:
            conn.close()

    def test_002_is_noop_when_memory_entry_table_absent(self):
        # Guard 1: a pure-migration database has no memory_entry to alter.
        applied = run_migrations(self.db_path)

        self.assertIn(_MIGRATION_ID_002, applied)
        conn = self._connect()
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        self.assertIn("capture", tables)
        self.assertNotIn("memory_entry", tables)

    def test_002_adds_captured_via_id_column(self):
        self._create_stub_memory_entry()

        run_migrations(self.db_path)

        conn = self._connect()
        columns = {
            row[1]
            for row in conn.execute("PRAGMA table_info(memory_entry)").fetchall()
        }
        self.assertIn("captured_via_id", columns)

    def test_002_column_is_nullable_integer(self):
        self._create_stub_memory_entry()

        run_migrations(self.db_path)

        conn = self._connect()
        # PRAGMA table_info row layout: cid, name, type, notnull, dflt_value, pk.
        info = {
            row[1]: (row[2], row[3])
            for row in conn.execute("PRAGMA table_info(memory_entry)").fetchall()
        }
        sql_type, notnull = info["captured_via_id"]
        self.assertEqual(sql_type, "INTEGER")
        self.assertEqual(notnull, 0)

    def test_002_creates_named_index(self):
        self._create_stub_memory_entry()

        run_migrations(self.db_path)

        conn = self._connect()
        indexes = {
            row[1]
            for row in conn.execute("PRAGMA index_list(memory_entry)").fetchall()
        }
        self.assertIn("idx_memory_entry_captured_via_id", indexes)

    def test_002_is_idempotent_on_column_present(self):
        # Guard 2: the column already exists (a db.create_all() fresh install).
        self._create_stub_memory_entry(with_column=True, with_index=True)

        first = run_migrations(self.db_path)
        second = run_migrations(self.db_path)

        self.assertIn(_MIGRATION_ID_002, first)
        self.assertEqual(second, [])
        conn = self._connect()
        columns = [
            row[1]
            for row in conn.execute("PRAGMA table_info(memory_entry)").fetchall()
        ]
        self.assertEqual(columns.count("captured_via_id"), 1)

    def test_002_is_idempotent_on_index_present(self):
        # Guard 3: the index already exists; CREATE INDEX must be skipped.
        self._create_stub_memory_entry(with_column=True, with_index=True)

        run_migrations(self.db_path)  # must not raise

        conn = self._connect()
        indexes = [
            row[1]
            for row in conn.execute("PRAGMA index_list(memory_entry)").fetchall()
        ]
        self.assertEqual(indexes.count("idx_memory_entry_captured_via_id"), 1)

    def test_002_partial_apply_recovery(self):
        # Column present but index absent: Guard 3 still creates the index.
        self._create_stub_memory_entry(with_column=True, with_index=False)

        run_migrations(self.db_path)

        conn = self._connect()
        indexes = {
            row[1]
            for row in conn.execute("PRAGMA index_list(memory_entry)").fetchall()
        }
        self.assertIn("idx_memory_entry_captured_via_id", indexes)

    def test_runner_applies_both_in_order(self):
        run_migrations(self.db_path)

        conn = self._connect()
        recorded = [
            row[0]
            for row in conn.execute(
                "SELECT id FROM schema_migrations ORDER BY id"
            ).fetchall()
        ]
        self.assertEqual(recorded, [_MIGRATION_ID, _MIGRATION_ID_002])

    def test_002_column_type_matches_model(self):
        # Deepening section 3.6 parity: the migration-built captured_via_id
        # and its index must match what db.create_all() builds from the model.
        self._create_stub_memory_entry()
        run_migrations(self.db_path)
        migration_conn = self._connect()
        migration_info = {
            row[1]: (row[2], row[3])
            for row in migration_conn.execute(
                "PRAGMA table_info(memory_entry)"
            ).fetchall()
        }
        migration_indexes = {
            row[1]
            for row in migration_conn.execute(
                "PRAGMA index_list(memory_entry)"
            ).fetchall()
        }
        migration_fks = migration_conn.execute(
            "PRAGMA foreign_key_list(memory_entry)"
        ).fetchall()

        model_db_path = str(self.tmpdir / "model-path.db")
        app = Flask(__name__)
        app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{model_db_path}"
        app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        db.init_app(app)
        with app.app_context():
            db.create_all()
        self.addCleanup(release_app_db_handles, app, drop_all=True)
        model_conn = sqlite3.connect(model_db_path)
        self.addCleanup(model_conn.close)
        model_info = {
            row[1]: (row[2], row[3])
            for row in model_conn.execute(
                "PRAGMA table_info(memory_entry)"
            ).fetchall()
        }
        model_indexes = {
            row[1]
            for row in model_conn.execute(
                "PRAGMA index_list(memory_entry)"
            ).fetchall()
        }
        model_fks = model_conn.execute(
            "PRAGMA foreign_key_list(memory_entry)"
        ).fetchall()

        # Column name, declared type, and nullability converge.
        self.assertEqual(
            migration_info["captured_via_id"], model_info["captured_via_id"]
        )
        self.assertEqual(migration_info["captured_via_id"][0], "INTEGER")
        self.assertEqual(migration_info["captured_via_id"][1], 0)
        # The explicit index name converges on both creation paths.
        self.assertIn("idx_memory_entry_captured_via_id", migration_indexes)
        self.assertIn("idx_memory_entry_captured_via_id", model_indexes)
        # No FK is declared on either path (the adjudicated B2 choice).
        self.assertEqual(migration_fks, [])
        self.assertEqual(model_fks, [])


if __name__ == "__main__":
    unittest.main()
