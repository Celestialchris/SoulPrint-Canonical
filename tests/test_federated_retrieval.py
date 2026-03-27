"""Tests for federated read-only retrieval across native + imported lanes."""

from datetime import datetime
import unittest

from flask import Flask

from src.app.models import ImportedConversation, ImportedMessage, MemoryEntry
from src.app.models.db import db
from src.retrieval import federated_search
from tests.temp_helpers import make_test_temp_dir


class FederatedRetrievalTest(unittest.TestCase):
    def test_federated_search_returns_both_lanes_with_source_metadata(self):
        workdir = make_test_temp_dir(self, "federated-retrieval")
        sqlite_path = workdir / "federated.db"
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
        workdir = make_test_temp_dir(self, "federated-retrieval")
        sqlite_path = workdir / "federated_keyword.db"
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

    def test_imported_lane_prefers_updated_then_created_timestamps_over_id(self):
        workdir = make_test_temp_dir(self, "federated-retrieval")
        sqlite_path = workdir / "federated_imported_order.db"
        app = Flask(__name__)
        app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{sqlite_path}"
        app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

        db.init_app(app)
        with app.app_context():
            try:
                db.create_all()

                older_insert_newer_timestamp = ImportedConversation(
                    source="chatgpt",
                    source_conversation_id="conv-newer-ts",
                    title="Newest by timestamp",
                    created_at_unix=1710000100.0,
                    updated_at_unix=1710000900.0,
                )
                newer_insert_older_timestamp = ImportedConversation(
                    source="chatgpt",
                    source_conversation_id="conv-older-ts",
                    title="Older by timestamp",
                    created_at_unix=1710000000.0,
                    updated_at_unix=1710000200.0,
                )
                db.session.add(older_insert_newer_timestamp)
                db.session.add(newer_insert_older_timestamp)
                db.session.commit()
            finally:
                db.session.remove()
                db.engine.dispose()

        rows = federated_search(sqlite_path, limit_per_lane=1)

        imported_rows = [row for row in rows if row.source_lane == "imported_conversation"]
        self.assertEqual(
            [row.source_metadata["source_conversation_id"] for row in imported_rows],
            ["conv-newer-ts"],
        )

    def test_imported_message_match_adds_evidence_text_without_changing_primary_stable_id(self):
        workdir = make_test_temp_dir(self, "federated-retrieval")
        sqlite_path = workdir / "federated_imported_evidence.db"
        app = Flask(__name__)
        app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{sqlite_path}"
        app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

        db.init_app(app)
        with app.app_context():
            try:
                db.create_all()

                imported = ImportedConversation(
                    source="chatgpt",
                    source_conversation_id="conv-evidence",
                    title="General planning",
                    created_at_unix=1710000000.0,
                    updated_at_unix=1710000300.0,
                )
                db.session.add(imported)
                db.session.flush()
                db.session.add_all(
                    [
                        ImportedMessage(
                            conversation_id=imported.id,
                            source_message_id="msg-non-match",
                            role="user",
                            content="Talk about packing lists.",
                            sequence_index=0,
                            created_at_unix=1710000001.0,
                        ),
                        ImportedMessage(
                            conversation_id=imported.id,
                            source_message_id="msg-match",
                            role="assistant",
                            content="Include baking ideas for the fundraiser.",
                            sequence_index=1,
                            created_at_unix=1710000002.0,
                        ),
                    ]
                )
                db.session.commit()
            finally:
                db.session.remove()
                db.engine.dispose()

        rows = federated_search(sqlite_path, keyword="baking")

        self.assertEqual(len(rows), 1)
        imported_row = rows[0]
        self.assertEqual(imported_row.source_lane, "imported_conversation")
        self.assertEqual(imported_row.stable_id, "imported_conversation:1")
        self.assertEqual(imported_row.title, "General planning")
        self.assertEqual(imported_row.evidence_text, "Include baking ideas for the fundraiser.")
        self.assertEqual(imported_row.evidence_stable_ids, ["imported_conversation:1"])


if __name__ == "__main__":
    unittest.main()
