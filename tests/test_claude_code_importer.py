"""Tests for Claude Code session JSONL normalization and SQLite persistence."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from flask import Flask

from src.app.models import ImportedConversation, ImportedMessage
from src.app.models.db import db
from src.importers.claude_code import (
    TRUNCATE_AT,
    ClaudeCodeImporter,
    looks_like_claude_code_export,
)
from src.importers.contracts import PROVIDER_CLAUDE_CODE, SUPPORTED_IMPORT_PROVIDERS
from src.importers.persistence import persist_normalized_conversations
from src.importers.registry import parse_import_file
from tests.temp_helpers import make_test_temp_dir

_FIXTURE = Path("sample_data/claude_code.jsonl")
_CLAUDE_JSON_FIXTURE = Path("sample_data/claude.json")
_SESSION_ID = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"


def _fixture_bytes() -> bytes:
    return _FIXTURE.read_bytes()


class ClaudeCodeDetectorTest(unittest.TestCase):
    def test_detects_valid_session(self):
        self.assertTrue(looks_like_claude_code_export(_fixture_bytes()))

    def test_rejects_claude_json_export(self):
        payload = _CLAUDE_JSON_FIXTURE.read_bytes()
        self.assertFalse(looks_like_claude_code_export(payload))

    def test_rejects_invalid_utf8(self):
        self.assertFalse(looks_like_claude_code_export(b"\xff\xfe\xfd"))

    def test_rejects_empty(self):
        self.assertFalse(looks_like_claude_code_export(b""))

    def test_rejects_non_json_jsonl(self):
        self.assertFalse(looks_like_claude_code_export(b"not json at all\n"))


class ClaudeCodeParseTest(unittest.TestCase):
    def setUp(self):
        self._importer = ClaudeCodeImporter()
        self._conversations = self._importer.parse_payload(_fixture_bytes())

    def test_empty_file_returns_empty(self):
        result = self._importer.parse_payload(b"")
        self.assertEqual(result, [])

    def test_happy_path_fixture(self):
        self.assertEqual(len(self._conversations), 1)
        conv = self._conversations[0]
        self.assertEqual(conv.source_provider, PROVIDER_CLAUDE_CODE)
        self.assertEqual(conv.source_conversation_id, _SESSION_ID)
        # 8 kept messages: lines 3,4,5,6,7,8,9,11 (lines 1,2,10,12 skipped)
        self.assertEqual(len(conv.messages), 8)

    def test_tool_use_bash_rendering(self):
        conv = self._conversations[0]
        # message index 1 is the assistant with thinking+text+tool_use(Bash)
        msg = conv.messages[1]
        self.assertIn("[Tool: Bash]", msg.content)
        self.assertIn("cat src/utils/helpers.py", msg.content)

    def test_write_tool_use_rendering(self):
        conv = self._conversations[0]
        # message index 3 is assistant with tool_use(Write)+text
        msg = conv.messages[3]
        self.assertIn("[Tool: Write]", msg.content)
        self.assertIn("src/utils/helpers.py", msg.content)

    def test_tool_result_string_content(self):
        conv = self._conversations[0]
        # message index 2 is user with tool_result (string content)
        msg = conv.messages[2]
        self.assertIn("def process(items)", msg.content)

    def test_tool_result_list_content_flattened(self):
        conv = self._conversations[0]
        # message index 4 is user with tool_result (list-typed content)
        msg = conv.messages[4]
        self.assertIn("File written successfully", msg.content)
        self.assertNotIn("[{", msg.content)  # must not be a raw list repr

    def test_tool_result_error_marker(self):
        conv = self._conversations[0]
        # message index 6 is user with is_error: true tool_result
        msg = conv.messages[6]
        self.assertTrue(msg.content.startswith("[Error]"))

    def test_thinking_blocks_dropped(self):
        conv = self._conversations[0]
        thinking_text = "I should analyze the function structure first."
        for msg in conv.messages:
            self.assertNotIn(thinking_text, msg.content)

    def test_malformed_jsonl_line_skipped(self):
        raw = _fixture_bytes()
        # Inject a bad line at the top — must not crash and must yield same result
        injected = b"THIS IS NOT JSON\n" + raw
        result = self._importer.parse_payload(injected)
        self.assertEqual(len(result), 1)
        self.assertEqual(len(result[0].messages), 8)

    def test_missing_timestamp_skipped(self):
        # Build a minimal payload with one valid message and one with no timestamp
        session = _SESSION_ID
        valid = json.dumps({
            "type": "user",
            "sessionId": session,
            "uuid": "x1",
            "timestamp": "2026-04-19T10:00:02.000Z",
            "message": {"role": "user", "content": "Hello"},
        })
        no_ts = json.dumps({
            "type": "assistant",
            "sessionId": session,
            "uuid": "x2",
            "message": {"role": "assistant", "content": [{"type": "text", "text": "Hi"}]},
        })
        payload = (valid + "\n" + no_ts + "\n").encode()
        result = self._importer.parse_payload(payload)
        self.assertEqual(len(result), 1)
        self.assertEqual(len(result[0].messages), 1)

    def test_large_tool_result_truncated(self):
        big_content = "x" * 10000
        session = _SESSION_ID
        record = json.dumps({
            "type": "user",
            "sessionId": session,
            "uuid": "big-1",
            "timestamp": "2026-04-19T10:00:02.000Z",
            "message": {
                "role": "user",
                "content": [
                    {"type": "tool_result", "tool_use_id": "tu-big", "content": big_content, "is_error": False}
                ],
            },
        })
        result = self._importer.parse_payload(record.encode())
        self.assertEqual(len(result), 1)
        rendered = result[0].messages[0].content
        self.assertTrue(rendered.endswith("... [truncated]"))
        # content portion is exactly TRUNCATE_AT chars before the suffix
        suffix = "... [truncated]"
        body = rendered[: -len(suffix)]
        self.assertEqual(len(body), TRUNCATE_AT)


class ClaudeCodeContractTest(unittest.TestCase):
    def test_roundtrip_through_persist(self):
        importer = ClaudeCodeImporter()
        conversations = importer.parse_payload(_fixture_bytes())

        workdir = make_test_temp_dir(self, "claude-code-contract")
        app = Flask(__name__)
        app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{workdir / 'test.db'}"
        app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        db.init_app(app)

        with app.app_context():
            try:
                db.create_all()
                result = persist_normalized_conversations(conversations)
                self.assertEqual(result.imported_conversations, 1)
                self.assertEqual(result.imported_messages, 8)

                stored = ImportedConversation.query.all()
                self.assertEqual(len(stored), 1)
                self.assertEqual(stored[0].source, PROVIDER_CLAUDE_CODE)

                messages = ImportedMessage.query.all()
                self.assertEqual(len(messages), 8)
            finally:
                db.session.remove()
                db.engine.dispose()


class ClaudeCodeRegistryTest(unittest.TestCase):
    def test_registered_in_supported_providers(self):
        self.assertIn(PROVIDER_CLAUDE_CODE, SUPPORTED_IMPORT_PROVIDERS)

    def test_parse_import_file_routes_jsonl(self):
        result = parse_import_file(_FIXTURE)
        self.assertEqual(result.provider_id, PROVIDER_CLAUDE_CODE)
        self.assertEqual(len(result.conversations), 1)

    def test_parse_import_file_does_not_collide_with_claude_json(self):
        result = parse_import_file(_CLAUDE_JSON_FIXTURE)
        self.assertEqual(result.provider_id, "claude")


if __name__ == "__main__":
    unittest.main()
