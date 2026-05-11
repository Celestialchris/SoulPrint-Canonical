"""Tests for GET /api/notes and GET /api/notes/<id> endpoints."""

from __future__ import annotations

import json
import unittest
from datetime import datetime

from src.app import create_app
from src.app.models import MemoryEntry
from src.app.models.db import db
from src.config import Config
from tests.temp_helpers import make_test_temp_dir, release_app_db_handles


def _seed_note(
    app,
    content: str = "Test note",
    tags: str | None = None,
    role: str = "user",
    timestamp: datetime | None = None,
) -> int:
    with app.app_context():
        entry = MemoryEntry(
            timestamp=timestamp or datetime(2024, 3, 1, 12, 0, 0),
            role=role,
            content=content,
            tags=tags,
        )
        db.session.add(entry)
        db.session.commit()
        return entry.id


class NotesApiTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = make_test_temp_dir(self, "notes-api")
        self.db_path = str(self.tmpdir / "test.db")
        self._old_uri = Config.SQLALCHEMY_DATABASE_URI
        Config.SQLALCHEMY_DATABASE_URI = f"sqlite:///{self.db_path}"
        self.app = create_app()
        self.client = self.app.test_client()
        self.addCleanup(release_app_db_handles, self.app, drop_all=True)
        self.addCleanup(self._restore_uri)

    def _restore_uri(self):
        Config.SQLALCHEMY_DATABASE_URI = self._old_uri

    def test_api_notes_returns_empty_list(self):
        resp = self.client.get("/api/notes")
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertEqual(data, [])

    def test_api_notes_returns_notes_newest_first(self):
        _seed_note(self.app, content="older note", timestamp=datetime(2024, 1, 1, 10, 0, 0))
        _seed_note(self.app, content="newer note", timestamp=datetime(2024, 6, 1, 10, 0, 0))
        resp = self.client.get("/api/notes")
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["content"], "newer note")
        self.assertEqual(data[1]["content"], "older note")

    def test_api_notes_serializes_tags_as_list(self):
        _seed_note(self.app, content="tagged note", tags="foo, bar")
        resp = self.client.get("/api/notes")
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertEqual(data[0]["tags"], ["foo", "bar"])

    def test_api_notes_tags_none_returns_empty_list(self):
        _seed_note(self.app, content="untagged note", tags=None)
        resp = self.client.get("/api/notes")
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertEqual(data[0]["tags"], [])

    def test_api_notes_detail_returns_note(self):
        note_id = _seed_note(self.app, content="detail note", tags="a, b")
        resp = self.client.get(f"/api/notes/{note_id}")
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertEqual(data["id"], note_id)
        self.assertEqual(data["content"], "detail note")
        self.assertEqual(data["tags"], ["a", "b"])
        self.assertIn("timestamp", data)
        self.assertIn("role", data)

    def test_api_notes_detail_not_found(self):
        resp = self.client.get("/api/notes/99999")
        self.assertEqual(resp.status_code, 404)
        data = json.loads(resp.data)
        self.assertEqual(data, {"error": "not found"})

    def test_api_notes_cors_header_present(self):
        resp = self.client.get("/api/notes")
        self.assertEqual(
            resp.headers.get("Access-Control-Allow-Origin"),
            "http://127.0.0.1:5173",
        )

    def test_api_notes_cors_not_on_other_routes(self):
        resp = self.client.get("/chats")
        self.assertIsNone(resp.headers.get("Access-Control-Allow-Origin"))

    def test_chats_page_has_listen_link(self):
        note_id = _seed_note(self.app, content="listen me")
        resp = self.client.get("/chats")
        self.assertEqual(resp.status_code, 200)
        body = resp.data.decode()
        self.assertIn(f"http://127.0.0.1:5173/?source=note&id={note_id}", body)

    def test_memory_detail_has_listen_link(self):
        note_id = _seed_note(self.app, content="detail listen")
        resp = self.client.get(f"/memory/{note_id}")
        self.assertEqual(resp.status_code, 200)
        body = resp.data.decode()
        self.assertIn(f"http://127.0.0.1:5173/?source=note&id={note_id}", body)
