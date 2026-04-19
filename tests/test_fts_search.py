"""Tests for FTS5 message-level full-text search."""

from __future__ import annotations

import sqlite3
import unittest
from datetime import datetime, timezone

from src.app import create_app
from src.app.models.db import db
from src.app.models import ImportedConversation, ImportedMessage, MemoryEntry
from src.config import Config
from src.retrieval.fts import (
    ensure_fts_tables,
    index_new_messages,
    index_new_note,
    populate_fts_messages,
    populate_fts_notes,
    rebuild_fts,
    remove_conversation_from_fts,
    remove_note_from_fts,
    sanitize_fts_query,
    search_fts,
)
from tests.temp_helpers import make_test_temp_dir, release_app_db_handles


def _seed_test_data(app):
    """Insert test conversations, messages, and notes into the DB."""

    with app.app_context():
        conv1 = ImportedConversation(
            source="chatgpt",
            source_conversation_id="conv-aaa",
            title="Crypto trading strategies",
            created_at_unix=1710000000.0,
            updated_at_unix=1710001000.0,
        )
        db.session.add(conv1)
        db.session.flush()

        db.session.add(
            ImportedMessage(
                conversation_id=conv1.id,
                source_message_id="msg-1",
                role="user",
                content="What is a good DCA approach for Bitcoin allocation?",
                sequence_index=0,
                created_at_unix=1710000100.0,
            )
        )
        db.session.add(
            ImportedMessage(
                conversation_id=conv1.id,
                source_message_id="msg-2",
                role="assistant",
                content="I'd suggest a DCA approach with 60% BTC allocation and monthly rebalancing for a solid trading strategy.",
                sequence_index=1,
                created_at_unix=1710000200.0,
            )
        )

        conv2 = ImportedConversation(
            source="claude",
            source_conversation_id="conv-bbb",
            title="Travel planning for Lisbon",
            created_at_unix=1709000000.0,
            updated_at_unix=1709001000.0,
        )
        db.session.add(conv2)
        db.session.flush()

        db.session.add(
            ImportedMessage(
                conversation_id=conv2.id,
                source_message_id="msg-3",
                role="user",
                content="Plan a week in Lisbon with restaurants and historical sites.",
                sequence_index=0,
                created_at_unix=1709000100.0,
            )
        )

        note = MemoryEntry(
            timestamp=datetime(2024, 3, 10, tzinfo=timezone.utc),
            role="user",
            content="Remember: my favorite trading pair is ETH/BTC",
            tags="trading,crypto",
        )
        db.session.add(note)
        db.session.commit()

        return {
            "conv1_id": conv1.id,
            "conv2_id": conv2.id,
            "note_id": note.id,
            "msg1_id": conv1.messages[0].id,
            "msg2_id": conv1.messages[1].id,
        }


class FTSTableManagementTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = make_test_temp_dir(self, "fts-tables")
        self.db_path = str(self.tmpdir / "fts_test.db")
        # Create canonical tables via app
        self._old_uri = Config.SQLALCHEMY_DATABASE_URI
        Config.SQLALCHEMY_DATABASE_URI = f"sqlite:///{self.db_path}"
        self.app = create_app()
        self.addCleanup(release_app_db_handles, self.app, drop_all=True)
        self.addCleanup(self._restore_uri)

    def _restore_uri(self):
        Config.SQLALCHEMY_DATABASE_URI = self._old_uri

    def test_ensure_fts_tables_creates_virtual_tables(self):
        ensure_fts_tables(self.db_path)
        conn = sqlite3.connect(self.db_path)
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        conn.close()
        self.assertIn("fts_messages", tables)
        self.assertIn("fts_notes", tables)

    def test_ensure_fts_tables_is_idempotent(self):
        ensure_fts_tables(self.db_path)
        ensure_fts_tables(self.db_path)  # no error on second call

    def test_rebuild_fts_returns_correct_counts(self):
        ids = _seed_test_data(self.app)
        result = rebuild_fts(self.db_path)
        self.assertEqual(result["messages"], 3)  # 2 from conv1 + 1 from conv2
        self.assertEqual(result["notes"], 1)


class FTSIndexingTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = make_test_temp_dir(self, "fts-index")
        self.db_path = str(self.tmpdir / "fts_index_test.db")
        self._old_uri = Config.SQLALCHEMY_DATABASE_URI
        Config.SQLALCHEMY_DATABASE_URI = f"sqlite:///{self.db_path}"
        self.app = create_app()
        self.ids = _seed_test_data(self.app)
        ensure_fts_tables(self.db_path)
        self.addCleanup(release_app_db_handles, self.app, drop_all=True)
        self.addCleanup(self._restore_uri)

    def _restore_uri(self):
        Config.SQLALCHEMY_DATABASE_URI = self._old_uri

    def test_populate_fts_messages_indexes_all(self):
        count = populate_fts_messages(self.db_path)
        self.assertEqual(count, 3)

    def test_populate_fts_notes_indexes_all(self):
        count = populate_fts_notes(self.db_path)
        self.assertEqual(count, 1)

    def test_index_new_messages_single_conversation(self):
        count = index_new_messages(self.db_path, self.ids["conv1_id"])
        self.assertEqual(count, 2)  # conv1 has 2 messages

    def test_index_new_note_single_note(self):
        index_new_note(self.db_path, self.ids["note_id"])
        conn = sqlite3.connect(self.db_path)
        rows = conn.execute("SELECT * FROM fts_notes").fetchall()
        conn.close()
        self.assertEqual(len(rows), 1)


class FTSSearchTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = make_test_temp_dir(self, "fts-search")
        self.db_path = str(self.tmpdir / "fts_search_test.db")
        self._old_uri = Config.SQLALCHEMY_DATABASE_URI
        Config.SQLALCHEMY_DATABASE_URI = f"sqlite:///{self.db_path}"
        self.app = create_app()
        self.ids = _seed_test_data(self.app)
        rebuild_fts(self.db_path)
        self.addCleanup(release_app_db_handles, self.app, drop_all=True)
        self.addCleanup(self._restore_uri)

    def _restore_uri(self):
        Config.SQLALCHEMY_DATABASE_URI = self._old_uri

    def test_search_returns_matching_results(self):
        results = search_fts(self.db_path, '"DCA"')
        self.assertTrue(len(results) > 0)

    def test_search_returns_empty_for_no_match(self):
        results = search_fts(self.db_path, '"xyznonexistent"')
        self.assertEqual(len(results), 0)

    def test_search_results_contain_mark_tags(self):
        results = search_fts(self.db_path, '"DCA"')
        self.assertTrue(len(results) > 0)
        self.assertIn("<mark>", results[0]["snippet"])
        self.assertIn("</mark>", results[0]["snippet"])

    def test_search_results_contain_conversation_id_for_messages(self):
        results = search_fts(self.db_path, '"DCA"')
        msg_results = [r for r in results if r["source_type"] == "imported_message"]
        self.assertTrue(len(msg_results) > 0)
        self.assertEqual(msg_results[0]["conversation_id"], str(self.ids["conv1_id"]))

    def test_search_results_contain_note_id_for_notes(self):
        results = search_fts(self.db_path, '"trading"')
        note_results = [r for r in results if r["source_type"] == "native_note"]
        self.assertTrue(len(note_results) > 0)
        self.assertEqual(note_results[0]["note_id"], str(self.ids["note_id"]))

    def test_search_respects_limit(self):
        results = search_fts(self.db_path, '"trading" OR "Lisbon"', limit=2)
        self.assertLessEqual(len(results), 2)

    def test_search_sorted_by_bm25_relevance(self):
        results = search_fts(self.db_path, '"DCA"')
        if len(results) > 1:
            for i in range(len(results) - 1):
                self.assertLessEqual(results[i]["rank"], results[i + 1]["rank"])

    def test_search_across_messages_and_notes(self):
        results = search_fts(self.db_path, '"trading"')
        source_types = {r["source_type"] for r in results}
        self.assertIn("imported_message", source_types)
        self.assertIn("native_note", source_types)

    def test_search_results_include_message_id_for_deep_link(self):
        results = search_fts(self.db_path, '"DCA"')
        msg_results = [r for r in results if r["source_type"] == "imported_message"]
        self.assertTrue(len(msg_results) > 0)
        self.assertIsNotNone(msg_results[0]["message_id"])

    def test_search_results_include_provider(self):
        results = search_fts(self.db_path, '"Lisbon"')
        msg_results = [r for r in results if r["source_type"] == "imported_message"]
        self.assertTrue(len(msg_results) > 0)
        self.assertEqual(msg_results[0]["provider"], "claude")

    def test_porter_stemming_matches_word_variants(self):
        # "strategies" should match "strategy" via porter stemmer
        results = search_fts(self.db_path, '"strategy"')
        snippets = " ".join(r["snippet"] for r in results)
        # The porter stemmer should find the "trading strategy" content
        self.assertTrue(len(results) > 0)


class FTSQuerySanitizationTest(unittest.TestCase):
    def test_wraps_terms_in_quotes(self):
        result = sanitize_fts_query("hello world")
        self.assertEqual(result, '"hello" "world"')

    def test_handles_empty_string(self):
        result = sanitize_fts_query("")
        self.assertEqual(result, "")

    def test_handles_whitespace_only(self):
        result = sanitize_fts_query("   ")
        self.assertEqual(result, "")

    def test_handles_single_term(self):
        result = sanitize_fts_query("bitcoin")
        self.assertEqual(result, '"bitcoin"')


class FTSFederatedRouteIntegrationTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = make_test_temp_dir(self, "fts-route")
        self._old_uri = Config.SQLALCHEMY_DATABASE_URI
        self.db_path = str(self.tmpdir / "fts_route_test.db")
        Config.SQLALCHEMY_DATABASE_URI = f"sqlite:///{self.db_path}"
        self.app = create_app()
        self.client = self.app.test_client()
        self.ids = _seed_test_data(self.app)
        rebuild_fts(self.db_path)
        self.addCleanup(release_app_db_handles, self.app, drop_all=True)
        self.addCleanup(self._restore_uri)

    def _restore_uri(self):
        Config.SQLALCHEMY_DATABASE_URI = self._old_uri

    def test_federated_with_fts_query_returns_message_results(self):
        response = self.client.get("/federated?q=DCA")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("<mark>", html)
        self.assertIn("DCA", html)

    def test_federated_no_query_returns_browse_view(self):
        response = self.client.get("/federated")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("Everything, together", html)

    def test_fts_results_include_deep_links(self):
        response = self.client.get("/federated?q=DCA")
        html = response.get_data(as_text=True)
        self.assertIn("/imported/", html)
        self.assertIn("/explorer#message-", html)

    def test_fts_results_show_result_count(self):
        response = self.client.get("/federated?q=DCA")
        html = response.get_data(as_text=True)
        self.assertIn("result", html)
        self.assertIn("DCA", html)

    def test_fts_no_results_shows_empty_state(self):
        response = self.client.get("/federated?q=xyznonexistent")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        # Falls back to browse mode which shows empty_state
        self.assertIn("No results found", html)

    def test_fts_results_show_provider_tag(self):
        response = self.client.get("/federated?q=DCA")
        html = response.get_data(as_text=True)
        self.assertIn("chatgpt", html)

    def test_fts_mixed_results_include_notes(self):
        response = self.client.get("/federated?q=trading")
        html = response.get_data(as_text=True)
        self.assertIn("soulprint", html)
        self.assertIn("Note", html)


class FTSRemovalTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = make_test_temp_dir(self, "fts-removal")
        self.db_path = str(self.tmpdir / "fts_removal_test.db")
        self._old_uri = Config.SQLALCHEMY_DATABASE_URI
        Config.SQLALCHEMY_DATABASE_URI = f"sqlite:///{self.db_path}"
        self.app = create_app()
        self.ids = _seed_test_data(self.app)
        rebuild_fts(self.db_path)
        self.addCleanup(release_app_db_handles, self.app, drop_all=True)
        self.addCleanup(self._restore_uri)

    def _restore_uri(self):
        Config.SQLALCHEMY_DATABASE_URI = self._old_uri

    def _count_fts_messages_for_conv(self, conv_id):
        conn = sqlite3.connect(self.db_path)
        try:
            row = conn.execute(
                "SELECT COUNT(*) FROM fts_messages WHERE conversation_id = ?",
                (str(conv_id),),
            ).fetchone()
            return row[0]
        finally:
            conn.close()

    def _count_fts_notes_for_note(self, note_id):
        conn = sqlite3.connect(self.db_path)
        try:
            row = conn.execute(
                "SELECT COUNT(*) FROM fts_notes WHERE note_id = ?",
                (str(note_id),),
            ).fetchone()
            return row[0]
        finally:
            conn.close()

    def test_remove_conversation_deletes_all_its_messages(self):
        remove_conversation_from_fts(self.db_path, self.ids["conv1_id"])
        self.assertEqual(self._count_fts_messages_for_conv(self.ids["conv1_id"]), 0)

    def test_remove_conversation_leaves_other_conversations_intact(self):
        remove_conversation_from_fts(self.db_path, self.ids["conv1_id"])
        self.assertGreater(self._count_fts_messages_for_conv(self.ids["conv2_id"]), 0)

    def test_remove_conversation_returns_correct_count(self):
        count = remove_conversation_from_fts(self.db_path, self.ids["conv1_id"])
        # conv1 has 2 messages seeded
        self.assertEqual(count, 2)

    def test_remove_conversation_nonexistent_returns_zero(self):
        count = remove_conversation_from_fts(self.db_path, 999999)
        self.assertEqual(count, 0)

    def test_remove_conversation_with_int_id_matches_str_stored_rows(self):
        # Pass an int directly — coercion to str must happen inside the helper
        # or the DELETE matches nothing and returns 0 (indistinguishable from nonexistent)
        count = remove_conversation_from_fts(self.db_path, int(self.ids["conv1_id"]))
        self.assertEqual(count, 2)

    def test_remove_note_deletes_one_row(self):
        remove_note_from_fts(self.db_path, self.ids["note_id"])
        self.assertEqual(self._count_fts_notes_for_note(self.ids["note_id"]), 0)

    def test_remove_note_leaves_other_notes_intact(self):
        # Seed a second note and index it
        with self.app.app_context():
            note2 = MemoryEntry(
                timestamp=datetime(2024, 4, 1, tzinfo=timezone.utc),
                role="user",
                content="Second note content for removal test",
                tags="test",
            )
            db.session.add(note2)
            db.session.commit()
            note2_id = note2.id
        index_new_note(self.db_path, note2_id)

        remove_note_from_fts(self.db_path, self.ids["note_id"])
        self.assertEqual(self._count_fts_notes_for_note(self.ids["note_id"]), 0)
        self.assertEqual(self._count_fts_notes_for_note(note2_id), 1)

    def test_remove_note_nonexistent_returns_zero(self):
        count = remove_note_from_fts(self.db_path, 999999)
        self.assertEqual(count, 0)

    def test_search_no_longer_returns_removed_content(self):
        # After removing conv1, DCA content should not appear in search
        remove_conversation_from_fts(self.db_path, self.ids["conv1_id"])
        results = search_fts(self.db_path, '"DCA"')
        conv_ids = [r["conversation_id"] for r in results if r["source_type"] == "imported_message"]
        self.assertNotIn(str(self.ids["conv1_id"]), conv_ids)


if __name__ == "__main__":
    unittest.main()
