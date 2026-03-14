"""Focused tests for provider-agnostic importer contract behavior."""

from __future__ import annotations

import unittest
from pathlib import Path

from flask import Flask

from src.app.models import ImportedConversation
from src.app.models.db import db
from src.importers.chatgpt import ChatGPTImporter, parse_chatgpt_export_file
from src.importers.claude import ClaudeImporter
from src.importers.contracts import (
    PROVIDER_CHATGPT,
    PROVIDER_CLAUDE,
    PROVIDER_GEMINI,
    ConversationImporter,
    NormalizedConversation,
    validate_provider_id,
)
from src.importers.persistence import persist_normalized_conversations
from tests.temp_helpers import make_test_temp_dir


class ImporterContractTest(unittest.TestCase):
    def test_chatgpt_importer_conforms_to_contract(self):
        importer: ConversationImporter = ChatGPTImporter()
        self.assertEqual(importer.provider_id, PROVIDER_CHATGPT)

        fixture = Path("sample_data/chatgpt_export_sample.json")
        conversations = parse_chatgpt_export_file(fixture)
        parsed = importer.parse_payload([{"id": "x", "title": "t", "mapping": {}}])

        self.assertEqual(parsed[0].source_provider, PROVIDER_CHATGPT)
        self.assertEqual(conversations[0].source_provider, PROVIDER_CHATGPT)

    def test_claude_importer_conforms_to_contract(self):
        importer: ConversationImporter = ClaudeImporter()
        self.assertEqual(importer.provider_id, PROVIDER_CLAUDE)

        parsed = importer.parse_payload(
            [
                {
                    "uuid": "claude-conv-1",
                    "name": "Claude test",
                    "chat_messages": [],
                }
            ]
        )

        self.assertEqual(parsed[0].source_provider, PROVIDER_CLAUDE)

    def test_gemini_importer_conforms_to_contract(self):
        from src.importers.gemini import GeminiImporter

        importer: ConversationImporter = GeminiImporter()
        self.assertEqual(importer.provider_id, PROVIDER_GEMINI)

        parsed = importer.parse_payload(
            [
                {
                    "title": "Gemini test",
                    "messages": [
                        {"role": "user", "content": "Hello"},
                        {"role": "model", "content": "Hi"},
                    ],
                }
            ]
        )

        self.assertEqual(parsed[0].source_provider, PROVIDER_GEMINI)

    def test_provider_identity_is_preserved_through_persistence(self):
        fixture = Path("sample_data/chatgpt_export_sample.json")
        conversations = parse_chatgpt_export_file(fixture)

        workdir = make_test_temp_dir(self, "importer-contract")
        app = Flask(__name__)
        app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{workdir / 'provider_identity.db'}"
        app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

        db.init_app(app)
        with app.app_context():
            try:
                db.create_all()
                persist_normalized_conversations(conversations)

                stored_sources = {
                    row.source for row in ImportedConversation.query.with_entities(ImportedConversation.source).all()
                }
                self.assertEqual(stored_sources, {PROVIDER_CHATGPT})
            finally:
                db.session.remove()
                db.engine.dispose()


    def test_persistence_rejects_invalid_provider_identity(self):
        invalid = NormalizedConversation(
            source_provider="unsupported-provider",
            source_conversation_id="conv-x",
            title="Bad",
            created_at=None,
            updated_at=None,
            messages=[],
            source_metadata={},
        )

        workdir = make_test_temp_dir(self, "importer-contract")
        app = Flask(__name__)
        app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{workdir / 'invalid_provider.db'}"
        app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

        db.init_app(app)
        with app.app_context():
            try:
                db.create_all()
                with self.assertRaises(ValueError):
                    persist_normalized_conversations([invalid])
            finally:
                db.session.remove()
                db.engine.dispose()

    def test_validate_provider_id_rejects_blank_or_unsupported(self):
        with self.assertRaises(ValueError):
            validate_provider_id("   ")

        self.assertEqual(validate_provider_id("gemini"), PROVIDER_GEMINI)

        with self.assertRaises(ValueError):
            validate_provider_id("unsupported-provider")


if __name__ == "__main__":
    unittest.main()
