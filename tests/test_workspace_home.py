"""Tests for the canonical workspace rendered at `/`."""

from __future__ import annotations

import json
import unittest
from datetime import datetime

from src.app import create_app
from src.app.models import ImportedConversation, ImportedMessage, MemoryEntry
from src.app.models.db import db
from src.config import Config
from tests.temp_helpers import make_test_temp_dir, release_app_db_handles


class WorkspaceHomeTest(unittest.TestCase):
    def setUp(self):
        self.workdir = make_test_temp_dir(self, "workspace-home")
        self._old_uri = Config.SQLALCHEMY_DATABASE_URI
        Config.SQLALCHEMY_DATABASE_URI = f"sqlite:///{self.workdir}/test.db"
        self.addCleanup(self._restore_sqlite_uri)
        self.app = create_app()
        self.client = self.app.test_client()
        self.addCleanup(release_app_db_handles, self.app, drop_all=True)

    def _restore_sqlite_uri(self):
        Config.SQLALCHEMY_DATABASE_URI = self._old_uri

    def _get_workspace_html(self) -> str:
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
        trace_path = self.workdir / "answer_traces.jsonl"
        with open(trace_path, "w", encoding="utf-8") as f:
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

    def test_workspace_renders_workspace_blocks_empty_db(self):
        html = self._get_workspace_html()
        self.assertIn("Continuity Status", html)
        self.assertIn("Provider Coverage", html)
        self.assertIn("Resume Recent Work", html)
        self.assertIn("Search Handoff", html)
        self.assertIn("Passport / Integrity Status", html)
        self.assertIn("Next Actions", html)
        self.assertIn("Your workspace is ready.", html)

    def test_workspace_continuity_counts_reflect_seeded_data(self):
        with self.app.app_context():
            conv = self._seed_conv("chatgpt", "WithMessages")
            for i in range(2):
                db.session.add(
                    MemoryEntry(
                        timestamp=datetime.utcnow(),
                        role="user",
                        content=f"Native entry {i}",
                        tags="",
                    )
                )
            for i in range(3):
                db.session.add(
                    ImportedMessage(
                        conversation_id=conv.id,
                        sequence_index=i,
                        role="user",
                        content=f"Message {i}",
                        source_message_id=f"msg-{i}",
                    )
                )
            db.session.commit()

        self._write_traces(4)
        html = self._get_workspace_html()

        self.assertIn("You have 1 imported conversations across 1 providers and 2 native memory entries.", html)
        self.assertIn("Native entries</span><strong>2</strong>", html)
        self.assertIn("Imported conversations</span><strong>1</strong>", html)
        self.assertIn("Imported messages</span><strong>3</strong>", html)
        self.assertIn("Answer traces</span><strong>4</strong>", html)

    def test_workspace_provider_coverage_renders_provider_badges(self):
        with self.app.app_context():
            self._seed_conv("chatgpt", "C1")
            self._seed_conv("claude", "C2")
            db.session.commit()

        html = self._get_workspace_html()
        self.assertIn("chatgpt · 1", html)
        self.assertIn("claude · 1", html)

    def test_workspace_resume_recent_work_renders_links(self):
        with self.app.app_context():
            conv = self._seed_conv("gemini", "Recent import")
            db.session.add(
                MemoryEntry(
                    timestamp=datetime.utcnow(),
                    role="assistant",
                    content="Native resume preview content",
                    tags="",
                )
            )
            db.session.commit()
            conv_id = conv.id

        self._write_traces(1)
        html = self._get_workspace_html()
        self.assertIn(f'href="/imported/{conv_id}/explorer"', html)
        self.assertIn('href="/memory/1"', html)
        self.assertIn('href="/answer-traces/trace-0"', html)


if __name__ == "__main__":
    unittest.main()
