"""Tests for the home page Visual Summary Dashboard stats section."""

from __future__ import annotations

import json
import unittest
from datetime import datetime

from src.app import create_app
from src.app.models import ImportedConversation, ImportedMessage, MemoryEntry
from src.app.models.db import db
from src.config import Config
from tests.temp_helpers import make_test_temp_dir, release_app_db_handles


class HomeDashboardTest(unittest.TestCase):
    def setUp(self):
        self.workdir = make_test_temp_dir(self, "home-dashboard")
        self._old_uri = Config.SQLALCHEMY_DATABASE_URI
        Config.SQLALCHEMY_DATABASE_URI = f"sqlite:///{self.workdir}/test.db"
        self.addCleanup(self._restore_sqlite_uri)
        self.app = create_app()
        self.client = self.app.test_client()
        self.addCleanup(release_app_db_handles, self.app, drop_all=True)

    def _restore_sqlite_uri(self):
        Config.SQLALCHEMY_DATABASE_URI = self._old_uri

    def _get_home_html(self) -> str:
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        return response.get_data(as_text=True)

    def _seed_conv(self, source: str, title: str = "Test") -> ImportedConversation:
        conv = ImportedConversation(
            source=source,
            source_conversation_id=f"{source}-{title}-{id(object())}",
            title=title,
        )
        db.session.add(conv)
        db.session.flush()
        return conv

    def _write_traces(self, count: int) -> None:
        """Write minimal valid trace JSONL records to the expected path."""
        trace_path = self.workdir / "answer_traces.jsonl"
        with open(trace_path, "w") as f:
            for i in range(count):
                record = {
                    "trace_id": f"trace-{i}",
                    "created_at": "2026-03-11T00:00:00+00:00",
                    "question": f"Question {i}",
                    "retrieval_terms": f"term{i}",
                    "status": "answered",
                    "answer_text": f"Answer {i}",
                    "citations": [],
                    "source_lanes": [],
                    "notes": [],
                    "fallback_reason": None,
                    "derived_from": "canonical_ledger",
                    "trace_kind": "grounded_answer",
                }
                f.write(json.dumps(record) + "\n")

    # ── Test 1 ──────────────────────────────────────────────────────────────
    def test_home_renders_dashboard_section_empty_db(self):
        html = self._get_home_html()
        self.assertIn("dash-stats", html)
        self.assertIn("Native Entries", html)
        self.assertIn("Imported Conversations", html)
        self.assertIn("Imported Messages", html)
        self.assertIn("Answer Traces", html)

    # ── Test 2 ──────────────────────────────────────────────────────────────
    def test_home_native_count_reflects_seeded_entries(self):
        with self.app.app_context():
            for i in range(3):
                db.session.add(MemoryEntry(
                    timestamp=datetime.utcnow(),
                    role="user",
                    content=f"Native entry {i}",
                    tags="",
                ))
            db.session.commit()

        html = self._get_home_html()
        # "3" should appear in the tile near "Native Entries"
        self.assertIn("Native Entries", html)
        self.assertIn(">3<", html)

    # ── Test 3 ──────────────────────────────────────────────────────────────
    def test_home_imported_conv_count_reflects_seeded_conversations(self):
        with self.app.app_context():
            for i in range(4):
                self._seed_conv("chatgpt", f"Conv {i}")
            db.session.commit()

        html = self._get_home_html()
        self.assertIn("Imported Conversations", html)
        self.assertIn(">4<", html)

    # ── Test 4 ──────────────────────────────────────────────────────────────
    def test_home_imported_msg_count_reflects_seeded_messages(self):
        with self.app.app_context():
            conv = self._seed_conv("chatgpt", "WithMessages")
            for i in range(5):
                msg = ImportedMessage(
                    conversation_id=conv.id,
                    sequence_index=i,
                    role="user",
                    content=f"Message {i}",
                    source_message_id=f"msg-{i}",
                )
                db.session.add(msg)
            db.session.commit()

        html = self._get_home_html()
        self.assertIn("Imported Messages", html)
        self.assertIn(">5<", html)

    # ── Test 5 ──────────────────────────────────────────────────────────────
    def test_home_provider_chart_absent_when_no_imported_conversations(self):
        html = self._get_home_html()
        self.assertNotIn("dash-provider-chart", html)

    # ── Test 6 ──────────────────────────────────────────────────────────────
    def test_home_provider_chart_renders_provider_names(self):
        with self.app.app_context():
            self._seed_conv("chatgpt", "C1")
            self._seed_conv("chatgpt", "C2")
            self._seed_conv("claude", "Cl1")
            self._seed_conv("gemini", "G1")
            db.session.commit()

        html = self._get_home_html()
        self.assertIn("dash-provider-chart", html)
        self.assertIn("chatgpt", html)
        self.assertIn("claude", html)
        self.assertIn("gemini", html)

    # ── Test 7 ──────────────────────────────────────────────────────────────
    def test_home_provider_chart_dominant_provider_bar_is_full_width(self):
        with self.app.app_context():
            for i in range(3):
                self._seed_conv("chatgpt", f"C{i}")
            self._seed_conv("claude", "Cl1")
            db.session.commit()

        html = self._get_home_html()
        # chatgpt (3) is dominant; its bar should be width: 100%
        self.assertEqual(html.count("width: 100%"), 1)

    # ── Test 8 ──────────────────────────────────────────────────────────────
    def test_home_trace_count_reflects_seeded_traces(self):
        self._write_traces(2)

        html = self._get_home_html()
        self.assertIn("Answer Traces", html)
        self.assertIn(">2<", html)

    # ── Test 9 ──────────────────────────────────────────────────────────────
    def test_home_trace_count_zero_when_jsonl_absent(self):
        html = self._get_home_html()
        self.assertIn("Answer Traces", html)
        self.assertIn(">0<", html)

    # ── Test 10 ─────────────────────────────────────────────────────────────
    def test_home_nav_cards_still_present_alongside_stats(self):
        html = self._get_home_html()
        self.assertIn('href="/chats"', html)
        self.assertIn('href="/imported"', html)
        self.assertIn('href="/federated"', html)
        self.assertIn('href="/answer-traces"', html)
        self.assertIn("dash-stats", html)

    # ── Test 11 ─────────────────────────────────────────────────────────────
    def test_home_provider_chart_single_provider_no_division_error(self):
        with self.app.app_context():
            self._seed_conv("gemini", "G1")
            db.session.commit()

        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("width: 100%", html)
        self.assertIn("gemini", html)


if __name__ == "__main__":
    unittest.main()
