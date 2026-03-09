"""Tests for federated read-only retrieval across native + imported lanes."""

from datetime import datetime
from pathlib import Path
import tempfile
import unittest

from flask import Flask

from src.app.models import ImportedConversation, ImportedMessage, MemoryEntry
from src.app.models.db import db
from src.retrieval import federated_search


class FederatedRetrievalTest(unittest.TestCase):
    def test_federated_search_returns_both_lanes_with_source_metadata(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            sqlite_path = Path(tmpdir) / "federated.db"
            app = Flask(__name__)
            app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{sqlite_path}"
            app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

            db.init_app(app)
            with app.app_context():
                try:
                    db.create_all()

                    memory = MemoryEntry(
                        timestamp=datetime(2024, 3, 9, 16, 10, 0),
                        role="user",
                        content="Lisbon food notes",
                        tags="travel,food",
                    )
                    db.session.add(memory)

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
                            content="Plan me a 2-day trip to Lisbon.",
                            sequence_index=0,
                            created_at_unix=1710000001.0,
                        )
                    )
                    db.session.commit()
                finally:
                    db.session.remove()
                    db.engine.dispose()

            rows = federated_search(sqlite_path)

            self.assertEqual(len(rows), 2)
            self.assertEqual({row.source_lane for row in rows}, {"native_memory", "imported_conversation"})

            memory_row = next(row for row in rows if row.source_lane == "native_memory")
            self.assertEqual(memory_row.stable_id, "memory:1")
            self.assertEqual(memory_row.title, "Lisbon food notes")
            self.assertEqual(memory_row.source_metadata["role"], "user")

            imported_row = next(row for row in rows if row.source_lane == "imported_conversation")
            self.assertEqual(imported_row.stable_id, "imported_conversation:1")
            self.assertEqual(imported_row.title, "Trip planning")
            self.assertEqual(imported_row.source_metadata["source_conversation_id"], "conv-1")

    def test_federated_search_keyword_matches_both_lane_queries(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            sqlite_path = Path(tmpdir) / "federated_keyword.db"
            app = Flask(__name__)
            app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{sqlite_path}"
            app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

            db.init_app(app)
            with app.app_context():
                try:
                    db.create_all()
                    db.session.add(
                        MemoryEntry(
                            timestamp=datetime(2024, 3, 9, 17, 0, 0),
                            role="assistant",
                            content="Baking checklist",
                            tags="home",
                        )
                    )

                    imported = ImportedConversation(
                        source="chatgpt",
                        source_conversation_id="conv-2",
                        title="Ideas",
                        created_at_unix=1710003000.0,
                        updated_at_unix=1710003900.0,
                    )
                    db.session.add(imported)
                    db.session.flush()
                    db.session.add(
                        ImportedMessage(
                            conversation_id=imported.id,
                            source_message_id="msg-2",
                            role="assistant",
                            content="Include baking ideas",
                            sequence_index=0,
                            created_at_unix=1710003001.0,
                        )
                    )
                    db.session.commit()
                finally:
                    db.session.remove()
                    db.engine.dispose()

            rows = federated_search(sqlite_path, keyword="baking")

            self.assertEqual(len(rows), 2)
            self.assertEqual({row.source_lane for row in rows}, {"native_memory", "imported_conversation"})


if __name__ == "__main__":
    unittest.main()
