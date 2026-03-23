"""Tests for the Obsidian Bridge CLI."""

import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from flask import Flask

from src.app.models import ImportedConversation, ImportedMessage
from src.app.models.db import db
from src.obsidian.cli import main
from tests.temp_helpers import make_test_temp_dir


def _seed_db(sqlite_path: Path) -> None:
    """Seed a minimal test database."""
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{sqlite_path}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    with app.app_context():
        try:
            db.create_all()
            conv = ImportedConversation(
                source="chatgpt",
                source_conversation_id="conv-1",
                title="Test conversation",
                created_at_unix=1742673000.0,
                updated_at_unix=1742673000.0,
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
                    created_at_unix=1742673000.0,
                )
            )
            db.session.commit()
        finally:
            db.session.remove()
            db.engine.dispose()


class ObsidianCliExportTest(unittest.TestCase):
    def setUp(self):
        self.workdir = make_test_temp_dir(self, "obsidian-cli")
        self.sqlite_path = self.workdir / "test.db"
        self.vault_path = self.workdir / "vault"
        _seed_db(self.sqlite_path)

    def test_export_subcommand_works(self):
        output = StringIO()
        with redirect_stdout(output):
            code = main([
                "export",
                "--db", str(self.sqlite_path),
                "--vault", str(self.vault_path),
            ])
        self.assertEqual(code, 0)
        self.assertIn("Exported", output.getvalue())

    def test_default_subcommand_is_export(self):
        output = StringIO()
        with redirect_stdout(output):
            code = main([
                "--db", str(self.sqlite_path),
                "--vault", str(self.vault_path),
            ])
        self.assertEqual(code, 0)
        self.assertIn("Exported", output.getvalue())

    def test_dry_run_flag(self):
        output = StringIO()
        with redirect_stdout(output):
            code = main([
                "export",
                "--db", str(self.sqlite_path),
                "--vault", str(self.vault_path),
                "--dry-run",
            ])
        self.assertEqual(code, 0)
        self.assertIn("[dry run]", output.getvalue())

    def test_missing_vault_flag_errors(self):
        with self.assertRaises(SystemExit) as ctx:
            main(["export", "--db", str(self.sqlite_path)])
        self.assertNotEqual(ctx.exception.code, 0)


class ObsidianCliRefreshTest(unittest.TestCase):
    def setUp(self):
        self.workdir = make_test_temp_dir(self, "obsidian-cli-refresh")
        self.sqlite_path = self.workdir / "test.db"
        self.vault_path = self.workdir / "vault"
        _seed_db(self.sqlite_path)
        # Pre-export so there's a vault to refresh
        from src.obsidian.exporter import export_vault

        export_vault(self.sqlite_path, self.vault_path)

    def test_refresh_subcommand_works(self):
        output = StringIO()
        with redirect_stdout(output):
            code = main([
                "refresh",
                "--db", str(self.sqlite_path),
                "--vault", str(self.vault_path),
            ])
        self.assertEqual(code, 0)
        self.assertIn("Updated", output.getvalue())


if __name__ == "__main__":
    unittest.main()
