"""SoulPrint MCP Server — exposes your local memory to AI agents.

Run with:
    soulprint serve --mcp
    # or directly:
    python -m src.mcp_server

Connects to your local SoulPrint SQLite database and provides tools for
searching, browsing, and retrieving conversation history from any MCP client
(Claude Code, Claude.ai, Cursor, etc.).
"""

from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path
from typing import Optional

from mcp.server.fastmcp import FastMCP

from .retrieval.fts import ensure_fts_tables, rebuild_fts, sanitize_fts_query, search_fts
from .runtime import default_instance_dir


# ---------------------------------------------------------------------------
# Database path resolution
# ---------------------------------------------------------------------------

def _resolve_db_path() -> str:
    """Resolve the SoulPrint database path.

    Priority: SOULPRINT_DB env var > default instance dir.
    """
    env_path = os.getenv("SOULPRINT_DB")
    if env_path:
        return str(Path(env_path).expanduser().resolve())
    return str(default_instance_dir() / "soulprint.db")


def _db_path() -> str:
    """Cached DB path for the server lifetime."""
    if not hasattr(_db_path, "_cached"):
        _db_path._cached = _resolve_db_path()
    return _db_path._cached


# ---------------------------------------------------------------------------
# MCP Server
# ---------------------------------------------------------------------------

mcp = FastMCP(
    "soulprint_mcp",
    instructions=(
        "SoulPrint is a local-first memory system. It stores the user's "
        "imported AI conversation history from ChatGPT, Claude, Gemini, and "
        "other providers. Use these tools to search and retrieve context from "
        "the user's past conversations. All data is local; nothing leaves "
        "the machine."
    ),
)


# ---------------------------------------------------------------------------
# Tool: search
# ---------------------------------------------------------------------------

@mcp.tool(
    name="soulprint_search",
    annotations={
        "title": "Search conversation memory",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
def soulprint_search(query: str, limit: int = 20) -> str:
    """Search across all imported conversations and native notes.

    Uses FTS5 full-text search with BM25 ranking. Returns snippets with
    matched terms highlighted. Use short, specific keywords for best results.

    Args:
        query: Search keywords (e.g. "SQLite schema", "trading strategy").
        limit: Max results to return (default 20, max 100).

    Returns:
        JSON array of search results with snippets, provider, conversation
        title, and relevance ranking.
    """
    limit = min(max(1, limit), 100)
    db = _db_path()

    ensure_fts_tables(db)
    safe_query = sanitize_fts_query(query)
    if not safe_query:
        return json.dumps({"results": [], "message": "Empty query"})

    results = search_fts(db, safe_query, limit=limit)

    # Strip HTML <mark> tags for clean agent consumption
    for r in results:
        if r.get("snippet"):
            r["snippet"] = r["snippet"].replace("<mark>", "").replace("</mark>", "")

    return json.dumps({"query": query, "result_count": len(results), "results": results})


# ---------------------------------------------------------------------------
# Tool: list conversations
# ---------------------------------------------------------------------------

@mcp.tool(
    name="soulprint_list_conversations",
    annotations={
        "title": "List imported conversations",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
def soulprint_list_conversations(
    provider: Optional[str] = None,
    limit: int = 25,
    offset: int = 0,
) -> str:
    """List imported conversations, optionally filtered by provider.

    Args:
        provider: Filter by provider name ("chatgpt", "claude", "gemini").
                  Omit to list all providers.
        limit: Max conversations to return (default 25, max 100).
        offset: Pagination offset (default 0).

    Returns:
        JSON with conversation list (id, title, provider, message count,
        timestamps) and total count.
    """
    limit = min(max(1, limit), 100)
    offset = max(0, offset)
    db = _db_path()

    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row

    try:
        # Count total
        count_sql = "SELECT COUNT(*) FROM imported_conversation"
        list_sql = """
            SELECT
                ic.id,
                ic.title,
                ic.source AS provider,
                ic.source_conversation_id,
                ic.created_at_unix,
                ic.updated_at_unix,
                COUNT(im.id) AS message_count
            FROM imported_conversation ic
            LEFT JOIN imported_message im ON im.conversation_id = ic.id
        """

        params: list = []
        if provider:
            count_sql += " WHERE source = ?"
            list_sql += " WHERE ic.source = ?"
            params.append(provider.lower().strip())

        count = conn.execute(count_sql, params).fetchone()[0]

        list_sql += """
            GROUP BY ic.id
            ORDER BY COALESCE(ic.updated_at_unix, ic.created_at_unix, 0) DESC
            LIMIT ? OFFSET ?
        """
        rows = conn.execute(list_sql, params + [limit, offset]).fetchall()

        conversations = [
            {
                "id": row["id"],
                "title": row["title"],
                "provider": row["provider"],
                "source_conversation_id": row["source_conversation_id"],
                "message_count": row["message_count"],
                "created_at_unix": row["created_at_unix"],
                "updated_at_unix": row["updated_at_unix"],
            }
            for row in rows
        ]

        return json.dumps({
            "total": count,
            "offset": offset,
            "limit": limit,
            "conversations": conversations,
        })
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Tool: get conversation
# ---------------------------------------------------------------------------

@mcp.tool(
    name="soulprint_get_conversation",
    annotations={
        "title": "Get full conversation with messages",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
def soulprint_get_conversation(conversation_id: int, max_messages: int = 200) -> str:
    """Retrieve a full conversation with all its messages.

    Args:
        conversation_id: The numeric conversation ID from list or search results.
        max_messages: Max messages to return (default 200, max 1000).
                      Messages are returned in chronological order.

    Returns:
        JSON with conversation metadata and ordered message array.
    """
    max_messages = min(max(1, max_messages), 1000)
    db = _db_path()

    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row

    try:
        conv = conn.execute(
            """
            SELECT id, title, source, source_conversation_id,
                   created_at_unix, updated_at_unix
            FROM imported_conversation WHERE id = ?
            """,
            (conversation_id,),
        ).fetchone()

        if not conv:
            return json.dumps({"error": f"Conversation {conversation_id} not found"})

        messages = conn.execute(
            """
            SELECT id, role, content, sequence_index, created_at_unix
            FROM imported_message
            WHERE conversation_id = ?
            ORDER BY sequence_index ASC, id ASC
            LIMIT ?
            """,
            (conversation_id, max_messages),
        ).fetchall()

        return json.dumps({
            "conversation": {
                "id": conv["id"],
                "title": conv["title"],
                "provider": conv["source"],
                "source_conversation_id": conv["source_conversation_id"],
                "created_at_unix": conv["created_at_unix"],
                "updated_at_unix": conv["updated_at_unix"],
            },
            "message_count": len(messages),
            "messages": [
                {
                    "id": m["id"],
                    "role": m["role"],
                    "content": m["content"],
                    "sequence_index": m["sequence_index"],
                    "created_at_unix": m["created_at_unix"],
                }
                for m in messages
            ],
        })
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Tool: stats
# ---------------------------------------------------------------------------

@mcp.tool(
    name="soulprint_stats",
    annotations={
        "title": "Get workspace statistics",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
def soulprint_stats() -> str:
    """Get an overview of what's in the SoulPrint database.

    Returns conversation count, message count, provider breakdown,
    and native note count. Useful for understanding what memory is
    available before searching.

    Returns:
        JSON with total counts and per-provider breakdown.
    """
    db = _db_path()

    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row

    try:
        total_convs = conn.execute("SELECT COUNT(*) FROM imported_conversation").fetchone()[0]
        total_msgs = conn.execute("SELECT COUNT(*) FROM imported_message").fetchone()[0]

        providers = conn.execute(
            """
            SELECT source AS provider, COUNT(*) AS conversation_count
            FROM imported_conversation
            GROUP BY source
            ORDER BY conversation_count DESC
            """
        ).fetchall()

        try:
            total_notes = conn.execute("SELECT COUNT(*) FROM memory_entry").fetchone()[0]
        except sqlite3.OperationalError:
            total_notes = 0

        return json.dumps({
            "database_path": db,
            "total_conversations": total_convs,
            "total_messages": total_msgs,
            "total_notes": total_notes,
            "providers": [
                {"provider": p["provider"], "conversation_count": p["conversation_count"]}
                for p in providers
            ],
        })
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Tool: rebuild search index
# ---------------------------------------------------------------------------

@mcp.tool(
    name="soulprint_rebuild_index",
    annotations={
        "title": "Rebuild the search index",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
def soulprint_rebuild_index() -> str:
    """Rebuild the FTS5 full-text search index.

    Call this after importing new conversations, or if search results
    seem incomplete. Safe to run at any time; rebuilds from canonical data.

    Returns:
        JSON with count of indexed messages and notes.
    """
    db = _db_path()
    counts = rebuild_fts(db)
    return json.dumps({"status": "ok", "indexed": counts})


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    """Run the MCP server over stdio transport."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
