"""Tests for minimal Memory Passport export package generation."""

from __future__ import annotations

import json
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

from flask import Flask

from src.app.models import MemoryEntry
from src.app.models.db import db
from src.importers.cli import import_chatgpt_export_to_sqlite, import_conversation_export_to_sqlite
from src.passport.export import export_memory_passport


class PassportExportTest(unittest.TestCase):
    def _bootstrap_native_entry(self, sqlite_path: Path) -> None:
        app = Flask(__name__)
        app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{sqlite_path}"
        app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        db.init_app(app)
        with app.app_context():
            try:
                entry = MemoryEntry(
                    timestamp=datetime(2024, 3, 10, 12, 30, tzinfo=UTC),
                    role="user",
                    content="Remember: Lisbon bakery shortlist.",
                    tags="travel,food",
                )
                db.session.add(entry)
                db.session.commit()
            finally:
                db.session.remove()
                db.engine.dispose()

    def test_export_writes_manifest_lane_files_markdown_and_provenance(self):
        fixture = Path("sample_data/chatgpt_export_sample.json")

        with tempfile.TemporaryDirectory() as tmpdir:
            temp_root = Path(tmpdir)
            sqlite_path = temp_root / "passport.db"
            import_chatgpt_export_to_sqlite(fixture, sqlite_path)
            self._bootstrap_native_entry(sqlite_path)

            result = export_memory_passport(
                sqlite_path=sqlite_path,
                output_dir=temp_root / "exports",
                created_at=datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC),
                export_id="test-export-id",
            )

            package_dir = result.package_dir
            manifest_path = package_dir / "manifest.json"
            imported_conversations_path = (
                package_dir / "conversations" / "imported" / "chatgpt" / "conversations.jsonl"
            )
            imported_messages_path = (
                package_dir / "conversations" / "imported" / "chatgpt" / "messages.jsonl"
            )
            native_entries_path = package_dir / "native" / "memory_entries.jsonl"
            provenance_path = package_dir / "provenance" / "index.jsonl"

            self.assertTrue(manifest_path.exists())
            self.assertTrue(imported_conversations_path.exists())
            self.assertTrue(imported_messages_path.exists())
            self.assertTrue(native_entries_path.exists())
            self.assertTrue(provenance_path.exists())

            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(manifest["passport_version"], "1.0")
            self.assertEqual(manifest["export_id"], "test-export-id")
            self.assertEqual(
                manifest["source_lanes"],
                ["imported_conversation", "native_memory"],
            )
            self.assertEqual(manifest["counts"]["imported_conversations"], 2)
            self.assertEqual(manifest["counts"]["imported_messages"], 4)
            self.assertEqual(manifest["counts"]["native_memory_entries"], 1)
            self.assertIn("chatgpt", manifest["source_providers"])

            imported_conversations = [
                json.loads(line)
                for line in imported_conversations_path.read_text(encoding="utf-8").splitlines()
            ]
            self.assertEqual(imported_conversations[0]["stable_id"], "imported_conversation:1")
            self.assertEqual(imported_conversations[0]["source_provider"], "chatgpt")
            self.assertEqual(
                imported_conversations[0]["source_metadata"]["source_conversation_id"], "conv-1"
            )

            native_entries = [
                json.loads(line) for line in native_entries_path.read_text(encoding="utf-8").splitlines()
            ]
            self.assertEqual(native_entries[0]["stable_id"], "memory:1")
            self.assertEqual(native_entries[0]["source_lane"], "native_memory")
            self.assertEqual(native_entries[0]["source_metadata"]["role"], "user")

            markdown_conversation = package_dir / "markdown" / "conversations" / "imported_conversation:1.md"
            markdown_native = package_dir / "markdown" / "native" / "memory:1.md"
            self.assertTrue(markdown_conversation.exists())
            self.assertTrue(markdown_native.exists())

            provenance_rows = [
                json.loads(line) for line in provenance_path.read_text(encoding="utf-8").splitlines()
            ]
            self.assertTrue(
                any(
                    row["stable_id"] == "imported_conversation:1"
                    and row["source_record_id"] == "conv-1"
                    for row in provenance_rows
                )
            )
            self.assertTrue(
                any(
                    row["stable_id"] == "memory:1" and row["source_provider"] == "soulprint"
                    for row in provenance_rows
                )
            )
            self.assertTrue(
                any(
                    row["unit_type"] == "derived"
                    and row["source_metadata"].get("canonical_stable_id") == "imported_conversation:1"
                    for row in provenance_rows
                )
            )

    def test_export_empty_database_is_safe_and_deterministic_shape(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_root = Path(tmpdir)
            sqlite_path = temp_root / "empty.db"

            app = Flask(__name__)
            app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{sqlite_path}"
            app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
            db.init_app(app)
            with app.app_context():
                try:
                    db.create_all()
                finally:
                    db.session.remove()
                    db.engine.dispose()

            result = export_memory_passport(
                sqlite_path=sqlite_path,
                output_dir=temp_root / "exports",
                created_at=datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC),
                export_id="empty-export-id",
            )

            package_dir = result.package_dir
            manifest_path = package_dir / "manifest.json"
            provenance_path = package_dir / "provenance" / "index.jsonl"

            self.assertTrue(manifest_path.exists())
            self.assertTrue(provenance_path.exists())
            self.assertFalse((package_dir / "conversations").exists())
            self.assertFalse((package_dir / "native").exists())

            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(manifest["source_lanes"], [])
            self.assertEqual(manifest["source_providers"], [])
            self.assertEqual(manifest["counts"]["imported_conversations"], 0)
            self.assertEqual(manifest["counts"]["imported_messages"], 0)
            self.assertEqual(manifest["counts"]["native_memory_entries"], 0)
            self.assertEqual(manifest["counts"]["provenance_units"], 0)
            self.assertEqual(provenance_path.read_text(encoding="utf-8"), "")

    def test_export_groups_imported_records_under_their_provider_paths(self):
        fixture = Path("sample_data/claude_export_sample.json")

        with tempfile.TemporaryDirectory() as tmpdir:
            temp_root = Path(tmpdir)
            sqlite_path = temp_root / "passport_claude.db"
            import_conversation_export_to_sqlite(fixture, sqlite_path, provider="claude")

            result = export_memory_passport(
                sqlite_path=sqlite_path,
                output_dir=temp_root / "exports",
                created_at=datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC),
                export_id="claude-export-id",
            )

            package_dir = result.package_dir
            imported_conversations_path = (
                package_dir / "conversations" / "imported" / "claude" / "conversations.jsonl"
            )
            imported_messages_path = (
                package_dir / "conversations" / "imported" / "claude" / "messages.jsonl"
            )
            provenance_path = package_dir / "provenance" / "index.jsonl"

            self.assertTrue(imported_conversations_path.exists())
            self.assertTrue(imported_messages_path.exists())

            provenance_rows = [
                json.loads(line) for line in provenance_path.read_text(encoding="utf-8").splitlines()
            ]
            self.assertTrue(
                any(
                    row["source_provider"] == "claude"
                    and row["path"] == "conversations/imported/claude/conversations.jsonl"
                    for row in provenance_rows
                )
            )
            self.assertTrue(
                any(
                    row["source_provider"] == "claude"
                    and row["path"] == "conversations/imported/claude/messages.jsonl"
                    for row in provenance_rows
                )
            )


if __name__ == "__main__":
    unittest.main()
