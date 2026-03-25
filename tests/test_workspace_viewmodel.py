"""Unit tests for workspace viewmodel aggregation."""

from __future__ import annotations

import json
import unittest
from datetime import datetime

from src.app import create_app
from src.app.models import ImportedConversation, ImportedMessage, MemoryEntry
from src.app.models.db import db
from src.app.viewmodels.workspace import build_workspace_summary
from src.answering.trace import default_trace_store_path
from src.config import Config
from tests.temp_helpers import make_test_temp_dir, release_app_db_handles


class WorkspaceViewmodelTest(unittest.TestCase):
    def setUp(self):
        self.workdir = make_test_temp_dir(self, "workspace-viewmodel")
        self._old_uri = Config.SQLALCHEMY_DATABASE_URI
        Config.SQLALCHEMY_DATABASE_URI = f"sqlite:///{self.workdir}/test.db"
        self.addCleanup(self._restore_sqlite_uri)
        self.app = create_app()
        self.addCleanup(release_app_db_handles, self.app, drop_all=True)

    def _restore_sqlite_uri(self):
        Config.SQLALCHEMY_DATABASE_URI = self._old_uri

    def _trace_path(self):
        return default_trace_store_path(str(self.workdir / "test.db"))

    def test_workspace_summary_empty_state(self):
        with self.app.app_context():
            summary = build_workspace_summary(trace_store_path=self._trace_path())

        self.assertFalse(summary.has_any_data)
        self.assertEqual(summary.providers, [])
        self.assertEqual(summary.trace_count, 0)
        self.assertEqual(summary.recent_imported, [])
        self.assertEqual(summary.recent_native, [])
        self.assertEqual(summary.recent_traces, [])

    def test_workspace_summary_includes_recent_and_counts(self):
        with self.app.app_context():
            conv = ImportedConversation(
                source="chatgpt",
                source_conversation_id="conv-1",
                title="Imported title",
            )
            db.session.add(conv)
            db.session.flush()
            db.session.add(
                ImportedMessage(
                    conversation_id=conv.id,
                    sequence_index=0,
                    role="user",
                    content="message",
                    source_message_id="m1",
                )
            )
            db.session.add(
                MemoryEntry(
                    timestamp=datetime.utcnow(),
                    role="user",
                    content="Native content preview",
                    tags="",
                )
            )
            db.session.commit()

            trace_path = self._trace_path()
            trace_path.write_text(
                json.dumps(
                    {
                        "trace_id": "trace-1",
                        "created_at": "2026-03-11T00:00:00+00:00",
                        "question": "What happened?",
                        "status": "answered",
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            summary = build_workspace_summary(trace_store_path=trace_path)

        self.assertTrue(summary.has_any_data)
        self.assertEqual(summary.native_count, 1)
        self.assertEqual(summary.imported_conversation_count, 1)
        self.assertEqual(summary.imported_message_count, 1)
        self.assertEqual(summary.trace_count, 1)
        self.assertEqual(summary.providers[0]["name"], "chatgpt")
        self.assertEqual(summary.recent_imported[0]["title"], "Imported title")
        self.assertIn("Native content preview", summary.recent_native[0]["preview"])
        self.assertEqual(summary.recent_traces[0]["trace_id"], "trace-1")


    def test_provider_recent_includes_most_recent_per_provider(self):
        with self.app.app_context():
            # Seed 3 chatgpt conversations
            for i in range(3):
                conv = ImportedConversation(
                    source="chatgpt",
                    source_conversation_id=f"chatgpt-{i}",
                    title=f"ChatGPT conv {i}",
                )
                db.session.add(conv)
            # Seed 1 claude conversation
            conv_claude = ImportedConversation(
                source="claude",
                source_conversation_id="claude-0",
                title="Claude conv 0",
            )
            db.session.add(conv_claude)
            db.session.commit()

            summary = build_workspace_summary(trace_store_path=self._trace_path())

            self.assertEqual(len(summary.provider_recent), 2)
            # Ordered by count desc
            chatgpt_entry = summary.provider_recent[0]
            self.assertEqual(chatgpt_entry["provider"], "chatgpt")
            self.assertEqual(chatgpt_entry["count"], 3)
            self.assertEqual(chatgpt_entry["recent_title"], "ChatGPT conv 2")
            self.assertIsNotNone(chatgpt_entry["recent_id"])

            claude_entry = summary.provider_recent[1]
            self.assertEqual(claude_entry["provider"], "claude")
            self.assertEqual(claude_entry["count"], 1)
            self.assertEqual(claude_entry["recent_title"], "Claude conv 0")

    def test_provider_recent_empty_when_no_imports(self):
        with self.app.app_context():
            summary = build_workspace_summary(trace_store_path=self._trace_path())
            self.assertEqual(summary.provider_recent, [])


if __name__ == "__main__":
    unittest.main()
