from __future__ import annotations

import sqlite3
from pathlib import Path

CORE_TABLES = ["imported_conversation", "imported_message", "memory_entry"]
FTS_TABLES = ["fts_messages", "fts_notes"]

_SKIP_DETAIL = "skipped: database missing"


def verify_archive(db_path: Path) -> dict:
    """Run deterministic health checks against a SoulPrint SQLite ledger.

    Returns a dict with this exact shape:

    {
        "ok": bool,
        "db_path": str,
        "checks": {
            "db_exists":   {"ok": bool, "detail": str | None},
            "integrity":   {"ok": bool, "detail": str | None},
            "core_tables": {"ok": bool, "detail": str | None, "missing": list[str]},
            "fts_tables":  {"ok": bool, "detail": str | None, "missing": list[str]},
            "orphans":     {"ok": bool, "detail": str | None, "count": int},
        },
        "counts": {
            "conversations": int,
            "messages": int,
            "notes": int,
            "providers": dict[str, int],
        },
    }

    Never raises for expected failure modes. Unexpected exceptions propagate.
    """
    db_path = Path(db_path)
    result: dict = {
        "ok": False,
        "db_path": str(db_path.resolve()),
        "checks": {
            "db_exists":   {"ok": False, "detail": None},
            "integrity":   {"ok": False, "detail": None},
            "core_tables": {"ok": False, "detail": None, "missing": []},
            "fts_tables":  {"ok": False, "detail": None, "missing": []},
            "orphans":     {"ok": False, "detail": None, "count": 0},
        },
        "counts": {
            "conversations": 0,
            "messages": 0,
            "notes": 0,
            "providers": {},
        },
    }

    if not db_path.is_file():
        result["checks"]["db_exists"] = {"ok": False, "detail": None}
        result["checks"]["integrity"] = {"ok": False, "detail": _SKIP_DETAIL}
        result["checks"]["core_tables"] = {"ok": False, "detail": _SKIP_DETAIL, "missing": []}
        result["checks"]["fts_tables"] = {"ok": False, "detail": _SKIP_DETAIL, "missing": []}
        result["checks"]["orphans"] = {"ok": False, "detail": _SKIP_DETAIL, "count": 0}
        return result

    result["checks"]["db_exists"] = {"ok": True, "detail": None}

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    # Initialised here so orphan/counts guards can reference it even if the
    # core-tables query fails partway through.
    found_core: set[str] = set()
    try:
        # integrity check
        try:
            rows = conn.execute("PRAGMA integrity_check").fetchall()
            if len(rows) == 1 and rows[0][0] == "ok":
                result["checks"]["integrity"] = {"ok": True, "detail": None}
            else:
                detail = "; ".join(r[0] for r in rows)
                result["checks"]["integrity"] = {"ok": False, "detail": detail}
        except sqlite3.DatabaseError as exc:
            result["checks"]["integrity"] = {"ok": False, "detail": str(exc)}

        # core tables — guarded: a non-SQLite file raises DatabaseError here too
        try:
            rows = conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' AND name IN (?, ?, ?)",
                tuple(CORE_TABLES),
            ).fetchall()
            found_core = {r[0] for r in rows}
            missing_core = [t for t in CORE_TABLES if t not in found_core]
            if missing_core:
                result["checks"]["core_tables"] = {
                    "ok": False,
                    "detail": f"missing: {', '.join(missing_core)}",
                    "missing": missing_core,
                }
            else:
                result["checks"]["core_tables"] = {"ok": True, "detail": None, "missing": []}
        except sqlite3.DatabaseError as exc:
            result["checks"]["core_tables"] = {
                "ok": False,
                "detail": str(exc),
                "missing": list(CORE_TABLES),
            }

        # FTS tables — guarded for the same reason
        try:
            rows = conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' AND name IN (?, ?)",
                tuple(FTS_TABLES),
            ).fetchall()
            found_fts = {r[0] for r in rows}
            missing_fts = [t for t in FTS_TABLES if t not in found_fts]
            if missing_fts:
                result["checks"]["fts_tables"] = {
                    "ok": False,
                    "detail": f"missing: {', '.join(missing_fts)}",
                    "missing": missing_fts,
                }
            else:
                result["checks"]["fts_tables"] = {"ok": True, "detail": None, "missing": []}
        except sqlite3.DatabaseError as exc:
            result["checks"]["fts_tables"] = {
                "ok": False,
                "detail": str(exc),
                "missing": list(FTS_TABLES),
            }

        # orphans — skip if either referenced table is absent; the subquery
        # references imported_conversation, so both tables must exist
        if "imported_message" not in found_core or "imported_conversation" not in found_core:
            result["checks"]["orphans"] = {"ok": True, "detail": None, "count": 0}
        else:
            try:
                count = conn.execute(
                    "SELECT COUNT(*) FROM imported_message"
                    " WHERE conversation_id NOT IN (SELECT id FROM imported_conversation)"
                ).fetchone()[0]
                if count > 0:
                    result["checks"]["orphans"] = {
                        "ok": False,
                        "detail": f"{count} rows point to missing conversations",
                        "count": count,
                    }
                else:
                    result["checks"]["orphans"] = {"ok": True, "detail": None, "count": 0}
            except sqlite3.DatabaseError as exc:
                result["checks"]["orphans"] = {"ok": False, "detail": str(exc), "count": 0}

        # counts — only query tables that exist
        if "imported_conversation" in found_core:
            result["counts"]["conversations"] = conn.execute(
                "SELECT COUNT(*) FROM imported_conversation"
            ).fetchone()[0]
            provider_rows = conn.execute(
                "SELECT source, COUNT(*) AS cnt FROM imported_conversation GROUP BY source"
            ).fetchall()
            result["counts"]["providers"] = {
                r["source"]: r["cnt"] for r in provider_rows if r["cnt"] > 0
            }
        if "imported_message" in found_core:
            result["counts"]["messages"] = conn.execute(
                "SELECT COUNT(*) FROM imported_message"
            ).fetchone()[0]
        if "memory_entry" in found_core:
            result["counts"]["notes"] = conn.execute(
                "SELECT COUNT(*) FROM memory_entry"
            ).fetchone()[0]
    finally:
        conn.close()

    result["ok"] = all(c["ok"] for c in result["checks"].values())
    return result
