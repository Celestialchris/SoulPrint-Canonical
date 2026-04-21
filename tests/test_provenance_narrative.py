"""Tests for Provenance Narrative — search callout and Wrapped origin block."""

from __future__ import annotations

import unittest

from src.app import create_app
from src.app.models import ImportedConversation, ImportedMessage
from src.app.models.db import db
from src.app.viewmodels.wrapped import build_wrapped_summary
from src.config import Config
from src.retrieval.fts import rebuild_fts
from tests.temp_helpers import make_test_temp_dir, release_app_db_handles


def _seed_two_conversations(app, *, shared_word: str = "archipelago") -> dict:
    """Insert two conversations whose messages both contain shared_word."""
    with app.app_context():
        conv_old = ImportedConversation(
            source="chatgpt",
            source_conversation_id="prov-old-001",
            title="The early discussion",
            created_at_unix=1700000000.0,  # older
            updated_at_unix=1700001000.0,
        )
        db.session.add(conv_old)
        db.session.flush()
        db.session.add(
            ImportedMessage(
                conversation_id=conv_old.id,
                source_message_id="prov-msg-001",
                role="user",
                content=f"First mention of {shared_word} in my notes.",
                sequence_index=0,
                created_at_unix=1700000100.0,
            )
        )

        conv_new = ImportedConversation(
            source="claude",
            source_conversation_id="prov-new-002",
            title="The later discussion",
            created_at_unix=1710000000.0,  # newer
            updated_at_unix=1710001000.0,
        )
        db.session.add(conv_new)
        db.session.flush()
        db.session.add(
            ImportedMessage(
                conversation_id=conv_new.id,
                source_message_id="prov-msg-002",
                role="assistant",
                content=f"Revisiting {shared_word} concepts again.",
                sequence_index=0,
                created_at_unix=1710000100.0,
            )
        )

        db.session.commit()
        return {"old_id": conv_old.id, "new_id": conv_new.id}


class SearchCalloutTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = make_test_temp_dir(self, "provenance-search")
        self.db_path = str(self.tmpdir / "test.db")
        self._old_uri = Config.SQLALCHEMY_DATABASE_URI
        Config.SQLALCHEMY_DATABASE_URI = f"sqlite:///{self.db_path}"
        self.app = create_app()
        self.client = self.app.test_client()
        self.addCleanup(release_app_db_handles, self.app, drop_all=True)
        self.addCleanup(self._restore_uri)

    def _restore_uri(self):
        Config.SQLALCHEMY_DATABASE_URI = self._old_uri

    def test_search_callout_appears_for_multi_result(self):
        _seed_two_conversations(self.app, shared_word="archipelago")
        rebuild_fts(self.db_path)

        response = self.client.get("/federated?q=archipelago")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("provenance-callout", html)
        self.assertIn("Earliest mention in these results", html)

    def test_search_callout_suppressed_for_single_result(self):
        with self.app.app_context():
            conv = ImportedConversation(
                source="chatgpt",
                source_conversation_id="prov-single-001",
                title="Unique topic",
                created_at_unix=1700000000.0,
                updated_at_unix=1700001000.0,
            )
            db.session.add(conv)
            db.session.flush()
            db.session.add(
                ImportedMessage(
                    conversation_id=conv.id,
                    source_message_id="prov-single-msg-001",
                    role="user",
                    content="A word that appears only once: xylophonequartz.",
                    sequence_index=0,
                    created_at_unix=1700000100.0,
                )
            )
            db.session.commit()

        rebuild_fts(self.db_path)

        response = self.client.get("/federated?q=xylophonequartz")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertNotIn("provenance-callout", html)
        self.assertNotIn("Earliest mention in these results", html)

    def test_search_callout_suppressed_in_archaeology_mode(self):
        _seed_two_conversations(self.app, shared_word="archipelago")
        rebuild_fts(self.db_path)

        response = self.client.get("/federated?q=archipelago&mode=archaeology")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertNotIn("provenance-callout", html)
        self.assertNotIn("Earliest mention in these results", html)


class WrappedOriginBlockTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = make_test_temp_dir(self, "provenance-wrapped")
        self.db_path = str(self.tmpdir / "test.db")
        self._old_uri = Config.SQLALCHEMY_DATABASE_URI
        Config.SQLALCHEMY_DATABASE_URI = f"sqlite:///{self.db_path}"
        self.app = create_app()
        self.addCleanup(release_app_db_handles, self.app, drop_all=True)
        self.addCleanup(self._restore_uri)

    def _restore_uri(self):
        Config.SQLALCHEMY_DATABASE_URI = self._old_uri

    def test_wrapped_earliest_conversation_populated(self):
        ids = _seed_two_conversations(self.app)

        with self.app.app_context():
            summary = build_wrapped_summary(sqlite_path=self.db_path)

        self.assertIsNotNone(summary.earliest_conversation)
        ec = summary.earliest_conversation
        self.assertEqual(ec["id"], ids["old_id"])
        self.assertEqual(ec["provider"], "chatgpt")
        self.assertEqual(ec["created_at_unix"], 1700000000.0)
        self.assertEqual(ec["title"], "The early discussion")

    def test_wrapped_earliest_conversation_none_for_fewer_than_two(self):
        with self.app.app_context():
            conv = ImportedConversation(
                source="claude",
                source_conversation_id="prov-only-001",
                title="The only conversation",
                created_at_unix=1700000000.0,
                updated_at_unix=1700001000.0,
            )
            db.session.add(conv)
            db.session.commit()

            summary = build_wrapped_summary(sqlite_path=self.db_path)

        self.assertIsNone(summary.earliest_conversation)
