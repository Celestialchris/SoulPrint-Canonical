"""Lightweight migration runner for SoulPrint.

Every migration script in this directory exposes:

    def apply(conn: sqlite3.Connection) -> None: ...

Scripts are named ``NNN_*.py`` where ``NNN`` is a three-digit zero-padded
number. The runner discovers them via glob, applies them in sorted order, and
records each applied id in the ``schema_migrations`` table.

Idempotence: each script must be a no-op on re-application (use
``CREATE TABLE IF NOT EXISTS`` / ``CREATE INDEX IF NOT EXISTS``). The runner
itself skips any migration id already recorded in ``schema_migrations``.

Loading: scripts are loaded via ``importlib.util.spec_from_file_location``
because their filenames begin with a digit and cannot be imported by module
name.

Wiring status: this runner ships tested in Campaign 03 B1 but is not yet
wired into application startup. The live app creates the ``capture`` table via
``db.create_all()`` from the registered model; migration ``001`` expresses the
same schema and is exercised only by ``tests/test_capture_migration.py``. A
future branch gives the runner startup ownership.
"""

from __future__ import annotations

import importlib.util
import sqlite3
import time
from pathlib import Path

MIGRATIONS_DIR = Path(__file__).parent


def run_migrations(db_path: str | Path) -> list[str]:
    """Apply any pending migrations to the SQLite database at ``db_path``.

    Returns the list of migration ids applied during this call. Migrations
    already recorded in ``schema_migrations`` are skipped, so repeated calls
    are safe and return ``[]`` once everything is current.
    """

    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS schema_migrations ("
            "id TEXT PRIMARY KEY, applied_at_unix REAL NOT NULL)"
        )
        conn.commit()

        applied = {
            row[0]
            for row in conn.execute("SELECT id FROM schema_migrations").fetchall()
        }

        newly_applied: list[str] = []
        for script in sorted(MIGRATIONS_DIR.glob("[0-9][0-9][0-9]_*.py")):
            migration_id = script.stem
            if migration_id in applied:
                continue

            spec = importlib.util.spec_from_file_location(
                f"src.migrations.{migration_id}", script
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            module.apply(conn)

            conn.execute(
                "INSERT INTO schema_migrations (id, applied_at_unix) VALUES (?, ?)",
                (migration_id, time.time()),
            )
            conn.commit()
            newly_applied.append(migration_id)

        return newly_applied
    finally:
        conn.close()
