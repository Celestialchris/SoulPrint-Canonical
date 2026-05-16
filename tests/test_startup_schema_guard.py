"""Tests for the create_app startup column guard backfilling captured_via_id.

B2 added ``MemoryEntry.captured_via_id`` to the ORM model. Databases created
before B2 have a ``memory_entry`` table without that column, and
``db.create_all()`` never ALTERs an existing table, so the ad-hoc startup
guard in ``create_app`` must backfill the column and its index before the ORM
selects ``MemoryEntry``.
"""

from __future__ import annotations

import sqlite3
import unittest

from src.app import create_app
from src.app.models import MemoryEntry
from src.config import Config
from tests.temp_helpers import make_test_temp_dir, release_app_db_handles


class CapturedViaIdStartupGuardTest(unittest.TestCase):
    def setUp(self):
        self.workdir = make_test_temp_dir(self, "startup-schema-guard")
        self.db_path = str(self.workdir / "legacy.db")
        self._build_legacy_database()
        self._old_uri = Config.SQLALCHEMY_DATABASE_URI
        Config.SQLALCHEMY_DATABASE_URI = f"sqlite:///{self.db_path}"
        self.addCleanup(self._restore_sqlite_uri)

    def _restore_sqlite_uri(self):
        Config.SQLALCHEMY_DATABASE_URI = self._old_uri

    def _build_legacy_database(self):
        """Create a pre-B2 memory_entry table: no captured_via_id column."""

        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                "CREATE TABLE memory_entry ("
                "id INTEGER PRIMARY KEY, "
                "timestamp DATETIME NOT NULL, "
                "role VARCHAR(32) NOT NULL, "
                "content TEXT NOT NULL, "
                "tags TEXT, "
                "is_starred BOOLEAN NOT NULL DEFAULT 0)"
            )
            conn.execute(
                "INSERT INTO memory_entry (id, timestamp, role, content) "
                "VALUES (1, '2026-05-16 12:00:00.000000', 'user', 'legacy note')"
            )
            conn.commit()
        finally:
            conn.close()

    def _memory_entry_columns(self) -> set[str]:
        conn = sqlite3.connect(self.db_path)
        try:
            return {
                row[1] for row in conn.execute("PRAGMA table_info(memory_entry)")
            }
        finally:
            conn.close()

    def _memory_entry_indexes(self) -> set[str]:
        conn = sqlite3.connect(self.db_path)
        try:
            return {
                row[0]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='index' "
                    "AND tbl_name='memory_entry'"
                )
            }
        finally:
            conn.close()

    def test_memory_entry_query_works_after_startup_guard(self):
        # Pre-condition: the legacy database genuinely lacks the column.
        self.assertNotIn("captured_via_id", self._memory_entry_columns())

        app = create_app()
        self.addCleanup(release_app_db_handles, app, drop_all=True)

        # Without the guard this raises sqlite3.OperationalError: no such column.
        with app.app_context():
            rows = MemoryEntry.query.all()
        self.assertEqual(len(rows), 1)
        self.assertIsNone(rows[0].captured_via_id)

    def test_guard_adds_captured_via_id_column(self):
        app = create_app()
        self.addCleanup(release_app_db_handles, app, drop_all=True)

        self.assertIn("captured_via_id", self._memory_entry_columns())

    def test_guard_creates_captured_via_id_index(self):
        app = create_app()
        self.addCleanup(release_app_db_handles, app, drop_all=True)

        self.assertIn(
            "idx_memory_entry_captured_via_id", self._memory_entry_indexes()
        )

    def test_guard_is_idempotent_on_repeated_startup(self):
        first = create_app()
        release_app_db_handles(first, drop_all=False)

        # A second startup over the now-upgraded database is a clean no-op:
        # the column and index are already present, so neither is re-created.
        second = create_app()
        self.addCleanup(release_app_db_handles, second, drop_all=True)

        self.assertIn("captured_via_id", self._memory_entry_columns())
        self.assertIn(
            "idx_memory_entry_captured_via_id", self._memory_entry_indexes()
        )
        with second.app_context():
            rows = MemoryEntry.query.all()
        self.assertEqual(len(rows), 1)


if __name__ == "__main__":
    unittest.main()
