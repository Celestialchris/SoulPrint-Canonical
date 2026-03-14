"""Tests for Memory Passport validation and integrity diagnostics."""

from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stdout
from datetime import UTC, datetime
from pathlib import Path

from flask import Flask

from src.app.models import MemoryEntry
from src.app.models.db import db
from src.importers.cli import import_chatgpt_export_to_sqlite, import_conversation_export_to_sqlite
from src.passport import cli as passport_cli
from src.passport.export import export_memory_passport
from src.passport.validator import (
    STATUS_INVALID,
    STATUS_VALID,
    STATUS_VALID_WITH_WARNINGS,
    validate_memory_passport,
)
from tests.temp_helpers import make_test_temp_dir


class PassportValidationTest(unittest.TestCase):
    def _bootstrap_native_entry(self, sqlite_path: Path) -> None:
        app = Flask(__name__)
        app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{sqlite_path}"
        app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        db.init_app(app)
        with app.app_context():
            try:
                db.session.add(
                    MemoryEntry(
                        timestamp=datetime(2024, 3, 10, 12, 30, tzinfo=UTC),
                        role="user",
                        content="Remember: Lisbon bakery shortlist.",
                        tags="travel,food",
                    )
                )
                db.session.commit()
            finally:
                db.session.remove()
                db.engine.dispose()

    def _export_chatgpt_passport(self, *, include_native: bool = True) -> Path:
        workdir = make_test_temp_dir(self, "passport-validation")
        sqlite_path = workdir / "passport.db"
        import_chatgpt_export_to_sqlite(
            Path("sample_data/chatgpt_export_sample.json"),
            sqlite_path,
        )
        if include_native:
            self._bootstrap_native_entry(sqlite_path)

        result = export_memory_passport(
            sqlite_path=sqlite_path,
            output_dir=workdir / "exports",
            created_at=datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC),
            export_id="passport-validation-test",
        )
        return result.package_dir

    def _read_json(self, path: Path) -> dict:
        return json.loads(path.read_text(encoding="utf-8"))

    def _write_json(self, path: Path, payload: dict) -> None:
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def _read_jsonl(self, path: Path) -> list[dict]:
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]

    def _write_jsonl(self, path: Path, records: list[dict]) -> None:
        lines = [json.dumps(record, sort_keys=True) for record in records]
        path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")

    def test_exported_passport_validates_cleanly(self):
        package_dir = self._export_chatgpt_passport()

        result = validate_memory_passport(package_dir)

        self.assertEqual(result.status, STATUS_VALID)
        self.assertEqual(result.errors, [])
        self.assertEqual(result.warnings, [])
        self.assertEqual(result.checked_counts["imported_conversations"], 2)
        self.assertEqual(result.checked_counts["imported_messages"], 4)
        self.assertEqual(result.checked_counts["native_memory_entries"], 1)
        self.assertEqual(result.provider_summary["chatgpt"]["imported_conversations"], 2)
        self.assertEqual(result.provider_summary["chatgpt"]["imported_messages"], 4)
        self.assertEqual(result.provider_summary["soulprint"]["native_memory_entries"], 1)

    def test_missing_required_manifest_field_is_invalid(self):
        package_dir = self._export_chatgpt_passport()
        manifest_path = package_dir / "manifest.json"
        manifest = self._read_json(manifest_path)
        manifest.pop("passport_version")
        self._write_json(manifest_path, manifest)

        result = validate_memory_passport(package_dir)

        self.assertEqual(result.status, STATUS_INVALID)
        self.assertTrue(any("passport_version" in error.message for error in result.errors))

    def test_missing_message_reference_is_invalid(self):
        package_dir = self._export_chatgpt_passport()
        messages_path = package_dir / "conversations" / "imported" / "chatgpt" / "messages.jsonl"
        records = self._read_jsonl(messages_path)
        records[0]["conversation_stable_id"] = "imported_conversation:999999"
        self._write_jsonl(messages_path, records)

        result = validate_memory_passport(package_dir)

        self.assertEqual(result.status, STATUS_INVALID)
        self.assertTrue(
            any("references missing conversation" in error.message for error in result.errors)
        )

    def test_duplicate_conflicting_stable_id_is_invalid(self):
        package_dir = self._export_chatgpt_passport()
        conversations_path = (
            package_dir / "conversations" / "imported" / "chatgpt" / "conversations.jsonl"
        )
        records = self._read_jsonl(conversations_path)
        duplicate = dict(records[0])
        duplicate["source_record_id"] = "conflicting-conversation-id"
        records.append(duplicate)
        self._write_jsonl(conversations_path, records)

        result = validate_memory_passport(package_dir)

        self.assertEqual(result.status, STATUS_INVALID)
        self.assertTrue(any("duplicate stable_id" in error.message for error in result.errors))

    def test_incomplete_metadata_warns_but_remains_usable(self):
        package_dir = self._export_chatgpt_passport()
        conversations_path = (
            package_dir / "conversations" / "imported" / "chatgpt" / "conversations.jsonl"
        )
        records = self._read_jsonl(conversations_path)
        records[0].pop("created_at_unix", None)
        records[0].pop("created_at_iso", None)
        self._write_jsonl(conversations_path, records)

        result = validate_memory_passport(package_dir)

        self.assertEqual(result.status, STATUS_VALID_WITH_WARNINGS)
        self.assertEqual(result.errors, [])
        self.assertTrue(
            any("missing created_at timestamp metadata" in warning.message for warning in result.warnings)
        )

    def test_integrity_notes_array_remains_valid(self):
        package_dir = self._export_chatgpt_passport()
        manifest_path = package_dir / "manifest.json"
        manifest = self._read_json(manifest_path)
        manifest["integrity_notes"] = [
            "v1 non-cryptographic export",
            "deterministic JSON/JSONL ordering",
        ]
        self._write_json(manifest_path, manifest)

        result = validate_memory_passport(package_dir)

        self.assertEqual(result.status, STATUS_VALID)
        self.assertEqual(result.errors, [])

    def test_import_export_validate_round_trip_for_provider_path(self):
        workdir = make_test_temp_dir(self, "passport-roundtrip")
        sqlite_path = workdir / "claude.db"
        import_conversation_export_to_sqlite(
            Path("sample_data/claude_export_sample.json"),
            sqlite_path,
            provider="claude",
        )
        package_dir = export_memory_passport(
            sqlite_path=sqlite_path,
            output_dir=workdir / "exports",
            created_at=datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC),
            export_id="claude-roundtrip-passport",
        ).package_dir

        result = validate_memory_passport(package_dir)

        self.assertEqual(result.status, STATUS_VALID)
        self.assertEqual(result.provider_summary["claude"]["imported_conversations"], 2)
        self.assertEqual(result.provider_summary["claude"]["imported_messages"], 6)

    def test_validate_cli_emits_machine_readable_result(self):
        package_dir = self._export_chatgpt_passport()

        stdout = io.StringIO()
        with redirect_stdout(stdout):
            exit_code = passport_cli.main(["validate", str(package_dir), "--json"])

        self.assertEqual(exit_code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["status"], STATUS_VALID)
        self.assertEqual(payload["checked_counts"]["imported_conversations"], 2)


if __name__ == "__main__":
    unittest.main()
