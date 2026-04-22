"""Tests for tag normalization, auto-tag extraction, and tag routes."""

from __future__ import annotations

import unittest

from src.app import create_app
from src.app.models import ImportedConversation, ImportedMessage
from src.app.models.db import db
from src.app.tags import auto_tag_from_title, normalize_tag_string
from src.config import Config
from src.importers.contracts import NormalizedConversation, NormalizedMessage
from src.importers.persistence import persist_normalized_conversations
from tests.temp_helpers import make_test_temp_dir, release_app_db_handles


# ---------------------------------------------------------------------------
# Seed helpers
# ---------------------------------------------------------------------------

def _seed_conversation(
    app,
    title: str = "Test conversation",
    tags: str = "",
    source_id: str = "src-tags-001",
) -> int:
    """Insert one conversation + one message; return the conversation id."""
    with app.app_context():
        conv = ImportedConversation(
            source="chatgpt",
            source_conversation_id=source_id,
            title=title,
            created_at_unix=1710000000.0,
            updated_at_unix=1710001000.0,
            tags=tags,
        )
        db.session.add(conv)
        db.session.flush()
        db.session.add(
            ImportedMessage(
                conversation_id=conv.id,
                source_message_id="msg-1",
                role="user",
                content="Hello",
                sequence_index=0,
                created_at_unix=1710000100.0,
            )
        )
        db.session.commit()
        return conv.id


# ---------------------------------------------------------------------------
# Unit tests — no app context needed
# ---------------------------------------------------------------------------

class NormalizeTagStringTest(unittest.TestCase):
    def test_lowercase_and_dedup(self):
        self.assertEqual(normalize_tag_string("Novel, NOVEL, novel"), "novel")

    def test_internal_whitespace_collapse(self):
        self.assertEqual(normalize_tag_string("  My  Draft , notes"), "my draft, notes")

    def test_empty_input(self):
        self.assertEqual(normalize_tag_string(""), "")

    def test_empty_parts_dropped(self):
        self.assertEqual(normalize_tag_string("a, , , b"), "a, b")

    def test_truncation_at_64_chars(self):
        long_tag = "x" * 65
        result = normalize_tag_string(long_tag)
        self.assertEqual(len(result), 64)

    def test_unicode_preserved(self):
        result = normalize_tag_string("café, résumé")
        self.assertIn("café", result)
        self.assertIn("résumé", result)


class AutoTagFromTitleTest(unittest.TestCase):
    def test_skips_leading_stopwords(self):
        self.assertEqual(auto_tag_from_title("How do I bake carbonara?"), "bake")

    def test_skips_my(self):
        self.assertEqual(auto_tag_from_title("My novel draft revisions"), "novel")

    def test_no_leading_stopword(self):
        self.assertEqual(auto_tag_from_title("Soulprint issue"), "soulprint")

    def test_skips_the(self):
        self.assertEqual(auto_tag_from_title("The complete guide to X"), "complete")

    def test_empty_title(self):
        self.assertEqual(auto_tag_from_title(""), "")

    def test_single_stopword_returns_empty(self):
        self.assertEqual(auto_tag_from_title("Why"), "")

    def test_all_stopwords_returns_empty(self):
        self.assertEqual(auto_tag_from_title("why when where"), "")


# ---------------------------------------------------------------------------
# Schema tests — require app + DB
# ---------------------------------------------------------------------------

class ImportedConversationTagsColumnTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = make_test_temp_dir(self, "tags-column")
        self.db_path = str(self.tmpdir / "test.db")
        self._old_uri = Config.SQLALCHEMY_DATABASE_URI
        Config.SQLALCHEMY_DATABASE_URI = f"sqlite:///{self.db_path}"
        self.app = create_app()
        self.addCleanup(release_app_db_handles, self.app, drop_all=True)
        self.addCleanup(self._restore_uri)

    def _restore_uri(self):
        Config.SQLALCHEMY_DATABASE_URI = self._old_uri

    def test_tags_column_exists_and_saves(self):
        with self.app.app_context():
            conv = ImportedConversation(
                source="chatgpt",
                source_conversation_id="col-test-001",
                title="Column Test",
                created_at_unix=1710000000.0,
                updated_at_unix=1710001000.0,
                tags="novel, draft",
            )
            db.session.add(conv)
            db.session.commit()
            stored = ImportedConversation.query.get(conv.id)
        self.assertEqual(stored.tags, "novel, draft")

    def test_tags_default_is_empty_string(self):
        with self.app.app_context():
            conv = ImportedConversation(
                source="chatgpt",
                source_conversation_id="col-test-002",
                title="No Tags",
                created_at_unix=1710000000.0,
                updated_at_unix=1710001000.0,
            )
            db.session.add(conv)
            db.session.commit()
            stored = ImportedConversation.query.get(conv.id)
        self.assertEqual(stored.tags, "")
        self.assertIsNotNone(stored.tags)


# ---------------------------------------------------------------------------
# Add tag route tests
# ---------------------------------------------------------------------------

class AddTagRouteTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = make_test_temp_dir(self, "add-tag-route")
        self.db_path = str(self.tmpdir / "test.db")
        self._old_uri = Config.SQLALCHEMY_DATABASE_URI
        Config.SQLALCHEMY_DATABASE_URI = f"sqlite:///{self.db_path}"
        self.app = create_app()
        self.client = self.app.test_client()
        self.conv_id = _seed_conversation(self.app, title="Empty Tags Conv", source_id="src-add-001")
        self.addCleanup(release_app_db_handles, self.app, drop_all=True)
        self.addCleanup(self._restore_uri)

    def _restore_uri(self):
        Config.SQLALCHEMY_DATABASE_URI = self._old_uri

    def test_adds_new_tag(self):
        self.client.post(f"/imported/{self.conv_id}/tags/add", data={"tag": "novel"})
        with self.app.app_context():
            conv = ImportedConversation.query.get(self.conv_id)
        self.assertEqual(conv.tags, "novel")

    def test_adds_to_existing_tags(self):
        self.client.post(f"/imported/{self.conv_id}/tags/add", data={"tag": "novel"})
        self.client.post(f"/imported/{self.conv_id}/tags/add", data={"tag": "draft"})
        with self.app.app_context():
            conv = ImportedConversation.query.get(self.conv_id)
        self.assertIn("novel", conv.tags)
        self.assertIn("draft", conv.tags)

    def test_deduplicates_existing_tag(self):
        self.client.post(f"/imported/{self.conv_id}/tags/add", data={"tag": "novel"})
        self.client.post(f"/imported/{self.conv_id}/tags/add", data={"tag": "novel"})
        with self.app.app_context():
            conv = ImportedConversation.query.get(self.conv_id)
        parts = [t.strip() for t in conv.tags.split(",") if t.strip()]
        self.assertEqual(parts.count("novel"), 1)

    def test_empty_tag_is_noop(self):
        self.client.post(f"/imported/{self.conv_id}/tags/add", data={"tag": ""})
        with self.app.app_context():
            conv = ImportedConversation.query.get(self.conv_id)
        self.assertEqual(conv.tags, "")

    def test_whitespace_only_tag_is_noop(self):
        self.client.post(f"/imported/{self.conv_id}/tags/add", data={"tag": "   "})
        with self.app.app_context():
            conv = ImportedConversation.query.get(self.conv_id)
        self.assertEqual(conv.tags, "")

    def test_normalizes_incoming_tag(self):
        self.client.post(f"/imported/{self.conv_id}/tags/add", data={"tag": "NOVEL"})
        with self.app.app_context():
            conv = ImportedConversation.query.get(self.conv_id)
        self.assertEqual(conv.tags, "novel")

    def test_redirects_to_next_when_valid(self):
        resp = self.client.post(
            f"/imported/{self.conv_id}/tags/add",
            data={"tag": "test", "next": "/imported?q=hello"},
        )
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/imported", resp.headers.get("Location", ""))

    def test_sanitizer_rejects_external_url(self):
        resp = self.client.post(
            f"/imported/{self.conv_id}/tags/add",
            data={"tag": "test", "next": "https://evil.com/x"},
        )
        location = resp.headers.get("Location", "")
        self.assertFalse(location.startswith("https://evil"))

    def test_sanitizer_strips_backslash_next(self):
        # \\evil.com after replace("\\", "") becomes evil.com (relative path, not open redirect)
        resp = self.client.post(
            f"/imported/{self.conv_id}/tags/add",
            data={"tag": "test", "next": "\\\\evil.com"},
        )
        self.assertEqual(resp.status_code, 302)
        location = resp.headers.get("Location", "")
        self.assertFalse(location.startswith("//"))
        self.assertFalse(location.startswith("http://"))
        self.assertFalse(location.startswith("https://"))


# ---------------------------------------------------------------------------
# Remove tag route tests
# ---------------------------------------------------------------------------

class RemoveTagRouteTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = make_test_temp_dir(self, "remove-tag-route")
        self.db_path = str(self.tmpdir / "test.db")
        self._old_uri = Config.SQLALCHEMY_DATABASE_URI
        Config.SQLALCHEMY_DATABASE_URI = f"sqlite:///{self.db_path}"
        self.app = create_app()
        self.client = self.app.test_client()
        self.conv_id = _seed_conversation(
            self.app, title="Tagged Conv", tags="novel, draft", source_id="src-remove-001"
        )
        self.addCleanup(release_app_db_handles, self.app, drop_all=True)
        self.addCleanup(self._restore_uri)

    def _restore_uri(self):
        Config.SQLALCHEMY_DATABASE_URI = self._old_uri

    def test_removes_existing_tag(self):
        self.client.post(f"/imported/{self.conv_id}/tags/remove/novel")
        with self.app.app_context():
            conv = ImportedConversation.query.get(self.conv_id)
        self.assertNotIn("novel", conv.tags)
        self.assertIn("draft", conv.tags)

    def test_missing_tag_is_noop(self):
        self.client.post(f"/imported/{self.conv_id}/tags/remove/nonexistent")
        with self.app.app_context():
            conv = ImportedConversation.query.get(self.conv_id)
        self.assertIn("novel", conv.tags)
        self.assertIn("draft", conv.tags)

    def test_case_insensitive_match(self):
        self.client.post(f"/imported/{self.conv_id}/tags/remove/NOVEL")
        with self.app.app_context():
            conv = ImportedConversation.query.get(self.conv_id)
        self.assertNotIn("novel", conv.tags)

    def test_preserves_other_tags(self):
        self.client.post(f"/imported/{self.conv_id}/tags/remove/novel")
        with self.app.app_context():
            conv = ImportedConversation.query.get(self.conv_id)
        self.assertIn("draft", conv.tags)

    def test_sanitizer_rejects_bad_next(self):
        resp = self.client.post(
            f"/imported/{self.conv_id}/tags/remove/novel",
            data={"next": "http://evil.com"},
        )
        location = resp.headers.get("Location", "")
        self.assertFalse(location.startswith("http://evil"))


# ---------------------------------------------------------------------------
# Auto-tag on import tests
# ---------------------------------------------------------------------------

class AutoTagOnImportTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = make_test_temp_dir(self, "auto-tag-import")
        self.db_path = str(self.tmpdir / "test.db")
        self._old_uri = Config.SQLALCHEMY_DATABASE_URI
        Config.SQLALCHEMY_DATABASE_URI = f"sqlite:///{self.db_path}"
        self.app = create_app()
        self.addCleanup(release_app_db_handles, self.app, drop_all=True)
        self.addCleanup(self._restore_uri)

    def _restore_uri(self):
        Config.SQLALCHEMY_DATABASE_URI = self._old_uri

    def _make_conversation(self, title: str, source_id: str) -> NormalizedConversation:
        return NormalizedConversation(
            source_provider="chatgpt",
            source_conversation_id=source_id,
            title=title,
            created_at=1710000000.0,
            updated_at=1710001000.0,
            messages=[
                NormalizedMessage(
                    source_message_id="msg-1",
                    role="user",
                    content="Hello",
                    sequence_index=0,
                    created_at=1710000100.0,
                )
            ],
        )

    def test_auto_tag_set_from_title(self):
        conv = self._make_conversation("My novel draft", "auto-001")
        with self.app.app_context():
            persist_normalized_conversations([conv])
            stored = ImportedConversation.query.filter_by(
                source_conversation_id="auto-001"
            ).one()
        self.assertEqual(stored.tags, "novel")

    def test_empty_title_yields_empty_tags(self):
        conv = self._make_conversation("", "auto-002")
        with self.app.app_context():
            persist_normalized_conversations([conv])
            stored = ImportedConversation.query.filter_by(
                source_conversation_id="auto-002"
            ).one()
        self.assertEqual(stored.tags, "")

    def test_all_stopword_title_yields_empty_tags(self):
        conv = self._make_conversation("How do I", "auto-003")
        with self.app.app_context():
            persist_normalized_conversations([conv])
            stored = ImportedConversation.query.filter_by(
                source_conversation_id="auto-003"
            ).one()
        self.assertEqual(stored.tags, "")


# ---------------------------------------------------------------------------
# Rendering tests
# ---------------------------------------------------------------------------

class TagChipRenderingTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = make_test_temp_dir(self, "tag-render")
        self.db_path = str(self.tmpdir / "test.db")
        self._old_uri = Config.SQLALCHEMY_DATABASE_URI
        Config.SQLALCHEMY_DATABASE_URI = f"sqlite:///{self.db_path}"
        self.app = create_app()
        self.client = self.app.test_client()
        self.addCleanup(release_app_db_handles, self.app, drop_all=True)
        self.addCleanup(self._restore_uri)

    def _restore_uri(self):
        Config.SQLALCHEMY_DATABASE_URI = self._old_uri

    def test_chips_render_for_tagged_conversation(self):
        _seed_conversation(
            self.app, title="Tagged", tags="novel, draft", source_id="render-001"
        )
        resp = self.client.get("/imported")
        html = resp.data.decode()
        self.assertIn("tag-chip", html)
        self.assertIn("novel", html)
        self.assertIn("draft", html)

    def test_add_input_renders_when_no_tags(self):
        _seed_conversation(self.app, title="No tags", tags="", source_id="render-002")
        resp = self.client.get("/imported")
        html = resp.data.decode()
        self.assertIn("tag-chip-add__input", html)
        self.assertNotIn("tag-chip__remove", html)
