"""Migration 001: create the ``capture`` ledger table.

Creates the frozen Campaign 03 capture table plus its four indexes. The DDL
reproduces the B1 schema verbatim, including the named CHECK constraint
``capture_status_chk`` and the ``DESC`` index orderings, so it converges
idempotently with the SQLAlchemy ``Capture`` model's ``db.create_all()`` path.

Idempotent: re-application is a no-op via ``IF NOT EXISTS``.
"""

from __future__ import annotations

import sqlite3

_DDL = """
CREATE TABLE IF NOT EXISTS capture (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  adapter_id TEXT NOT NULL,
  adapter_version TEXT NOT NULL,
  payload_kind TEXT NOT NULL,
  body_text TEXT NOT NULL,
  body_html TEXT,
  source_url TEXT,
  source_title TEXT,
  metadata_json TEXT,
  hints_json TEXT,
  content_hash TEXT NOT NULL,
  content_hash_recipe_version INTEGER NOT NULL,
  raw_payload_hash TEXT NOT NULL,
  captured_at_unix REAL NOT NULL,
  received_at_unix REAL NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending',
  triaged_at_unix REAL,
  decided_at_unix REAL,
  decided_by TEXT,
  reject_reason TEXT,
  quarantine_reason TEXT,
  promoted_to_kind TEXT,
  promoted_to_id INTEGER,
  tags TEXT,
  filesystem_path TEXT,
  CONSTRAINT capture_status_chk CHECK (status IN ('pending','triaged','promoted','rejected','quarantined'))
);

CREATE INDEX IF NOT EXISTS idx_capture_status ON capture(status);
CREATE INDEX IF NOT EXISTS idx_capture_content_hash ON capture(content_hash);
CREATE INDEX IF NOT EXISTS idx_capture_received_at ON capture(received_at_unix DESC);
CREATE INDEX IF NOT EXISTS idx_capture_adapter ON capture(adapter_id, captured_at_unix DESC);
"""


def apply(conn: sqlite3.Connection) -> None:
    """Create the ``capture`` table and its four indexes."""

    conn.executescript(_DDL)
