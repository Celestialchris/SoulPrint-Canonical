"""Tests for the Wrapped Summary viewmodel and /summary route."""

from __future__ import annotations

import json
import unittest
from datetime import datetime, timezone
from pathlib import Path

from src.app import create_app
from src.app.models import ImportedConversation, ImportedMessage, MemoryEntry
from src.app.models.db import db
from src.app.viewmodels.wrapped import WrappedSummary, build_wrapped_summary
from src.config import Config
from tests.temp_helpers import make_test_temp_dir, release_app_db_handles


class WrappedSummaryTest(unittest.TestCase):
    def setUp(self):
        self.workdir = make_test_temp_dir(self, "wrapped-summary")
        self._old_uri = Config.SQLALCHEMY_DATABASE_URI
        Config.SQLALCHEMY_DATABASE_URI = f"sqlite:///{self.workdir}/test.db"
        self.addCleanup(self._restore_sqlite_uri)
        self.app = create_app()
        self.client = self.app.test_client()
        self.addCleanup(release_app_db_handles, self.app, drop_all=True)

    def _restore_sqlite_uri(self):
        Config.SQLALCHEMY_DATABASE_URI = self._old_uri

    def _sqlite_path(self) -> str:
        return str(self.workdir / "test.db")

    def _seed_conv(
        self,
        source: str,
        title: str = "Test",
        created_at_unix: float | None = None,
        updated_at_unix: float | None = None,
    ) -> ImportedConversation:
        conv = ImportedConversation(
            source=source,
            source_conversation_id=f"{source}-{title}-{id(object())}",
            title=title,
            created_at_unix=created_at_unix,
            updated_at_unix=updated_at_unix,
        )
        db.session.add(conv)
        db.session.flush()
        return conv

    def _add_messages(
        self, conv: ImportedConversation, roles: list[str], ts_base: float = 1700000000.0
    ) -> None:
        for i, role in enumerate(roles):
            db.session.add(
                ImportedMessage(
                    conversation_id=conv.id,
                    sequence_index=i,
                    role=role,
                    content=f"Message {i} from {role}",
                    source_message_id=f"msg-{conv.id}-{i}",
                    created_at_unix=ts_base + i * 60,
                )
            )

    # ------------------------------------------------------------------
    # Test 1: Viewmodel stats correct from seeded data
    # ------------------------------------------------------------------
    def test_viewmodel_stats_correct_from_seeded_data(self):
        """Seed 2 imported conversations with messages + 1 native entry.
        Assert total_conversations=3, total_messages=6 (5 imported + 1 native).
        """
        with self.app.app_context():
            conv1 = self._seed_conv("chatgpt", "Conv1", created_at_unix=1700000000.0)
            self._add_messages(conv1, ["user", "assistant", "user"])  # 3 messages

            conv2 = self._seed_conv("claude", "Conv2", created_at_unix=1700100000.0)
            self._add_messages(conv2, ["user", "assistant"])  # 2 messages

            db.session.add(
                MemoryEntry(
                    timestamp=datetime(2024, 1, 15, tzinfo=timezone.utc),
                    role="user",
                    content="Native entry",
                    tags="",
                )
            )
            db.session.commit()

            summary = build_wrapped_summary(sqlite_path=self._sqlite_path())

        self.assertIsInstance(summary, WrappedSummary)
        self.assertEqual(summary.total_conversations, 3)
        self.assertEqual(summary.total_messages, 6)  # 5 imported + 1 native
        self.assertTrue(summary.has_data)

    # ------------------------------------------------------------------
    # Test 2: GET /summary returns 200 (will fail until Task 2)
    # ------------------------------------------------------------------
    def test_get_summary_returns_200(self):
        """GET /summary returns 200. Will fail until Task 2 adds the route."""
        with self.app.app_context():
            self._seed_conv("chatgpt", "SomeConv")
            db.session.commit()

        response = self.client.get("/summary")
        self.assertEqual(response.status_code, 200)

    # ------------------------------------------------------------------
    # Test 3: Provider percentages sum to approximately 100
    # ------------------------------------------------------------------
    def test_provider_percentages_sum_to_approximately_100(self):
        """Seed 3 conversations (2 chatgpt, 1 claude). Assert sum of
        percentages is approximately 100.
        """
        with self.app.app_context():
            self._seed_conv("chatgpt", "C1")
            self._seed_conv("chatgpt", "C2")
            self._seed_conv("claude", "C3")
            db.session.commit()

            summary = build_wrapped_summary(sqlite_path=self._sqlite_path())

        total_pct = sum(p["percentage"] for p in summary.providers)
        self.assertAlmostEqual(total_pct, 100.0, delta=1.0)
        # chatgpt should have 2/3, claude 1/3
        chatgpt = next(p for p in summary.providers if p["name"] == "chatgpt")
        claude = next(p for p in summary.providers if p["name"] == "claude")
        self.assertEqual(chatgpt["count"], 2)
        self.assertEqual(claude["count"], 1)

    # ------------------------------------------------------------------
    # Test 4: Empty DB renders empty state (will fail until Task 2)
    # ------------------------------------------------------------------
    def test_empty_db_renders_empty_state(self):
        """GET /summary on empty DB returns 200 with empty-state messaging.
        Will fail until Task 2 adds the route.
        """
        response = self.client.get("/summary")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("Import your first conversation", html)

    # ------------------------------------------------------------------
    # Test 5: Generated by SoulPrint present (will fail until Task 2)
    # ------------------------------------------------------------------
    def test_generated_by_soulprint_present(self):
        """Seed data, GET /summary, assert 'Generated by SoulPrint' in HTML.
        Will fail until Task 2 adds the route.
        """
        with self.app.app_context():
            conv = self._seed_conv("chatgpt", "TestConv")
            self._add_messages(conv, ["user", "assistant"])
            db.session.commit()

        response = self.client.get("/summary")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("Generated by SoulPrint", html)

    # ------------------------------------------------------------------
    # Test 6: Topic section absent when no topic data (will fail until Task 2)
    # ------------------------------------------------------------------
    def test_topic_section_absent_when_no_topic_data(self):
        """Seed data, GET /summary, assert 'Topics' not in HTML.
        Will fail until Task 2 adds the route.
        """
        with self.app.app_context():
            conv = self._seed_conv("chatgpt", "TestConv")
            self._add_messages(conv, ["user", "assistant"])
            db.session.commit()

        response = self.client.get("/summary")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertNotIn("Topics", html)

    # ------------------------------------------------------------------
    # Test 7: Unfinished threads count is 0 when last message is assistant
    # ------------------------------------------------------------------
    def test_unfinished_threads_count_present_when_zero(self):
        """Seed conversation where last message is assistant (answered).
        Assert unfinished_threads['count'] == 0.
        """
        with self.app.app_context():
            conv = self._seed_conv("chatgpt", "AnsweredConv")
            self._add_messages(conv, ["user", "assistant"])  # last is assistant
            db.session.commit()

            summary = build_wrapped_summary(sqlite_path=self._sqlite_path())

        self.assertEqual(summary.unfinished_threads["count"], 0)
        self.assertEqual(summary.unfinished_threads["titles"], [])

    # ------------------------------------------------------------------
    # Test 8: POST /import redirects to /summary (will fail until Task 3)
    # ------------------------------------------------------------------
    def test_post_first_import_redirects_to_summary(self):
        """POST /import with fixture on empty DB should redirect 302 to
        /summary. Will fail until Task 3 adds the redirect.
        """
        fixture_path = Path(__file__).resolve().parent.parent / "sample_data" / "chatgpt.json"
        if not fixture_path.exists():
            self.skipTest(f"Fixture not found at {fixture_path}")

        with open(fixture_path, "rb") as f:
            response = self.client.post(
                "/import",
                data={"export_file": (f, "chatgpt.json")},
                content_type="multipart/form-data",
            )

        self.assertEqual(response.status_code, 302)
        self.assertIn("/summary", response.headers.get("Location", ""))


if __name__ == "__main__":
    unittest.main()
