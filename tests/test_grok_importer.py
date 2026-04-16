"""Tests for Grok (xAI) export normalization and SQLite persistence."""

import json
import unittest
from pathlib import Path

from flask import Flask

from src.app.models import ImportedConversation, ImportedMessage
from src.app.models.db import db
from src.importers import (
    PROVIDER_GROK,
    GrokImporter,
    parse_grok_export_file,
    persist_normalized_conversations,
)
from src.importers.grok import looks_like_grok_export, parse_grok_export
from src.importers.registry import parse_import_file
from tests.temp_helpers import make_test_temp_dir, release_app_db_handles

_FIXTURE = Path("sample_data/grok.json")
_CHATGPT_FIXTURE = Path("sample_data/chatgpt.json")
_CLAUDE_FIXTURE = Path("sample_data/claude.json")


def _make_app(db_path: Path) -> Flask:
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    with app.app_context():
        db.create_all()
    return app


class GrokParserTest(unittest.TestCase):
    def test_parse_grok_fixture_normalizes_conversations_and_messages(self):
        conversations = parse_grok_export_file(_FIXTURE)

        self.assertEqual(len(conversations), 2)

        first = conversations[0]
        self.assertEqual(first.source_provider, "grok")
        self.assertEqual(first.source_conversation_id, "a1b2c3d4-e5f6-7890-abcd-ef1234567890")
        self.assertEqual(len(first.messages), 4)
        self.assertEqual(
            [m.role for m in first.messages],
            ["user", "assistant", "user", "assistant"],
        )
        self.assertEqual([m.sequence_index for m in first.messages], [0, 1, 2, 3])

        second = conversations[1]
        self.assertEqual(len(second.messages), 1)
        self.assertEqual(second.messages[0].role, "user")

    def test_grok_first_conversation_has_correct_metadata(self):
        conversations = parse_grok_export_file(_FIXTURE)
        first = conversations[0]

        self.assertEqual(first.title, "Machine Learning Basics")
        self.assertIsNotNone(first.source_conversation_id)
        self.assertIsNotNone(first.created_at)
        self.assertIsNotNone(first.updated_at)

    def test_grok_fallback_title_for_empty_title(self):
        conversations = parse_grok_export_file(_FIXTURE)
        second = conversations[1]

        self.assertEqual(second.title, "Untitled Conversation")

    def test_grok_timestamps_parsed_from_mongodb_bson(self):
        conversations = parse_grok_export_file(_FIXTURE)
        first = conversations[0]

        for msg in first.messages:
            self.assertIsNotNone(msg.created_at, f"Message {msg.source_message_id} has None timestamp")
            self.assertGreater(msg.created_at, 1e9, "Timestamp should be a valid Unix epoch in seconds")

    def test_grok_source_metadata_contains_model(self):
        conversations = parse_grok_export_file(_FIXTURE)
        first = conversations[0]

        self.assertIn("grok_model", first.source_metadata)
        self.assertEqual(first.source_metadata["grok_model"], "grok-3")


class GrokDetectorTest(unittest.TestCase):
    def test_looks_like_grok_export_true_for_grok_payload(self):
        with _FIXTURE.open("r", encoding="utf-8") as fh:
            payload = json.load(fh)
        self.assertTrue(looks_like_grok_export(payload))

    def test_looks_like_grok_export_false_for_chatgpt_payload(self):
        with _CHATGPT_FIXTURE.open("r", encoding="utf-8") as fh:
            payload = json.load(fh)
        self.assertFalse(looks_like_grok_export(payload))

    def test_looks_like_grok_export_false_for_claude_payload(self):
        with _CLAUDE_FIXTURE.open("r", encoding="utf-8") as fh:
            payload = json.load(fh)
        self.assertFalse(looks_like_grok_export(payload))

    def test_looks_like_grok_export_false_for_non_dict(self):
        self.assertFalse(looks_like_grok_export([{"conversation": {}, "responses": []}]))

    def test_looks_like_grok_export_false_for_empty_dict(self):
        self.assertFalse(looks_like_grok_export({}))


class GrokRegistryTest(unittest.TestCase):
    def test_registry_auto_detects_grok_fixture(self):
        result = parse_import_file(_FIXTURE)
        self.assertEqual(result.provider_id, "grok")
        self.assertEqual(len(result.conversations), 2)


class GrokPersistenceTest(unittest.TestCase):
    def test_persist_grok_conversations_to_sqlite(self):
        conversations = parse_grok_export_file(_FIXTURE)

        workdir = make_test_temp_dir(self, "grok-importer")
        app = _make_app(workdir / "grok_test.db")

        with app.app_context():
            result = persist_normalized_conversations(conversations)

        self.assertEqual(result.imported_conversations, 2)
        self.assertEqual(result.imported_messages, 5)
        self.assertEqual(result.skipped_conversations, 0)

        with app.app_context():
            stored_convs = ImportedConversation.query.all()
            self.assertEqual(len(stored_convs), 2)
            sources = {c.source for c in stored_convs}
            self.assertEqual(sources, {"grok"})

        release_app_db_handles(app)


class GrokContractTest(unittest.TestCase):
    def test_grok_importer_conforms_to_contract(self):
        importer = GrokImporter()
        self.assertEqual(importer.provider_id, "grok")

        minimal_payload = {
            "conversations": [
                {
                    "conversation": {
                        "id": "test-conv-1",
                        "title": "Test",
                        "create_time": "2025-01-01T00:00:00.000Z",
                        "modify_time": "2025-01-01T00:00:00.000Z",
                    },
                    "responses": [
                        {
                            "response": {
                                "_id": "r1",
                                "conversation_id": "test-conv-1",
                                "message": "Hello",
                                "sender": "human",
                                "create_time": {"$date": {"$numberLong": "1735689600000"}},
                                "model": "grok-3",
                            }
                        }
                    ],
                }
            ]
        }
        result = importer.parse_payload(minimal_payload)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].source_provider, "grok")


class GrokEdgeCaseTest(unittest.TestCase):
    def test_grok_empty_responses_skipped(self):
        payload = {
            "conversations": [
                {
                    "conversation": {
                        "id": "empty-conv",
                        "title": "Empty",
                        "create_time": "2025-01-01T00:00:00.000Z",
                        "modify_time": "2025-01-01T00:00:00.000Z",
                    },
                    "responses": [],
                }
            ]
        }
        result = parse_grok_export(payload)
        self.assertEqual(len(result), 0)

    def test_conversations_not_a_list_raises_value_error(self):
        with self.assertRaises(ValueError) as ctx:
            parse_grok_export({"conversations": {"not": "a list"}})
        self.assertIn("list", str(ctx.exception))

    def test_fallback_id_stable_when_first_conv_is_malformed(self):
        """Skipping a malformed first conv must not shift the fallback ID of later convs."""
        payload = {
            "conversations": [
                # index 0 — malformed (no 'conversation' key), will be skipped
                {"responses": []},
                # index 1 — valid, no explicit id → should get grok-conv-1, not grok-conv-0
                {
                    "conversation": {
                        "title": "Second",
                        "create_time": "2025-01-01T00:00:00.000Z",
                        "modify_time": "2025-01-01T00:00:00.000Z",
                    },
                    "responses": [
                        {
                            "response": {
                                "_id": "r1",
                                "message": "Hello",
                                "sender": "human",
                                "create_time": {"$date": {"$numberLong": "1735689600000"}},
                            }
                        }
                    ],
                },
            ]
        }
        result = parse_grok_export(payload)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].source_conversation_id, "grok-conv-1")

    def test_grok_empty_message_text_skipped(self):
        payload = {
            "conversations": [
                {
                    "conversation": {
                        "id": "whitespace-conv",
                        "title": "Whitespace Test",
                        "create_time": "2025-01-01T00:00:00.000Z",
                        "modify_time": "2025-01-01T00:00:00.000Z",
                    },
                    "responses": [
                        {
                            "response": {
                                "_id": "r1",
                                "conversation_id": "whitespace-conv",
                                "message": "   ",
                                "sender": "human",
                                "create_time": {"$date": {"$numberLong": "1735689600000"}},
                                "model": "grok-3",
                            }
                        },
                        {
                            "response": {
                                "_id": "r2",
                                "conversation_id": "whitespace-conv",
                                "message": "Hello there",
                                "sender": "assistant",
                                "create_time": {"$date": {"$numberLong": "1735689615000"}},
                                "model": "grok-3",
                            }
                        },
                    ],
                }
            ]
        }
        result = parse_grok_export(payload)
        self.assertEqual(len(result), 1)
        self.assertEqual(len(result[0].messages), 1)
        self.assertEqual(result[0].messages[0].content, "Hello there")


if __name__ == "__main__":
    unittest.main()
