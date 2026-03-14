"""Tests for federated retrieval CLI output."""

from __future__ import annotations

from contextlib import redirect_stdout
from datetime import datetime
from io import StringIO
import unittest
from unittest.mock import patch

from flask import Flask

from src.app.models import ImportedConversation, ImportedMessage, MemoryEntry
from src.app.models.db import db
from src.retrieval import cli
from tests.temp_helpers import make_test_temp_dir


class FederatedCliTest(unittest.TestCase):
    def test_cli_search_prints_mixed_lane_fields(self):
        workdir = make_test_temp_dir(self, "federated-cli")
        sqlite_path = workdir / "federated_cli.db"
        app = Flask(__name__)
        app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{sqlite_path}"
        app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

        db.init_app(app)
        with app.app_context():
            try:
                db.create_all()

                db.session.add(
                    MemoryEntry(
                        timestamp=datetime(2024, 3, 9, 16, 10, 0),
                        role="user",
                        content="Lisbon food notes",
                        tags="travel,food",
                    )
                )
                imported = ImportedConversation(
                    source="chatgpt",
                    source_conversation_id="conv-1",
                    title="Trip planning",
                    created_at_unix=1710000000.0,
                    updated_at_unix=1710000300.0,
                )
                db.session.add(imported)
                db.session.flush()
                db.session.add(
                    ImportedMessage(
                        conversation_id=imported.id,
                        source_message_id="msg-1",
                        role="user",
                        content="Plan a 2-day Lisbon trip.",
                        sequence_index=0,
                        created_at_unix=1710000001.0,
                    )
                )
                db.session.commit()
            finally:
                db.session.remove()
                db.engine.dispose()

        output = StringIO()
        with patch(
            "sys.argv",
            ["federated-cli", "--db", str(sqlite_path), "Lisbon", "--limit-per-lane", "5"],
        ):
            with redirect_stdout(output):
                exit_code = cli.main()

        text = output.getvalue()
        self.assertEqual(exit_code, 0)
        self.assertIn("source_lane: native_memory", text)
        self.assertIn("source_lane: imported_conversation", text)
        self.assertIn("stable_id: memory:1", text)
        self.assertIn("stable_id: imported_conversation:1", text)
        self.assertIn("title: Lisbon food notes", text)
        self.assertIn("title: Trip planning", text)
        self.assertIn('source_metadata: {"role": "user", "tags": "travel,food"}', text)
        self.assertIn(
            'source_metadata: {"source": "chatgpt", "source_conversation_id": "conv-1"}',
            text,
        )


if __name__ == "__main__":
    unittest.main()
