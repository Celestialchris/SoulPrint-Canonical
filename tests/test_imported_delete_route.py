"""Tests for the /imported/<conv_id>/delete cascade-delete route and memory FTS cleanup."""

from __future__ import annotations

import json
import sqlite3
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from src.app import create_app
from src.app.models import ImportedConversation, ImportedMessage, MemoryEntry
from src.app.models.db import db
from src.config import Config
from src.retrieval.fts import ensure_fts_tables, index_new_messages, index_new_note, rebuild_fts
from tests.temp_helpers import make_test_temp_dir, release_app_db_handles


def _seed_conversation(app, source: str = "chatgpt", title: str = "Test conv") -> int:
    """Insert a conversation + 2 messages; return the conversation id."""
    with app.app_context():
        conv = ImportedConversation(
            source=source,
            source_conversation_id="src-001",
            title=title,
            created_at_unix=1710000000.0,
            updated_at_unix=1710001000.0,
        )
        db.session.add(conv)
        db.session.flush()
        db.session.add(ImportedMessage(
            conversation_id=conv.id,
            source_message_id="msg-1",
            role="user",
            content="Hello world",
            sequence_index=0,
            created_at_unix=1710000100.0,
        ))
        db.session.add(ImportedMessage(
            conversation_id=conv.id,
            source_message_id="msg-2",
            role="assistant",
            content="Hi there",
            sequence_index=1,
            created_at_unix=1710000200.0,
        ))
        db.session.commit()
        return conv.id


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            cleaned = line.strip()
            if cleaned:
                rows.append(json.loads(cleaned))
    return rows


class ImportedDeleteConfirmTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = make_test_temp_dir(self, "del-confirm")
        self.db_path = str(self.tmpdir / "test.db")
        self._old_uri = Config.SQLALCHEMY_DATABASE_URI
        Config.SQLALCHEMY_DATABASE_URI = f"sqlite:///{self.db_path}"
        self.app = create_app()
        self.client = self.app.test_client()
        self.conv_id = _seed_conversation(self.app, title="My Test Conversation")
        self.addCleanup(release_app_db_handles, self.app, drop_all=True)
        self.addCleanup(self._restore_uri)

    def _restore_uri(self):
        Config.SQLALCHEMY_DATABASE_URI = self._old_uri

    def test_get_shows_confirm_page(self):
        resp = self.client.get(f"/imported/{self.conv_id}/delete")
        self.assertEqual(resp.status_code, 200)
        html = resp.get_data(as_text=True)
        self.assertIn("My Test Conversation", html)
        self.assertIn("Delete conversation", html)
        self.assertIn(f"imported_conversation:{self.conv_id}", html)

    def test_get_404_unknown_id(self):
        resp = self.client.get("/imported/999999/delete")
        self.assertEqual(resp.status_code, 404)

    def test_get_shows_zero_counts_when_no_artifacts(self):
        resp = self.client.get(f"/imported/{self.conv_id}/delete")
        html = resp.get_data(as_text=True)
        self.assertIn("Summaries", html)
        self.assertIn("Topic scans", html)


class ImportedDeleteCascadeTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = make_test_temp_dir(self, "del-cascade")
        self.db_path = str(self.tmpdir / "test.db")
        self._old_uri = Config.SQLALCHEMY_DATABASE_URI
        Config.SQLALCHEMY_DATABASE_URI = f"sqlite:///{self.db_path}"
        self.app = create_app()
        self.client = self.app.test_client()
        self.conv_id = _seed_conversation(self.app, title="Cascade conv")
        self.stable_id = f"imported_conversation:{self.conv_id}"

        # Seed JSONL artifacts referencing this conversation
        db_dir = Path(self.db_path).parent
        _write_jsonl(db_dir / "derived_summaries.jsonl", [
            {"summary_id": "s1", "source_conversation_stable_id": self.stable_id},
        ])
        _write_jsonl(db_dir / "topic_scans.jsonl", [
            {"scan_id": "ts1", "clusters": [{"conversation_stable_ids": [self.stable_id]}]},
        ])
        _write_jsonl(db_dir / "derived_digests.jsonl", [
            {"digest_id": "dg1", "source_conversation_stable_ids": [self.stable_id]},
        ])
        _write_jsonl(db_dir / "derived_distillations.jsonl", [
            {"distillation_id": "dt1", "source_conversation_stable_ids": [self.stable_id]},
        ])
        _write_jsonl(db_dir / "continuity_artifacts.jsonl", [
            {"artifact_id": "a1", "artifact_type": "summary", "source_conversation_ids": [self.stable_id]},
        ])

        self.addCleanup(release_app_db_handles, self.app, drop_all=True)
        self.addCleanup(self._restore_uri)

    def _restore_uri(self):
        Config.SQLALCHEMY_DATABASE_URI = self._old_uri

    def test_post_redirects_to_imported(self):
        resp = self.client.post(f"/imported/{self.conv_id}/delete")
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/imported", resp.headers["Location"])

    def test_post_removes_conversation_from_db(self):
        self.client.post(f"/imported/{self.conv_id}/delete")
        with self.app.app_context():
            conv = ImportedConversation.query.get(self.conv_id)
        self.assertIsNone(conv)

    def test_post_removes_messages_via_cascade(self):
        self.client.post(f"/imported/{self.conv_id}/delete")
        with self.app.app_context():
            msgs = ImportedMessage.query.filter_by(conversation_id=self.conv_id).all()
        self.assertEqual(msgs, [])

    def test_post_cleans_jsonl_artifacts(self):
        self.client.post(f"/imported/{self.conv_id}/delete")
        db_dir = Path(self.db_path).parent
        self.assertEqual(_read_jsonl(db_dir / "derived_summaries.jsonl"), [])
        self.assertEqual(_read_jsonl(db_dir / "topic_scans.jsonl"), [])
        self.assertEqual(_read_jsonl(db_dir / "derived_digests.jsonl"), [])
        self.assertEqual(_read_jsonl(db_dir / "derived_distillations.jsonl"), [])
        self.assertEqual(_read_jsonl(db_dir / "continuity_artifacts.jsonl"), [])

    def test_flash_message_set_in_session(self):
        with self.client.session_transaction() as sess:
            sess.clear()
        self.client.post(f"/imported/{self.conv_id}/delete")
        # Follow redirect to consume session flash
        resp = self.client.get("/imported")
        html = resp.get_data(as_text=True)
        self.assertIn("Deleted conversation", html)


class ImportedDeleteEmptyCascadeTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = make_test_temp_dir(self, "del-empty")
        self.db_path = str(self.tmpdir / "test.db")
        self._old_uri = Config.SQLALCHEMY_DATABASE_URI
        Config.SQLALCHEMY_DATABASE_URI = f"sqlite:///{self.db_path}"
        self.app = create_app()
        self.client = self.app.test_client()
        self.conv_id = _seed_conversation(self.app, title="Empty cascade conv")
        self.addCleanup(release_app_db_handles, self.app, drop_all=True)
        self.addCleanup(self._restore_uri)

    def _restore_uri(self):
        Config.SQLALCHEMY_DATABASE_URI = self._old_uri

    def test_post_deletes_conversation_with_no_artifacts(self):
        resp = self.client.post(f"/imported/{self.conv_id}/delete")
        self.assertEqual(resp.status_code, 302)
        with self.app.app_context():
            conv = ImportedConversation.query.get(self.conv_id)
        self.assertIsNone(conv)


class ImportedDeleteFtsSurvivalTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = make_test_temp_dir(self, "del-fts-survival")
        self.db_path = str(self.tmpdir / "test.db")
        self._old_uri = Config.SQLALCHEMY_DATABASE_URI
        Config.SQLALCHEMY_DATABASE_URI = f"sqlite:///{self.db_path}"
        self.app = create_app()
        self.client = self.app.test_client()
        self.conv_id = _seed_conversation(self.app, title="FTS crash conv")
        self.addCleanup(release_app_db_handles, self.app, drop_all=True)
        self.addCleanup(self._restore_uri)

    def _restore_uri(self):
        Config.SQLALCHEMY_DATABASE_URI = self._old_uri

    def test_fts_failure_does_not_block_cascade(self):
        with patch("src.retrieval.fts.remove_conversation_from_fts", side_effect=RuntimeError("fts boom")):
            resp = self.client.post(f"/imported/{self.conv_id}/delete")
        self.assertEqual(resp.status_code, 302)
        with self.app.app_context():
            conv = ImportedConversation.query.get(self.conv_id)
        self.assertIsNone(conv)

    def test_fts_failure_still_sets_flash(self):
        with patch("src.retrieval.fts.remove_conversation_from_fts", side_effect=RuntimeError("fts boom")):
            self.client.post(f"/imported/{self.conv_id}/delete")
        resp = self.client.get("/imported")
        html = resp.get_data(as_text=True)
        self.assertIn("Deleted conversation", html)


class MemoryDeleteFtsCleanupTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = make_test_temp_dir(self, "mem-fts-cleanup")
        self.db_path = str(self.tmpdir / "test.db")
        self._old_uri = Config.SQLALCHEMY_DATABASE_URI
        Config.SQLALCHEMY_DATABASE_URI = f"sqlite:///{self.db_path}"
        self.app = create_app()
        self.client = self.app.test_client()
        with self.app.app_context():
            note = MemoryEntry(
                timestamp=datetime(2024, 3, 10, tzinfo=timezone.utc),
                role="user",
                content="Test note for FTS cleanup",
                tags="test",
            )
            db.session.add(note)
            db.session.commit()
            self.note_id = note.id
        ensure_fts_tables(self.db_path)
        index_new_note(self.db_path, self.note_id)
        self.addCleanup(release_app_db_handles, self.app, drop_all=True)
        self.addCleanup(self._restore_uri)

    def _restore_uri(self):
        Config.SQLALCHEMY_DATABASE_URI = self._old_uri

    def _count_fts_note(self, note_id: int) -> int:
        conn = sqlite3.connect(self.db_path)
        try:
            row = conn.execute(
                "SELECT COUNT(*) FROM fts_notes WHERE note_id = ?", (str(note_id),)
            ).fetchone()
            return row[0]
        finally:
            conn.close()

    def test_memory_delete_removes_fts_row(self):
        self.assertEqual(self._count_fts_note(self.note_id), 1)
        resp = self.client.post(f"/memory/{self.note_id}/delete")
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(self._count_fts_note(self.note_id), 0)

    def test_memory_delete_still_redirects_on_fts_failure(self):
        with patch("src.retrieval.fts.remove_note_from_fts", side_effect=RuntimeError("fts boom")):
            resp = self.client.post(f"/memory/{self.note_id}/delete")
        self.assertEqual(resp.status_code, 302)
        with self.app.app_context():
            entry = MemoryEntry.query.get(self.note_id)
        self.assertIsNone(entry)


class ImportedDeleteFtsRowsTest(unittest.TestCase):
    """Verify that FTS rows for a deleted conversation are actually removed."""

    def setUp(self):
        self.tmpdir = make_test_temp_dir(self, "del-fts-rows")
        self.db_path = str(self.tmpdir / "test.db")
        self._old_uri = Config.SQLALCHEMY_DATABASE_URI
        Config.SQLALCHEMY_DATABASE_URI = f"sqlite:///{self.db_path}"
        self.app = create_app()
        self.client = self.app.test_client()
        self.conv_id = _seed_conversation(self.app, title="FTS rows conv")
        ensure_fts_tables(self.db_path)
        index_new_messages(self.db_path, self.conv_id)
        self.addCleanup(release_app_db_handles, self.app, drop_all=True)
        self.addCleanup(self._restore_uri)

    def _restore_uri(self):
        Config.SQLALCHEMY_DATABASE_URI = self._old_uri

    def _count_fts_messages_for_conv(self, conv_id: int) -> int:
        conn = sqlite3.connect(self.db_path)
        try:
            row = conn.execute(
                "SELECT COUNT(*) FROM fts_messages WHERE conversation_id = ?",
                (str(conv_id),),
            ).fetchone()
            return row[0]
        finally:
            conn.close()

    def test_fts_rows_present_before_delete(self):
        count = self._count_fts_messages_for_conv(self.conv_id)
        self.assertEqual(count, 2)  # seeded 2 messages

    def test_post_delete_removes_fts_rows(self):
        self.assertEqual(self._count_fts_messages_for_conv(self.conv_id), 2)
        self.client.post(f"/imported/{self.conv_id}/delete")
        self.assertEqual(self._count_fts_messages_for_conv(self.conv_id), 0)


if __name__ == "__main__":
    unittest.main()
