from __future__ import annotations

import sqlite3
import unittest
from pathlib import Path

from tests.temp_helpers import make_test_temp_dir

_CORE_DDL = """
CREATE TABLE imported_conversation (
    id INTEGER PRIMARY KEY,
    source TEXT,
    created_at_unix REAL
);
CREATE TABLE imported_message (
    id INTEGER PRIMARY KEY,
    conversation_id INTEGER
);
CREATE TABLE memory_entry (
    id INTEGER PRIMARY KEY
);
"""

_FULL_DDL = _CORE_DDL + """
CREATE VIRTUAL TABLE fts_messages USING fts5(content);
CREATE VIRTUAL TABLE fts_notes USING fts5(content);
"""


def _make_db(path: Path, ddl: str) -> None:
    conn = sqlite3.connect(str(path))
    try:
        conn.executescript(ddl)
        conn.commit()
    finally:
        conn.close()


class VerifyArchiveTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = make_test_temp_dir(self, "verify-archive")

    def _db(self, name: str = "test.db") -> Path:
        return self.tmpdir / name

    # ------------------------------------------------------------------

    def test_verify_missing_db_reports_db_exists_false(self) -> None:
        from src.verify import verify_archive

        path = self._db("nonexistent.db")
        result = verify_archive(path)

        self.assertFalse(result["ok"])
        self.assertFalse(result["checks"]["db_exists"]["ok"])
        # all other checks skipped
        for key in ("integrity", "core_tables", "fts_tables", "orphans"):
            self.assertFalse(result["checks"][key]["ok"])
            self.assertIn("skipped", result["checks"][key]["detail"])
        # counts are all zero / empty
        self.assertEqual(result["counts"]["conversations"], 0)
        self.assertEqual(result["counts"]["messages"], 0)
        self.assertEqual(result["counts"]["notes"], 0)
        self.assertEqual(result["counts"]["providers"], {})

    def test_verify_healthy_archive_returns_ok_true(self) -> None:
        from src.verify import verify_archive

        path = self._db()
        _make_db(path, _FULL_DDL)
        conn = sqlite3.connect(str(path))
        try:
            conn.execute(
                "INSERT INTO imported_conversation (source, created_at_unix) VALUES (?, ?)",
                ("chatgpt", 1_700_000_000.0),
            )
            conn.execute("INSERT INTO imported_message (conversation_id) VALUES (?)", (1,))
            conn.execute("INSERT INTO memory_entry DEFAULT VALUES")
            conn.commit()
        finally:
            conn.close()

        result = verify_archive(path)

        self.assertTrue(result["ok"])
        for key in result["checks"]:
            self.assertTrue(result["checks"][key]["ok"], f"check {key!r} should be ok")

    def test_verify_missing_core_tables(self) -> None:
        from src.verify import verify_archive

        path = self._db()
        # only memory_entry
        conn = sqlite3.connect(str(path))
        try:
            conn.execute("CREATE TABLE memory_entry (id INTEGER PRIMARY KEY)")
            conn.commit()
        finally:
            conn.close()

        result = verify_archive(path)

        self.assertFalse(result["checks"]["core_tables"]["ok"])
        self.assertEqual(
            set(result["checks"]["core_tables"]["missing"]),
            {"imported_conversation", "imported_message"},
        )
        self.assertFalse(result["ok"])

    def test_verify_missing_fts_tables(self) -> None:
        from src.verify import verify_archive

        path = self._db()
        _make_db(path, _CORE_DDL)

        result = verify_archive(path)

        self.assertFalse(result["checks"]["fts_tables"]["ok"])
        self.assertEqual(
            set(result["checks"]["fts_tables"]["missing"]),
            {"fts_messages", "fts_notes"},
        )

    def test_verify_detects_orphan_messages(self) -> None:
        from src.verify import verify_archive

        path = self._db()
        _make_db(path, _CORE_DDL)
        conn = sqlite3.connect(str(path))
        try:
            conn.execute("INSERT INTO imported_message (conversation_id) VALUES (?)", (999,))
            conn.commit()
        finally:
            conn.close()

        result = verify_archive(path)

        self.assertEqual(result["checks"]["orphans"]["count"], 1)
        self.assertFalse(result["checks"]["orphans"]["ok"])

    def test_verify_counts_only_nonzero_providers(self) -> None:
        from src.verify import verify_archive

        path = self._db()
        _make_db(path, _CORE_DDL)
        conn = sqlite3.connect(str(path))
        try:
            conn.execute(
                "INSERT INTO imported_conversation (source, created_at_unix) VALUES (?, ?)",
                ("chatgpt", 1_700_000_000.0),
            )
            conn.execute(
                "INSERT INTO imported_conversation (source, created_at_unix) VALUES (?, ?)",
                ("chatgpt", 1_701_000_000.0),
            )
            conn.commit()
        finally:
            conn.close()

        result = verify_archive(path)

        self.assertEqual(result["counts"]["providers"], {"chatgpt": 2})
        self.assertNotIn("claude", result["counts"]["providers"])
        self.assertNotIn("gemini", result["counts"]["providers"])

    def test_verify_integrity_check_passes_on_fresh_db(self) -> None:
        from src.verify import verify_archive

        path = self._db()
        _make_db(path, _CORE_DDL)

        result = verify_archive(path)

        self.assertTrue(result["checks"]["integrity"]["ok"])
        self.assertIsNone(result["checks"]["integrity"]["detail"])

    def test_verify_non_sqlite_file_does_not_crash(self) -> None:
        from src.verify import verify_archive

        path = self._db("not_sqlite.db")
        path.write_text("this is not a sqlite database\n")

        result = verify_archive(path)

        self.assertTrue(result["checks"]["db_exists"]["ok"])
        self.assertFalse(result["checks"]["integrity"]["ok"])
        self.assertFalse(result["ok"])

    def test_verify_orphan_skips_when_conversation_table_missing(self) -> None:
        from src.verify import verify_archive

        path = self._db()
        conn = sqlite3.connect(str(path))
        try:
            conn.execute(
                "CREATE TABLE imported_message (id INTEGER PRIMARY KEY, conversation_id INTEGER)"
            )
            conn.execute("CREATE TABLE memory_entry (id INTEGER PRIMARY KEY)")
            conn.execute("INSERT INTO imported_message (conversation_id) VALUES (?)", (999,))
            conn.commit()
        finally:
            conn.close()

        result = verify_archive(path)

        self.assertTrue(result["checks"]["orphans"]["ok"])
        self.assertFalse(result["checks"]["core_tables"]["ok"])
        self.assertIn("imported_conversation", result["checks"]["core_tables"]["missing"])

    # ------------------------------------------------------------------
    # quick_health_summary tests
    # ------------------------------------------------------------------

    def test_quick_health_summary_missing_db_returns_unknown(self) -> None:
        from src.verify import quick_health_summary

        path = self._db("qs_nonexistent.db")
        result = quick_health_summary(path)

        self.assertEqual(result["state"], "unknown")
        self.assertIsInstance(result["db_path"], str)

    def test_quick_health_summary_healthy_archive_returns_healthy(self) -> None:
        from src.verify import quick_health_summary

        path = self._db("qs_healthy.db")
        _make_db(path, _FULL_DDL)
        result = quick_health_summary(path)

        self.assertEqual(result["state"], "healthy")
        self.assertIsNone(result["detail"])

    def test_quick_health_summary_missing_core_table_returns_needs_attention(self) -> None:
        from src.verify import quick_health_summary

        path = self._db("qs_missing_core.db")
        # Build DB with all tables except memory_entry
        conn = sqlite3.connect(str(path))
        try:
            conn.executescript("""
                CREATE TABLE imported_conversation (
                    id INTEGER PRIMARY KEY, source TEXT, created_at_unix REAL
                );
                CREATE TABLE imported_message (
                    id INTEGER PRIMARY KEY, conversation_id INTEGER
                );
                CREATE VIRTUAL TABLE fts_messages USING fts5(content);
                CREATE VIRTUAL TABLE fts_notes USING fts5(content);
            """)
            conn.commit()
        finally:
            conn.close()

        result = quick_health_summary(path)

        self.assertEqual(result["state"], "needs_attention")
        self.assertIn("memory_entry", result["detail"])

    def test_quick_health_summary_corrupt_db_returns_needs_attention(self) -> None:
        from src.verify import quick_health_summary

        path = self._db("qs_corrupt.db")
        path.write_text("this is not a sqlite database\n")
        result = quick_health_summary(path)

        self.assertEqual(result["state"], "needs_attention")
        self.assertIsInstance(result["detail"], str)
        self.assertTrue(len(result["detail"]) > 0)

    def test_quick_health_summary_skips_full_verify_checks(self) -> None:
        """Orphan row does not flip state to needs_attention.

        Proves quick_health_summary skips the orphan detection that
        verify_archive runs. All tables present + an orphan row =
        state "healthy" from the quick function.
        """
        from src.verify import quick_health_summary

        path = self._db("qs_orphan.db")
        _make_db(path, _FULL_DDL)
        # Insert an orphaned message (conversation_id 999 has no parent row)
        conn = sqlite3.connect(str(path))
        try:
            conn.execute(
                "INSERT INTO imported_message (conversation_id) VALUES (?)", (999,)
            )
            conn.commit()
        finally:
            conn.close()

        result = quick_health_summary(path)

        self.assertEqual(result["state"], "healthy")
