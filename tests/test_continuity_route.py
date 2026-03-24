"""Route tests for the continuity packet surface."""

from __future__ import annotations

import json
import os
import unittest
from unittest.mock import patch

from src.app import create_app
from src.app.models import ImportedConversation, ImportedMessage
from src.app.models.db import db
from src.config import Config, sqlite_uri_from_path
from src.intelligence.continuity.store import (
    default_continuity_store_path,
    list_artifacts_for_conversation,
)
from src.intelligence.provider import StubProvider
from tests.temp_helpers import make_test_temp_dir, release_app_db_handles

# The stub provider returns plain text, but the continuity service expects
# structured JSON.  Patch StubProvider.summarize with this canned response
# in tests that exercise the generation route.
_STUB_CONTINUITY_RESPONSE = json.dumps({
    "summary": "Stub continuity summary for testing.",
    "decisions": ["Use SQLite for local storage"],
    "open_loops": ["Deployment strategy TBD"],
    "entity_map": ["SQLite", "SoulPrint"],
})


class ContinuityRouteTest(unittest.TestCase):

    def setUp(self):
        self.workdir = make_test_temp_dir(self, "continuity-route")
        self._old_uri = Config.SQLALCHEMY_DATABASE_URI
        self.addCleanup(self._restore_sqlite_uri)
        self.sqlite_path = self.workdir / "continuity_route_test.db"
        Config.SQLALCHEMY_DATABASE_URI = sqlite_uri_from_path(self.sqlite_path)

        # Clear LLM env vars by default
        self._env_clean = {
            k: v for k, v in os.environ.items()
            if not k.startswith("SOULPRINT_LLM_")
        }

        self.app = create_app()
        self.client = self.app.test_client()
        self.addCleanup(release_app_db_handles, self.app, drop_all=True)

    def _restore_sqlite_uri(self):
        Config.SQLALCHEMY_DATABASE_URI = self._old_uri

    def _create_conversation(self) -> int:
        with self.app.app_context():
            conv = ImportedConversation(
                source="chatgpt",
                source_conversation_id="conv_cont_1",
                title="Continuity Test Chat",
                created_at_unix=1700000000.0,
                updated_at_unix=1700000300.0,
            )
            db.session.add(conv)
            db.session.flush()
            db.session.add(
                ImportedMessage(
                    conversation_id=conv.id,
                    source_message_id="msg_1",
                    role="user",
                    content="Should we use SQLite?",
                    sequence_index=0,
                    created_at_unix=1700000000.0,
                )
            )
            db.session.add(
                ImportedMessage(
                    conversation_id=conv.id,
                    source_message_id="msg_2",
                    role="assistant",
                    content="Yes, for local-first storage.",
                    sequence_index=1,
                    created_at_unix=1700000001.0,
                )
            )
            db.session.commit()
            return conv.id

    def _post_generate(self, conv_id: int):
        """POST to generate a continuity packet with a stub returning valid JSON."""
        with patch.dict(os.environ, {"SOULPRINT_LLM_PROVIDER": "stub"}, clear=False):
            with patch.object(
                StubProvider, "summarize", return_value=_STUB_CONTINUITY_RESPONSE
            ):
                return self.client.post(f"/intelligence/continuity/{conv_id}")

    # -- empty state --

    def test_get_continuity_no_artifacts_shows_empty_state(self):
        conv_id = self._create_conversation()
        with patch.dict(os.environ, {"SOULPRINT_LLM_PROVIDER": "stub"}, clear=False):
            response = self.client.get(f"/intelligence/continuity/{conv_id}")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("No continuity packet yet", html)

    # -- generation --

    def test_post_generate_creates_artifacts_and_redirects(self):
        conv_id = self._create_conversation()
        response = self._post_generate(conv_id)

        self.assertEqual(response.status_code, 302)
        self.assertIn(f"/intelligence/continuity/{conv_id}", response.headers["Location"])

        store_path = default_continuity_store_path(str(self.sqlite_path))
        artifacts = list_artifacts_for_conversation(
            store_path, f"imported_conversation:{conv_id}"
        )
        self.assertGreater(len(artifacts), 0)

    def test_post_generate_no_provider_returns_400(self):
        conv_id = self._create_conversation()
        with patch.dict(os.environ, self._env_clean, clear=True):
            response = self.client.post(f"/intelligence/continuity/{conv_id}")

        self.assertEqual(response.status_code, 400)

    # -- viewing artifacts --

    def test_get_continuity_shows_artifacts_after_generation(self):
        conv_id = self._create_conversation()
        self._post_generate(conv_id)
        with patch.dict(os.environ, {"SOULPRINT_LLM_PROVIDER": "stub"}, clear=False):
            response = self.client.get(f"/intelligence/continuity/{conv_id}")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("Summary", html)
        self.assertIn("Decisions", html)
        self.assertIn("Open Loops", html)
        self.assertIn("Entity Map", html)

    def test_derived_badge_on_continuity_page(self):
        conv_id = self._create_conversation()
        with patch.dict(os.environ, {"SOULPRINT_LLM_PROVIDER": "stub"}, clear=False):
            self.client.post(f"/intelligence/continuity/{conv_id}")
            response = self.client.get(f"/intelligence/continuity/{conv_id}")

        html = response.get_data(as_text=True)
        self.assertIn("Generated", html)

    def test_copy_payload_present(self):
        conv_id = self._create_conversation()
        self._post_generate(conv_id)
        with patch.dict(os.environ, {"SOULPRINT_LLM_PROVIDER": "stub"}, clear=False):
            response = self.client.get(f"/intelligence/continuity/{conv_id}")

        html = response.get_data(as_text=True)
        self.assertIn("Copy for New Chat", html)
        self.assertIn("copy-payload", html)

    def test_source_conversation_link(self):
        conv_id = self._create_conversation()
        with patch.dict(os.environ, {"SOULPRINT_LLM_PROVIDER": "stub"}, clear=False):
            self.client.post(f"/intelligence/continuity/{conv_id}")
            response = self.client.get(f"/intelligence/continuity/{conv_id}")

        html = response.get_data(as_text=True)
        self.assertIn(f"/imported/{conv_id}/explorer", html)

    # -- explorer button --

    def test_explorer_shows_continuity_button_when_configured(self):
        conv_id = self._create_conversation()
        with patch.dict(os.environ, {"SOULPRINT_LLM_PROVIDER": "stub"}, clear=False):
            response = self.client.get(f"/imported/{conv_id}/explorer")

        html = response.get_data(as_text=True)
        self.assertIn("Continue this thread", html)
        self.assertIn(f"/intelligence/continuity/{conv_id}", html)

    def test_explorer_hides_continuity_button_when_not_configured(self):
        conv_id = self._create_conversation()
        with patch.dict(os.environ, self._env_clean, clear=True):
            response = self.client.get(f"/imported/{conv_id}/explorer")

        html = response.get_data(as_text=True)
        self.assertNotIn("Continue this thread", html)

    # -- canonical immutability --

    def test_canonical_conversation_unchanged_after_generation(self):
        conv_id = self._create_conversation()

        with self.app.app_context():
            before_conv = ImportedConversation.query.get(conv_id)
            before_title = before_conv.title
            before_msg_count = len(before_conv.messages)

        with patch.dict(os.environ, {"SOULPRINT_LLM_PROVIDER": "stub"}, clear=False):
            self.client.post(f"/intelligence/continuity/{conv_id}")

        with self.app.app_context():
            after_conv = ImportedConversation.query.get(conv_id)
            self.assertEqual(after_conv.title, before_title)
            self.assertEqual(len(after_conv.messages), before_msg_count)


if __name__ == "__main__":
    unittest.main()
