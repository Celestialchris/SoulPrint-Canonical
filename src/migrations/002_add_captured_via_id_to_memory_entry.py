"""Migration 002: add captured_via_id provenance column to memory_entry.

Adds a nullable integer column ``captured_via_id`` to memory_entry, plus
an explicit named index ``idx_memory_entry_captured_via_id``.

Adjudicated B2 choice: NO FK constraint is added. SQLite ALTER TABLE
cannot add a FOREIGN KEY constraint to an existing table without a
full table rebuild, and B2 rejects that scope expansion. The provenance
link is enforced by service logic in promote_capture, not by DB-level
FK enforcement. The model-side declaration matches: nullable Integer
column with no db.ForeignKey, explicit named index via __table_args__.
This keeps model-created and migration-created schemas equivalent per
the v2-patched deepening section 3.6 schema parity rule.

This migration is triple-guarded for idempotence and tolerance of the
B1 duality (memory_entry may not exist in the migration chain at all,
since db.create_all() creates it from the model and the migration
runner is dormant):

  Guard 1: if memory_entry table does not exist, do nothing.
  Guard 2: if captured_via_id column already exists, do nothing.
  Guard 3: if idx_memory_entry_captured_via_id index already exists,
           skip the CREATE INDEX (covers partial-apply recovery).

The migration is a correct no-op in all three guard-positive cases.
"""

from __future__ import annotations

import sqlite3


def _table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
    ).fetchone()
    return row is not None


def _column_exists(
    conn: sqlite3.Connection, table_name: str, column_name: str
) -> bool:
    rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    return any(r[1] == column_name for r in rows)


def _index_exists(conn: sqlite3.Connection, index_name: str) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='index' AND name=?",
        (index_name,),
    ).fetchone()
    return row is not None


def apply(conn: sqlite3.Connection) -> None:
    # Guard 1: table absent -> migration is a correct no-op.
    if not _table_exists(conn, "memory_entry"):
        return

    # Guard 2: column already present -> migration is a correct no-op.
    if not _column_exists(conn, "memory_entry", "captured_via_id"):
        conn.execute(
            "ALTER TABLE memory_entry ADD COLUMN captured_via_id INTEGER"
        )

    # Guard 3: index already present -> skip the CREATE.
    if not _index_exists(conn, "idx_memory_entry_captured_via_id"):
        conn.execute(
            "CREATE INDEX idx_memory_entry_captured_via_id "
            "ON memory_entry(captured_via_id)"
        )

    conn.commit()
