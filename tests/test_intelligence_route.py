"""Route tests for the intelligence / Notes surface."""

from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from src.app import create_app
from src.app.models import ImportedConversation, ImportedMessage
from src.app.models.db import db
from src.config import Config, sqlite_uri_from_path
from src.intelligence.store import append_summary, default_summary_store_path
from src.intelligence.summarizer import DerivedSummary
from tests.temp_helpers import make_test_temp_dir, release_app_db_handles


class IntelligenceRouteTest(unittest.TestCase):
    def setUp(self):
        self.workdir = make_test_temp_dir(self, "intel-route")
        self._old_uri = Config.SQLALCHEMY_DATABASE_URI
        self.addCleanup(self._restore_sqlite_uri)
        self.sqlite_path = self.workdir / "intel_route_test.db"
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

    def test_get_intelligence_unconfigured_shows_guidance(self):
        with patch.dict(os.environ, self._env_clean, clear=True):
            response = self.client.get("/intelligence")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("SOULPRINT_LLM_PROVIDER", html)
        self.assertIn("LLM provider not configured", html)

    def test_get_intelligence_configured_empty(self):
        with patch.dict(os.environ, {"SOULPRINT_LLM_PROVIDER": "stub"}, clear=False):
            response = self.client.get("/intelligence")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("No summaries generated yet", html)

    def test_get_intelligence_with_summaries(self):
        store_path = default_summary_store_path(str(self.sqlite_path))
        summary = DerivedSummary(
            summary_id="derived_summary:test-display",
            source_conversation_stable_id="imported_conversation:1",
            source_conversation_title="My Test Chat",
            generation_timestamp="2026-03-13T12:00:00+00:00",
            llm_provider_used="stub",
            prompt_template_version="v1",
            summary_text="This is a test summary for display.",
            derived_from="canonical_imported_conversation",
            artifact_kind="derived_summary_v1",
        )
        append_summary(store_path, summary)

        with patch.dict(os.environ, {"SOULPRINT_LLM_PROVIDER": "stub"}, clear=False):
            response = self.client.get("/intelligence")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("This is a test summary for display.", html)
        self.assertIn("My Test Chat", html)
        self.assertIn("Generated", html)
        self.assertIn("/imported/1/explorer", html)

    def test_post_summarize_creates_artifact_and_redirects(self):
        with self.app.app_context():
            conv = ImportedConversation(
                source="chatgpt",
                source_conversation_id="conv_sum_1",
                title="Summarizable Chat",
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
                    content="Hello there",
                    sequence_index=0,
                    created_at_unix=1700000000.0,
                )
            )
            db.session.add(
                ImportedMessage(
                    conversation_id=conv.id,
                    source_message_id="msg_2",
                    role="assistant",
                    content="Hi! How can I help?",
                    sequence_index=1,
                    created_at_unix=1700000001.0,
                )
            )
            db.session.commit()
            conv_id = conv.id

        with patch.dict(os.environ, {"SOULPRINT_LLM_PROVIDER": "stub"}, clear=False):
            response = self.client.post(f"/intelligence/summarize/{conv_id}")

        self.assertEqual(response.status_code, 302)
        self.assertIn("/intelligence", response.headers["Location"])

        # Verify artifact was stored
        from src.intelligence.store import list_summaries
        store_path = default_summary_store_path(str(self.sqlite_path))
        summaries = list_summaries(store_path)
        self.assertEqual(len(summaries), 1)
        self.assertEqual(summaries[0]["source_conversation_title"], "Summarizable Chat")
        self.assertTrue(summaries[0]["summary_id"].startswith("derived_summary:"))

    def test_nav_includes_notes(self):
        with patch.dict(os.environ, self._env_clean, clear=True):
            response = self.client.get("/intelligence")

        html = response.get_data(as_text=True)
        self.assertIn("Your own notes", html)
        self.assertIn("/intelligence", html)

    def test_explorer_shows_summarize_button_when_configured(self):
        with self.app.app_context():
            conv = ImportedConversation(
                source="chatgpt",
                source_conversation_id="conv_btn_1",
                title="Button Test",
                created_at_unix=1700000000.0,
                updated_at_unix=1700000300.0,
            )
            db.session.add(conv)
            db.session.commit()
            conv_id = conv.id

        with patch.dict(os.environ, {"SOULPRINT_LLM_PROVIDER": "stub"}, clear=False):
            response = self.client.get(f"/imported/{conv_id}/explorer")

        html = response.get_data(as_text=True)
        self.assertIn("Summarize", html)
        self.assertIn(f"/intelligence/summarize/{conv_id}", html)

    def test_explorer_hides_summarize_button_when_not_configured(self):
        with self.app.app_context():
            conv = ImportedConversation(
                source="chatgpt",
                source_conversation_id="conv_btn_2",
                title="No Button Test",
                created_at_unix=1700000000.0,
                updated_at_unix=1700000300.0,
            )
            db.session.add(conv)
            db.session.commit()
            conv_id = conv.id

        with patch.dict(os.environ, self._env_clean, clear=True):
            response = self.client.get(f"/imported/{conv_id}/explorer")

        html = response.get_data(as_text=True)
        self.assertNotIn("Summarize", html)

    def test_derived_badge_visible_on_intelligence_page(self):
        with patch.dict(os.environ, {"SOULPRINT_LLM_PROVIDER": "stub"}, clear=False):
            response = self.client.get("/intelligence")

        html = response.get_data(as_text=True)
        self.assertIn("Generated", html)


if __name__ == "__main__":
    unittest.main()
