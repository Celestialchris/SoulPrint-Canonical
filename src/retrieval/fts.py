"""Full-text search over imported messages and native notes using SQLite FTS5.

FTS5 virtual tables are Layer B (Legibility) — derived indexes over canonical
data, rebuildable at any time.  They never modify canonical tables.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone


def sanitize_fts_query(raw_query: str) -> str:
    """Make a raw user query safe for FTS5 MATCH.

    Wraps each term in double quotes to prevent FTS5 syntax errors
    from user input containing special characters like AND, OR, NOT, NEAR.
    """

    terms = raw_query.strip().split()
    if not terms:
        return ""
    return " ".join(f'"{term}"' for term in terms if term)


def ensure_fts_tables(db_path: str) -> None:
    """Create FTS5 virtual tables if they don't exist.

    Creates:
    - fts_messages: indexes imported message content
    - fts_notes: indexes native note content

    Call this on app startup or before first search.
    """

    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS fts_messages USING fts5(
                content,
                conversation_id UNINDEXED,
                conversation_title UNINDEXED,
                provider UNINDEXED,
                message_index UNINDEXED,
                message_role UNINDEXED,
                message_id UNINDEXED,
                timestamp UNINDEXED,
                tokenize='porter unicode61'
            )
            """
        )
        conn.execute(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS fts_notes USING fts5(
                content,
                note_id UNINDEXED,
                tags UNINDEXED,
                timestamp UNINDEXED,
                tokenize='porter unicode61'
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def populate_fts_messages(db_path: str) -> int:
    """Populate/rebuild fts_messages from imported message data.

    Reads all imported messages and inserts into the FTS5 table.
    Returns count of rows indexed.

    This is idempotent — clears and rebuilds the FTS table.
    """

    conn = sqlite3.connect(db_path)
    try:
        conn.execute("DELETE FROM fts_messages")

        rows = conn.execute(
            """
            SELECT
                m.content,
                m.conversation_id,
                c.title,
                c.source,
                m.sequence_index,
                m.role,
                m.id,
                m.created_at_unix
            FROM imported_message m
            JOIN imported_conversation c ON c.id = m.conversation_id
            """
        ).fetchall()

        for content, conv_id, title, source, seq_idx, role, msg_id, created_at in rows:
            conn.execute(
                "INSERT INTO fts_messages"
                "(content, conversation_id, conversation_title, provider,"
                " message_index, message_role, message_id, timestamp)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    content,
                    str(conv_id),
                    title,
                    source,
                    str(seq_idx),
                    role,
                    str(msg_id),
                    _format_unix_ts(created_at),
                ),
            )

        conn.commit()
        return len(rows)
    finally:
        conn.close()


def populate_fts_notes(db_path: str) -> int:
    """Populate/rebuild fts_notes from native MemoryEntry data.

    Returns count of rows indexed.
    Idempotent — clears and rebuilds.
    """

    conn = sqlite3.connect(db_path)
    try:
        conn.execute("DELETE FROM fts_notes")

        rows = conn.execute(
            "SELECT id, content, tags, timestamp FROM memory_entry"
        ).fetchall()

        for note_id, content, tags, timestamp in rows:
            conn.execute(
                "INSERT INTO fts_notes(content, note_id, tags, timestamp)"
                " VALUES (?, ?, ?, ?)",
                (content, str(note_id), tags or "", str(timestamp) if timestamp else ""),
            )

        conn.commit()
        return len(rows)
    finally:
        conn.close()


def rebuild_fts(db_path: str) -> dict:
    """Full rebuild of all FTS indexes. Returns counts."""

    ensure_fts_tables(db_path)
    messages = populate_fts_messages(db_path)
    notes = populate_fts_notes(db_path)
    return {"messages": messages, "notes": notes}


def index_new_messages(db_path: str, conversation_id: int | str) -> int:
    """Index messages from a single conversation (called after import).

    Only adds messages not already in the FTS table.
    Returns count of rows added.
    """

    ensure_fts_tables(db_path)
    conv_id = int(conversation_id)
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(
            """
            SELECT
                m.content,
                m.conversation_id,
                c.title,
                c.source,
                m.sequence_index,
                m.role,
                m.id,
                m.created_at_unix
            FROM imported_message m
            JOIN imported_conversation c ON c.id = m.conversation_id
            WHERE m.conversation_id = ?
            """,
            (conv_id,),
        ).fetchall()

        count = 0
        for content, cid, title, source, seq_idx, role, msg_id, created_at in rows:
            conn.execute(
                "INSERT INTO fts_messages"
                "(content, conversation_id, conversation_title, provider,"
                " message_index, message_role, message_id, timestamp)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    content,
                    str(cid),
                    title,
                    source,
                    str(seq_idx),
                    role,
                    str(msg_id),
                    _format_unix_ts(created_at),
                ),
            )
            count += 1

        conn.commit()
        return count
    finally:
        conn.close()


def index_new_note(db_path: str, note_id: int | str) -> None:
    """Index a single new note (called after note creation / clip)."""

    ensure_fts_tables(db_path)
    nid = int(note_id)
    conn = sqlite3.connect(db_path)
    try:
        row = conn.execute(
            "SELECT id, content, tags, timestamp FROM memory_entry WHERE id = ?",
            (nid,),
        ).fetchone()

        if row is None:
            return

        note_id_val, content, tags, timestamp = row
        conn.execute(
            "INSERT INTO fts_notes(content, note_id, tags, timestamp)"
            " VALUES (?, ?, ?, ?)",
            (content, str(note_id_val), tags or "", str(timestamp) if timestamp else ""),
        )
        conn.commit()
    finally:
        conn.close()


def remove_conversation_from_fts(db_path: str, conversation_id: int | str) -> int:
    """Delete all fts_messages rows for one conversation. Returns count deleted."""

    ensure_fts_tables(db_path)
    conv_id = str(int(conversation_id))
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.execute(
            "DELETE FROM fts_messages WHERE conversation_id = ?",
            (conv_id,),
        )
        conn.commit()
        return cur.rowcount
    finally:
        conn.close()


def remove_note_from_fts(db_path: str, note_id: int | str) -> int:
    """Delete the fts_notes row for one note. Returns count deleted (0 or 1)."""

    ensure_fts_tables(db_path)
    nid = str(int(note_id))
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.execute(
            "DELETE FROM fts_notes WHERE note_id = ?",
            (nid,),
        )
        conn.commit()
        return cur.rowcount
    finally:
        conn.close()


def search_fts(db_path: str, query: str, limit: int = 50) -> list[dict]:
    """Full-text search across messages and notes.

    Uses BM25 ranking.  Returns results with snippets.

    Each result dict contains:
    - snippet: str — highlighted excerpt with <mark> tags around matches
    - source_type: str — "imported_message" or "native_note"
    - conversation_id: str | None — for imported messages
    - conversation_title: str | None — for imported messages
    - provider: str | None — "chatgpt", "claude", "gemini"
    - message_index: int | None — position in conversation
    - message_role: str | None — "user" or "assistant"
    - message_id: str | None — DB primary key for deep-linking
    - note_id: str | None — for native notes
    - timestamp: str — ISO timestamp
    - rank: float — BM25 relevance score
    """

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    results: list[dict] = []

    # Search imported messages
    try:
        msg_rows = conn.execute(
            """
            SELECT
                snippet(fts_messages, 0, '<mark>', '</mark>', '\u2026', 40) as snippet,
                conversation_id,
                conversation_title,
                provider,
                message_index,
                message_role,
                message_id,
                timestamp,
                bm25(fts_messages) as rank
            FROM fts_messages
            WHERE fts_messages MATCH ?
            ORDER BY rank
            LIMIT ?
            """,
            (query, limit),
        ).fetchall()

        for row in msg_rows:
            results.append(
                {
                    "snippet": row["snippet"],
                    "source_type": "imported_message",
                    "conversation_id": row["conversation_id"],
                    "conversation_title": row["conversation_title"],
                    "provider": row["provider"],
                    "message_index": int(row["message_index"])
                    if row["message_index"]
                    else None,
                    "message_role": row["message_role"],
                    "message_id": row["message_id"],
                    "note_id": None,
                    "timestamp": row["timestamp"],
                    "rank": row["rank"],
                }
            )
    except sqlite3.OperationalError:
        pass  # FTS table doesn't exist yet

    # Search native notes
    try:
        note_rows = conn.execute(
            """
            SELECT
                snippet(fts_notes, 0, '<mark>', '</mark>', '\u2026', 40) as snippet,
                note_id,
                tags,
                timestamp,
                bm25(fts_notes) as rank
            FROM fts_notes
            WHERE fts_notes MATCH ?
            ORDER BY rank
            LIMIT ?
            """,
            (query, limit),
        ).fetchall()

        for row in note_rows:
            results.append(
                {
                    "snippet": row["snippet"],
                    "source_type": "native_note",
                    "conversation_id": None,
                    "conversation_title": None,
                    "provider": "soulprint",
                    "message_index": None,
                    "message_role": None,
                    "message_id": None,
                    "note_id": row["note_id"],
                    "timestamp": row["timestamp"],
                    "rank": row["rank"],
                }
            )
    except sqlite3.OperationalError:
        pass

    conn.close()

    # BM25 in FTS5 returns negative scores — more negative = more relevant.
    results.sort(key=lambda r: r["rank"])
    return results[:limit]


def _format_unix_ts(unix_ts: float | None) -> str:
    """Format a unix timestamp as ISO string, or empty string if None."""

    if unix_ts is None:
        return ""
    try:
        dt = datetime.fromtimestamp(unix_ts, tz=timezone.utc)
        return dt.isoformat(timespec="seconds").replace("+00:00", "Z")
    except (ValueError, OSError, OverflowError):
        return ""


if __name__ == "__main__":
    import sys

    db_path = sys.argv[1] if len(sys.argv) > 1 else "instance/soulprint.db"
    result = rebuild_fts(db_path)
    print(f"Indexed {result['messages']} messages, {result['notes']} notes")
