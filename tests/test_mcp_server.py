"""Tests for the SoulPrint MCP server tools.

These tests exercise the tool functions directly (without MCP transport)
to verify they return correct JSON against a real SQLite database.
"""

from __future__ import annotations

import json
import os
import sqlite3
import tempfile
from pathlib import Path
from unittest import mock

import pytest

from src.retrieval.fts import ensure_fts_tables, populate_fts_messages


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def sample_db(tmp_path):
    """Create a minimal SoulPrint database with test data."""
    db_path = str(tmp_path / "test.db")
    conn = sqlite3.connect(db_path)

    conn.executescript("""
        CREATE TABLE IF NOT EXISTS imported_conversation (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            source TEXT NOT NULL,
            source_conversation_id TEXT NOT NULL,
            created_at_unix REAL,
            updated_at_unix REAL
        );

        CREATE TABLE IF NOT EXISTS imported_message (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            sequence_index INTEGER NOT NULL DEFAULT 0,
            created_at_unix REAL,
            FOREIGN KEY (conversation_id) REFERENCES imported_conversation(id)
        );

        CREATE TABLE IF NOT EXISTS memory_entry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            tags TEXT,
            timestamp DATETIME
        );

        INSERT INTO imported_conversation (title, source, source_conversation_id, created_at_unix, updated_at_unix)
        VALUES
            ('SQLite schema decisions', 'chatgpt', 'conv-001', 1700000000, 1700001000),
            ('Python async patterns', 'claude', 'conv-002', 1700002000, 1700003000),
            ('Recipe for carbonara', 'gemini', 'conv-003', 1700004000, 1700005000);

        INSERT INTO imported_message (conversation_id, role, content, sequence_index, created_at_unix)
        VALUES
            (1, 'user', 'How should I design the SQLite schema for a local-first app?', 0, 1700000100),
            (1, 'assistant', 'Use a canonical ledger pattern with stable IDs and timestamps.', 1, 1700000200),
            (2, 'user', 'Explain async/await in Python 3.12', 0, 1700002100),
            (2, 'assistant', 'Python asyncio uses an event loop with coroutines.', 1, 1700002200),
            (3, 'user', 'How do I make authentic carbonara?', 0, 1700004100),
            (3, 'assistant', 'Use guanciale, pecorino, eggs, and black pepper. No cream.', 1, 1700004200);

        INSERT INTO memory_entry (content, role, tags, timestamp)
        VALUES ('SoulPrint uses SQLite as canonical ledger', 'user', 'architecture', '2024-01-15 10:00:00');
    """)
    conn.close()

    # Build FTS index
    ensure_fts_tables(db_path)
    populate_fts_messages(db_path)

    return db_path


@pytest.fixture(autouse=True)
def _patch_db_path(sample_db):
    """Patch the MCP server to use our test database."""
    # Clear cached path
    if hasattr(_db_path_func, "_cached"):
        delattr(_db_path_func, "_cached")

    with mock.patch.dict(os.environ, {"SOULPRINT_DB": sample_db}):
        # Re-import to pick up the env var
        if hasattr(_db_path_func, "_cached"):
            delattr(_db_path_func, "_cached")
        yield

    if hasattr(_db_path_func, "_cached"):
        delattr(_db_path_func, "_cached")


# We need a reference to the actual _db_path function to clear its cache
from src.mcp_server import _db_path as _db_path_func


# ---------------------------------------------------------------------------
# Import tools (after patching is set up)
# ---------------------------------------------------------------------------

from src.mcp_server import (
    soulprint_get_conversation,
    soulprint_list_conversations,
    soulprint_rebuild_index,
    soulprint_search,
    soulprint_stats,
)


# ---------------------------------------------------------------------------
# Tests: soulprint_stats
# ---------------------------------------------------------------------------

class TestStats:
    def test_returns_counts(self, sample_db):
        result = json.loads(soulprint_stats())
        assert result["total_conversations"] == 3
        assert result["total_messages"] == 6
        assert result["total_notes"] == 1
        assert len(result["providers"]) == 3

    def test_provider_breakdown(self, sample_db):
        result = json.loads(soulprint_stats())
        providers = {p["provider"]: p["conversation_count"] for p in result["providers"]}
        assert providers["chatgpt"] == 1
        assert providers["claude"] == 1
        assert providers["gemini"] == 1


# ---------------------------------------------------------------------------
# Tests: soulprint_list_conversations
# ---------------------------------------------------------------------------

class TestListConversations:
    def test_lists_all(self, sample_db):
        result = json.loads(soulprint_list_conversations())
        assert result["total"] == 3
        assert len(result["conversations"]) == 3

    def test_filter_by_provider(self, sample_db):
        result = json.loads(soulprint_list_conversations(provider="chatgpt"))
        assert result["total"] == 1
        assert result["conversations"][0]["title"] == "SQLite schema decisions"

    def test_pagination(self, sample_db):
        result = json.loads(soulprint_list_conversations(limit=1, offset=0))
        assert len(result["conversations"]) == 1
        assert result["total"] == 3

        result2 = json.loads(soulprint_list_conversations(limit=1, offset=1))
        assert result2["conversations"][0]["id"] != result["conversations"][0]["id"]

    def test_unknown_provider_returns_empty(self, sample_db):
        result = json.loads(soulprint_list_conversations(provider="discord"))
        assert result["total"] == 0
        assert result["conversations"] == []


# ---------------------------------------------------------------------------
# Tests: soulprint_get_conversation
# ---------------------------------------------------------------------------

class TestGetConversation:
    def test_returns_messages(self, sample_db):
        result = json.loads(soulprint_get_conversation(conversation_id=1))
        assert result["conversation"]["title"] == "SQLite schema decisions"
        assert result["message_count"] == 2
        assert result["messages"][0]["role"] == "user"
        assert result["messages"][1]["role"] == "assistant"

    def test_not_found(self, sample_db):
        result = json.loads(soulprint_get_conversation(conversation_id=999))
        assert "error" in result

    def test_message_limit(self, sample_db):
        result = json.loads(soulprint_get_conversation(conversation_id=1, max_messages=1))
        assert result["message_count"] == 1


# ---------------------------------------------------------------------------
# Tests: soulprint_search
# ---------------------------------------------------------------------------

class TestSearch:
    def test_finds_by_keyword(self, sample_db):
        result = json.loads(soulprint_search(query="SQLite"))
        assert result["result_count"] > 0
        assert any("SQLite" in r.get("snippet", "") for r in result["results"])

    def test_empty_query(self, sample_db):
        result = json.loads(soulprint_search(query=""))
        assert result["results"] == []

    def test_no_html_marks_in_snippets(self, sample_db):
        result = json.loads(soulprint_search(query="carbonara"))
        for r in result["results"]:
            assert "<mark>" not in r.get("snippet", "")

    def test_respects_limit(self, sample_db):
        result = json.loads(soulprint_search(query="the", limit=1))
        assert len(result["results"]) <= 1


# ---------------------------------------------------------------------------
# Tests: soulprint_rebuild_index
# ---------------------------------------------------------------------------

class TestRebuildIndex:
    def test_rebuild_succeeds(self, sample_db):
        result = json.loads(soulprint_rebuild_index())
        assert result["status"] == "ok"
        assert "indexed" in result
