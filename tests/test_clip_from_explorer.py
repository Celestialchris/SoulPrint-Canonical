"""Tests for clip-to-notes from the transcript explorer."""

from __future__ import annotations

import json
import unittest

from src.app import create_app
from src.app.models import ImportedConversation, ImportedMessage, MemoryEntry
from src.app.models.db import db
from src.config import Config
from tests.temp_helpers import make_test_temp_dir, release_app_db_handles


class ClipFromExplorerTest(unittest.TestCase):
    def setUp(self):
        self.workdir = make_test_temp_dir(self, "clip-explorer")
        self._old_uri = Config.SQLALCHEMY_DATABASE_URI
        self.addCleanup(self._restore_sqlite_uri)
        sqlite_path = self.workdir / "clip_test.db"
        Config.SQLALCHEMY_DATABASE_URI = f"sqlite:///{sqlite_path}"

        self.app = create_app()
        self.client = self.app.test_client()
        self.addCleanup(release_app_db_handles, self.app, drop_all=True)

    def _restore_sqlite_uri(self):
        Config.SQLALCHEMY_DATABASE_URI = self._old_uri

    def _create_conversation(self) -> int:
        with self.app.app_context():
            conversation = ImportedConversation(
                source="chatgpt",
                source_conversation_id="conv-clip-1",
                title="Strategic direction assessment",
                created_at_unix=1710000000.0,
                updated_at_unix=1710000500.0,
            )
            db.session.add(conversation)
            db.session.flush()

            db.session.add(
                ImportedMessage(
                    conversation_id=conversation.id,
                    source_message_id="msg-0",
                    role="assistant",
                    content="The key insight is that local-first wins.",
                    sequence_index=0,
                    created_at_unix=1710000001.0,
                )
            )
            db.session.commit()
            return conversation.id

    def _clip(self, payload: dict) -> tuple:
        response = self.client.post(
            "/api/clip",
            data=json.dumps(payload),
            content_type="application/json",
        )
        return response, response.get_json()

    # 1. POST /api/clip with valid payload creates a MemoryEntry
    def test_clip_creates_memory_entry(self):
        conv_id = self._create_conversation()
        response, data = self._clip({
            "content": "local-first wins",
            "source_conversation_id": conv_id,
            "source_conversation_title": "Strategic direction assessment",
            "source_provider": "chatgpt",
            "source_message_index": 0,
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["status"], "ok")
        self.assertIn("note_id", data)

        with self.app.app_context():
            entry = MemoryEntry.query.get(data["note_id"])
            self.assertIsNotNone(entry)

    # 2. The created note content contains the selected text
    def test_clip_content_contains_selected_text(self):
        conv_id = self._create_conversation()
        _, data = self._clip({
            "content": "local-first wins",
            "source_conversation_id": conv_id,
            "source_conversation_title": "Strategic direction assessment",
            "source_provider": "chatgpt",
            "source_message_index": 0,
        })

        with self.app.app_context():
            entry = MemoryEntry.query.get(data["note_id"])
            self.assertIn("local-first wins", entry.content)

    # 3. The created note content contains the citation with conversation title
    def test_clip_content_contains_citation(self):
        conv_id = self._create_conversation()
        _, data = self._clip({
            "content": "local-first wins",
            "source_conversation_id": conv_id,
            "source_conversation_title": "Strategic direction assessment",
            "source_provider": "chatgpt",
            "source_message_index": 0,
        })

        with self.app.app_context():
            entry = MemoryEntry.query.get(data["note_id"])
            self.assertIn("Strategic direction assessment", entry.content)
            self.assertIn("chatgpt", entry.content)

    # 4. The created note content contains the source link
    def test_clip_content_contains_source_link(self):
        conv_id = self._create_conversation()
        _, data = self._clip({
            "content": "local-first wins",
            "source_conversation_id": conv_id,
            "source_conversation_title": "Strategic direction assessment",
            "source_provider": "chatgpt",
            "source_message_index": 0,
        })

        with self.app.app_context():
            entry = MemoryEntry.query.get(data["note_id"])
            self.assertIn(f"/imported/{conv_id}/explorer#msg-0", entry.content)

    # 5. POST /api/clip with missing content returns 400
    def test_clip_missing_content_returns_400(self):
        conv_id = self._create_conversation()
        response, data = self._clip({
            "content": "",
            "source_conversation_id": conv_id,
        })

        self.assertEqual(response.status_code, 400)
        self.assertEqual(data["status"], "error")

    # 6. POST /api/clip with missing conversation_id returns 400
    def test_clip_missing_conversation_id_returns_400(self):
        self._create_conversation()
        response, data = self._clip({
            "content": "some text",
        })

        self.assertEqual(response.status_code, 400)
        self.assertEqual(data["status"], "error")

    # 7. The note is tagged "clipped"
    def test_clip_auto_tags_clipped(self):
        conv_id = self._create_conversation()
        _, data = self._clip({
            "content": "local-first wins",
            "source_conversation_id": conv_id,
            "source_conversation_title": "Strategic direction assessment",
            "source_provider": "chatgpt",
            "source_message_index": 0,
        })

        with self.app.app_context():
            entry = MemoryEntry.query.get(data["note_id"])
            self.assertEqual(entry.tags, "clipped")

    # 8. GET /chats shows the clipped note
    def test_clipped_note_visible_on_chats(self):
        conv_id = self._create_conversation()
        self._clip({
            "content": "local-first wins",
            "source_conversation_id": conv_id,
            "source_conversation_title": "Strategic direction assessment",
            "source_provider": "chatgpt",
            "source_message_index": 0,
        })

        response = self.client.get("/chats")
        html = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("local-first wins", html)

    # 9. The source link in the note resolves (the explorer route exists)
    def test_source_link_resolves(self):
        conv_id = self._create_conversation()
        response = self.client.get(f"/imported/{conv_id}/explorer")
        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
