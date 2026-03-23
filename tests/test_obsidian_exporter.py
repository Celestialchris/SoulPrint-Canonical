"""Integration tests for the Obsidian Bridge exporter."""

import json
import unittest
from pathlib import Path

from flask import Flask

from src.app.models import ImportedConversation, ImportedMessage
from src.app.models.db import db
from src.obsidian.exporter import (
    ExportResult,
    RefreshResult,
    _update_auto_block,
    export_vault,
    refresh_vault,
)
from src.obsidian.renderer import AUTO_BEGIN, AUTO_END
from tests.temp_helpers import make_test_temp_dir


def _seed_db(sqlite_path: Path) -> None:
    """Seed a test database with 2 conversations across 2 providers."""
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{sqlite_path}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    with app.app_context():
        try:
            db.create_all()

            conv1 = ImportedConversation(
                source="chatgpt",
                source_conversation_id="conv-1",
                title="Retrieval architecture",
                created_at_unix=1742673000.0,
                updated_at_unix=1742673000.0,
            )
            db.session.add(conv1)
            db.session.flush()

            db.session.add(
                ImportedMessage(
                    conversation_id=conv1.id,
                    source_message_id="msg-1",
                    role="user",
                    content="How should retrieval work?",
                    sequence_index=0,
                    created_at_unix=1742673000.0,
                )
            )
            db.session.add(
                ImportedMessage(
                    conversation_id=conv1.id,
                    source_message_id="msg-2",
                    role="assistant",
                    content="Lane-aware approach recommended.",
                    sequence_index=1,
                    created_at_unix=1742673060.0,
                )
            )

            conv2 = ImportedConversation(
                source="claude",
                source_conversation_id="conv-2",
                title="Memory continuity design",
                created_at_unix=1742759400.0,
                updated_at_unix=1742759400.0,
            )
            db.session.add(conv2)
            db.session.flush()

            db.session.add(
                ImportedMessage(
                    conversation_id=conv2.id,
                    source_message_id="msg-3",
                    role="user",
                    content="How does continuity work?",
                    sequence_index=0,
                    created_at_unix=1742759400.0,
                )
            )

            db.session.commit()
        finally:
            db.session.remove()
            db.engine.dispose()


def _seed_topic_scan(db_dir: Path) -> None:
    """Write a topic scan JSONL beside the DB."""
    scan = {
        "scan_id": "topic_scan:test-001",
        "generation_timestamp": "2026-03-22T12:00:00Z",
        "llm_provider_used": "keyword_fallback",
        "clusters": [
            {
                "topic_label": "Retrieval Architecture",
                "conversation_stable_ids": [
                    "imported_conversation:1",
                ],
                "conversation_titles": ["Retrieval architecture"],
                "confidence": "high",
            }
        ],
        "conversation_count": 2,
        "derived_from": "canonical_imported_conversations",
        "artifact_kind": "topic_scan_v1",
    }
    path = db_dir / "topic_scans.jsonl"
    path.write_text(json.dumps(scan) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# _update_auto_block unit tests
# ---------------------------------------------------------------------------


class UpdateAutoBlockTest(unittest.TestCase):
    def test_replaces_content_between_markers(self):
        existing = (
            "Header\n"
            f"{AUTO_BEGIN}\nold content\n{AUTO_END}\n"
            "Footer\n"
        )
        result = _update_auto_block(existing, "\nnew content\n")
        self.assertIn("new content", result)
        self.assertNotIn("old content", result)
        self.assertIn("Header", result)
        self.assertIn("Footer", result)

    def test_returns_none_without_markers(self):
        self.assertIsNone(_update_auto_block("no markers here", "\ncontent\n"))

    def test_preserves_text_outside_markers(self):
        existing = (
            "User annotation above\n"
            f"{AUTO_BEGIN}\nstuff\n{AUTO_END}\n"
            "User annotation below\n"
        )
        result = _update_auto_block(existing, "\nfresh\n")
        self.assertIn("User annotation above", result)
        self.assertIn("User annotation below", result)


# ---------------------------------------------------------------------------
# Export tests
# ---------------------------------------------------------------------------


class ExportVaultTest(unittest.TestCase):
    def setUp(self):
        self.workdir = make_test_temp_dir(self, "obsidian-export")
        self.sqlite_path = self.workdir / "test.db"
        self.vault_path = self.workdir / "vault"

    def test_full_export_creates_directory_structure(self):
        _seed_db(self.sqlite_path)
        export_vault(self.sqlite_path, self.vault_path)

        for subdir in ("Chats", "Themes", "Daily", "References", "Templates"):
            self.assertTrue(
                (self.vault_path / subdir).is_dir(), f"{subdir}/ not created"
            )
        self.assertTrue((self.vault_path / ".obsidian").is_dir())

    def test_chat_files_exist_with_correct_names(self):
        _seed_db(self.sqlite_path)
        export_vault(self.sqlite_path, self.vault_path)

        chat1 = self.vault_path / "Chats" / "chatgpt--1.md"
        chat2 = self.vault_path / "Chats" / "claude--2.md"
        self.assertTrue(chat1.exists(), "chatgpt--1.md not created")
        self.assertTrue(chat2.exists(), "claude--2.md not created")

    def test_chat_notes_contain_auto_markers(self):
        _seed_db(self.sqlite_path)
        export_vault(self.sqlite_path, self.vault_path)

        content = (self.vault_path / "Chats" / "chatgpt--1.md").read_text(
            encoding="utf-8"
        )
        self.assertIn(AUTO_BEGIN, content)
        self.assertIn(AUTO_END, content)

    def test_theme_notes_created_with_topic_scan(self):
        _seed_db(self.sqlite_path)
        _seed_topic_scan(self.sqlite_path.parent)
        result = export_vault(self.sqlite_path, self.vault_path)

        self.assertGreater(result.theme_count, 0)
        theme_file = self.vault_path / "Themes" / "retrieval-architecture.md"
        self.assertTrue(theme_file.exists())

    def test_daily_notes_created_for_unique_dates(self):
        _seed_db(self.sqlite_path)
        result = export_vault(self.sqlite_path, self.vault_path)

        self.assertGreater(result.daily_count, 0)
        daily_dir = self.vault_path / "Daily"
        md_files = list(daily_dir.glob("*.md"))
        self.assertGreater(len(md_files), 0)

    def test_provider_notes_created(self):
        _seed_db(self.sqlite_path)
        export_vault(self.sqlite_path, self.vault_path)

        self.assertTrue(
            (self.vault_path / "References" / "ChatGPT.md").exists()
        )
        self.assertTrue(
            (self.vault_path / "References" / "Claude.md").exists()
        )

    def test_category_notes_created(self):
        _seed_db(self.sqlite_path)
        export_vault(self.sqlite_path, self.vault_path)

        self.assertTrue((self.vault_path / "Chat.md").exists())
        self.assertTrue((self.vault_path / "Theme.md").exists())

    def test_incremental_skips_existing_files(self):
        _seed_db(self.sqlite_path)
        export_vault(self.sqlite_path, self.vault_path)

        # Add user annotation to a chat note
        chat_path = self.vault_path / "Chats" / "chatgpt--1.md"
        original = chat_path.read_text(encoding="utf-8")
        chat_path.write_text(original + "\n## My Notes\nPersonal note\n", encoding="utf-8")

        # Re-export with incremental
        result = export_vault(
            self.sqlite_path, self.vault_path, incremental=True
        )
        self.assertGreater(result.skipped, 0)

        # User annotation survives
        updated = chat_path.read_text(encoding="utf-8")
        self.assertIn("Personal note", updated)

    def test_dry_run_creates_no_files(self):
        _seed_db(self.sqlite_path)
        result = export_vault(self.sqlite_path, self.vault_path, dry_run=True)

        self.assertGreater(result.chat_count, 0)
        # Vault root should not exist or be empty
        chats_dir = self.vault_path / "Chats"
        if chats_dir.exists():
            self.assertEqual(list(chats_dir.glob("*.md")), [])

    def test_obsidian_config_created_first_time(self):
        _seed_db(self.sqlite_path)
        export_vault(self.sqlite_path, self.vault_path)

        app_json = self.vault_path / ".obsidian" / "app.json"
        self.assertTrue(app_json.exists())
        config = json.loads(app_json.read_text(encoding="utf-8"))
        self.assertEqual(config["attachmentFolderPath"], "Attachments")

    def test_obsidian_config_not_overwritten(self):
        _seed_db(self.sqlite_path)
        export_vault(self.sqlite_path, self.vault_path)

        # Modify config
        app_json = self.vault_path / ".obsidian" / "app.json"
        app_json.write_text('{"custom": true}\n', encoding="utf-8")

        # Re-export
        export_vault(self.sqlite_path, self.vault_path)

        # Custom config survives
        config = json.loads(app_json.read_text(encoding="utf-8"))
        self.assertTrue(config.get("custom"))

    def test_empty_db_produces_config_only(self):
        # Create empty DB
        app = Flask(__name__)
        app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{self.sqlite_path}"
        app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        db.init_app(app)
        with app.app_context():
            try:
                db.create_all()
            finally:
                db.session.remove()
                db.engine.dispose()

        result = export_vault(self.sqlite_path, self.vault_path)

        self.assertEqual(result.chat_count, 0)
        self.assertTrue((self.vault_path / ".obsidian").is_dir())

    def test_export_result_counts_accurate(self):
        _seed_db(self.sqlite_path)
        result = export_vault(self.sqlite_path, self.vault_path)

        self.assertIsInstance(result, ExportResult)
        self.assertEqual(result.chat_count, 2)
        self.assertEqual(result.provider_count, 2)
        self.assertGreaterEqual(result.daily_count, 1)
        self.assertEqual(result.skipped, 0)
        self.assertEqual(result.errors, [])


# ---------------------------------------------------------------------------
# Refresh tests
# ---------------------------------------------------------------------------


class RefreshVaultTest(unittest.TestCase):
    def setUp(self):
        self.workdir = make_test_temp_dir(self, "obsidian-refresh")
        self.sqlite_path = self.workdir / "test.db"
        self.vault_path = self.workdir / "vault"

    def test_refresh_updates_auto_block(self):
        _seed_db(self.sqlite_path)
        export_vault(self.sqlite_path, self.vault_path)

        chat_path = self.vault_path / "Chats" / "chatgpt--1.md"
        before = chat_path.read_text(encoding="utf-8")

        result = refresh_vault(self.sqlite_path, self.vault_path)

        self.assertIsInstance(result, RefreshResult)
        self.assertGreater(result.updated, 0)

        after = chat_path.read_text(encoding="utf-8")
        # AUTO markers still present
        self.assertIn(AUTO_BEGIN, after)
        self.assertIn(AUTO_END, after)

    def test_refresh_preserves_user_content(self):
        _seed_db(self.sqlite_path)
        export_vault(self.sqlite_path, self.vault_path)

        chat_path = self.vault_path / "Chats" / "chatgpt--1.md"
        content = chat_path.read_text(encoding="utf-8")

        # Add user annotation after AUTO_END
        content = content + "\n## My Personal Notes\nThis must survive.\n"
        chat_path.write_text(content, encoding="utf-8")

        refresh_vault(self.sqlite_path, self.vault_path)

        refreshed = chat_path.read_text(encoding="utf-8")
        self.assertIn("This must survive.", refreshed)

    def test_refresh_skips_files_without_markers(self):
        _seed_db(self.sqlite_path)
        export_vault(self.sqlite_path, self.vault_path)

        # Write a file without AUTO markers
        manual = self.vault_path / "Chats" / "manual--999.md"
        manual.write_text("# Manual note\nNo markers here.\n", encoding="utf-8")

        result = refresh_vault(self.sqlite_path, self.vault_path)
        self.assertGreater(result.skipped, 0)

        # Manual file unchanged
        self.assertEqual(
            manual.read_text(encoding="utf-8"),
            "# Manual note\nNo markers here.\n",
        )


if __name__ == "__main__":
    unittest.main()
