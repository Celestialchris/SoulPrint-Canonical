"""Route tests for Phase 7.2 intelligence features (topics + digests)."""

from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from src.app import create_app
from src.app.models import ImportedConversation, ImportedMessage
from src.app.models.db import db
from src.config import Config, sqlite_uri_from_path
from src.intelligence.digest import DerivedDigest
from src.intelligence.store import (
    append_digest,
    append_topic_scan,
    default_digest_store_path,
    default_topic_store_path,
    list_digests,
    list_topic_scans,
)
from src.intelligence.topics import TopicScan
from tests.temp_helpers import make_test_temp_dir, release_app_db_handles


class IntelligenceExtendedRouteTest(unittest.TestCase):
    def setUp(self):
        self.workdir = make_test_temp_dir(self, "intel-ext-route")
        self._old_uri = Config.SQLALCHEMY_DATABASE_URI
        self.addCleanup(self._restore_sqlite_uri)
        self.sqlite_path = self.workdir / "intel_ext_test.db"
        Config.SQLALCHEMY_DATABASE_URI = sqlite_uri_from_path(self.sqlite_path)

        self._env_clean = {
            k: v for k, v in os.environ.items()
            if not k.startswith("SOULPRINT_LLM_")
        }

        self.app = create_app()
        self.client = self.app.test_client()
        self.addCleanup(release_app_db_handles, self.app, drop_all=True)

    def _restore_sqlite_uri(self):
        Config.SQLALCHEMY_DATABASE_URI = self._old_uri

    def _seed_conversations(self):
        """Seed two conversations sharing a keyword for topic detection."""
        with self.app.app_context():
            conv1 = ImportedConversation(
                source="chatgpt",
                source_conversation_id="conv_topic_1",
                title="Python decorators guide",
                created_at_unix=1700000000.0,
                updated_at_unix=1700000300.0,
            )
            conv2 = ImportedConversation(
                source="chatgpt",
                source_conversation_id="conv_topic_2",
                title="Python testing patterns",
                created_at_unix=1700000100.0,
                updated_at_unix=1700000400.0,
            )
            db.session.add_all([conv1, conv2])
            db.session.flush()
            db.session.add(
                ImportedMessage(
                    conversation_id=conv1.id,
                    source_message_id="msg_t1",
                    role="user",
                    content="Tell me about decorators",
                    sequence_index=0,
                    created_at_unix=1700000000.0,
                )
            )
            db.session.add(
                ImportedMessage(
                    conversation_id=conv2.id,
                    source_message_id="msg_t2",
                    role="user",
                    content="Best testing frameworks",
                    sequence_index=0,
                    created_at_unix=1700000100.0,
                )
            )
            db.session.commit()
            return conv1.id, conv2.id

    # --- GET /intelligence shows sections ---

    def test_intelligence_shows_topics_section_configured(self):
        with patch.dict(os.environ, {"SOULPRINT_LLM_PROVIDER": "stub"}, clear=False):
            response = self.client.get("/intelligence")

        html = response.get_data(as_text=True)
        self.assertIn("Topics", html)
        self.assertIn("Scan topics", html)

    def test_intelligence_shows_digests_section_configured(self):
        with patch.dict(os.environ, {"SOULPRINT_LLM_PROVIDER": "stub"}, clear=False):
            response = self.client.get("/intelligence")

        html = response.get_data(as_text=True)
        self.assertIn("Digests", html)
        self.assertIn("No digests generated yet", html)

    def test_intelligence_shows_topics_empty_state(self):
        with patch.dict(os.environ, {"SOULPRINT_LLM_PROVIDER": "stub"}, clear=False):
            response = self.client.get("/intelligence")

        html = response.get_data(as_text=True)
        self.assertIn("No topic scans yet", html)

    # --- POST /intelligence/scan-topics ---

    def test_scan_topics_creates_artifact_and_redirects(self):
        self._seed_conversations()

        with patch.dict(os.environ, {"SOULPRINT_LLM_PROVIDER": "stub"}, clear=False):
            response = self.client.post("/intelligence/scan-topics")

        self.assertEqual(response.status_code, 302)
        self.assertIn("/intelligence", response.headers["Location"])

        scans = list_topic_scans(default_topic_store_path(str(self.sqlite_path)))
        self.assertEqual(len(scans), 1)
        self.assertTrue(scans[0]["scan_id"].startswith("topic_scan:"))

    def test_scan_topics_works_without_llm(self):
        """Keyword fallback should work even when no LLM is configured."""
        self._seed_conversations()

        with patch.dict(os.environ, self._env_clean, clear=True):
            response = self.client.post("/intelligence/scan-topics")

        self.assertEqual(response.status_code, 302)

        scans = list_topic_scans(default_topic_store_path(str(self.sqlite_path)))
        self.assertEqual(len(scans), 1)
        self.assertEqual(scans[0]["llm_provider_used"], "keyword_fallback")

    def test_scan_topics_with_data_shows_clusters(self):
        self._seed_conversations()

        with patch.dict(os.environ, {"SOULPRINT_LLM_PROVIDER": "stub"}, clear=False):
            self.client.post("/intelligence/scan-topics")
            response = self.client.get("/intelligence")

        html = response.get_data(as_text=True)
        # Should show the scan results (at minimum, topic section with clusters)
        self.assertIn("Topics", html)

    # --- Topic links resolve to explorers ---

    def test_topic_links_resolve_to_explorers(self):
        conv1_id, conv2_id = self._seed_conversations()

        scan = TopicScan(
            scan_id="topic_scan:link-test",
            generation_timestamp="2026-03-13T12:00:00+00:00",
            llm_provider_used="stub",
            clusters=[
                {
                    "topic_label": "Python",
                    "conversation_stable_ids": [
                        f"imported_conversation:{conv1_id}",
                        f"imported_conversation:{conv2_id}",
                    ],
                    "conversation_titles": [
                        "Python decorators guide",
                        "Python testing patterns",
                    ],
                    "confidence": "high",
                }
            ],
            conversation_count=2,
            derived_from="canonical_imported_conversations",
            artifact_kind="topic_scan_v1",
        )
        append_topic_scan(default_topic_store_path(str(self.sqlite_path)), scan)

        with patch.dict(os.environ, {"SOULPRINT_LLM_PROVIDER": "stub"}, clear=False):
            response = self.client.get("/intelligence")

        html = response.get_data(as_text=True)
        self.assertIn(f"/imported/{conv1_id}/explorer", html)
        self.assertIn(f"/imported/{conv2_id}/explorer", html)

    # --- POST /intelligence/digest/<topic_index> ---

    def test_digest_creates_artifact_and_redirects(self):
        conv1_id, conv2_id = self._seed_conversations()

        # Seed a topic scan with one cluster
        scan = TopicScan(
            scan_id="topic_scan:digest-test",
            generation_timestamp="2026-03-13T12:00:00+00:00",
            llm_provider_used="stub",
            clusters=[
                {
                    "topic_label": "Python",
                    "conversation_stable_ids": [
                        f"imported_conversation:{conv1_id}",
                        f"imported_conversation:{conv2_id}",
                    ],
                    "conversation_titles": [
                        "Python decorators guide",
                        "Python testing patterns",
                    ],
                    "confidence": "high",
                }
            ],
            conversation_count=2,
            derived_from="canonical_imported_conversations",
            artifact_kind="topic_scan_v1",
        )
        append_topic_scan(default_topic_store_path(str(self.sqlite_path)), scan)

        with patch.dict(os.environ, {"SOULPRINT_LLM_PROVIDER": "stub"}, clear=False):
            response = self.client.post("/intelligence/digest/0")

        self.assertEqual(response.status_code, 302)
        self.assertIn("/intelligence", response.headers["Location"])

        digests = list_digests(default_digest_store_path(str(self.sqlite_path)))
        self.assertEqual(len(digests), 1)
        self.assertTrue(digests[0]["digest_id"].startswith("derived_digest:"))
        self.assertEqual(digests[0]["topic_label"], "Python")

    def test_digest_provenance_shows_source_conversations(self):
        conv1_id, conv2_id = self._seed_conversations()

        digest = DerivedDigest(
            digest_id="derived_digest:prov-test",
            topic_label="Python",
            source_conversation_stable_ids=[
                f"imported_conversation:{conv1_id}",
                f"imported_conversation:{conv2_id}",
            ],
            source_conversation_titles=[
                "Python decorators guide",
                "Python testing patterns",
            ],
            generation_timestamp="2026-03-13T12:00:00+00:00",
            llm_provider_used="stub",
            prompt_template_version="v1",
            digest_text="A digest about Python.",
            derived_from="canonical_imported_conversations",
            artifact_kind="derived_digest_v1",
        )
        append_digest(default_digest_store_path(str(self.sqlite_path)), digest)

        with patch.dict(os.environ, {"SOULPRINT_LLM_PROVIDER": "stub"}, clear=False):
            response = self.client.get("/intelligence")

        html = response.get_data(as_text=True)
        self.assertIn("A digest about Python.", html)
        self.assertIn("Synthesized from 2 conversations", html)
        self.assertIn(f"/imported/{conv1_id}/explorer", html)
        self.assertIn(f"/imported/{conv2_id}/explorer", html)
        self.assertIn("Generated", html)

    def test_digest_without_llm_returns_400(self):
        """Digest requires an LLM provider."""
        self._seed_conversations()

        scan = TopicScan(
            scan_id="topic_scan:no-llm",
            generation_timestamp="2026-03-13T12:00:00+00:00",
            llm_provider_used="keyword_fallback",
            clusters=[
                {
                    "topic_label": "Python",
                    "conversation_stable_ids": [
                        "imported_conversation:1",
                        "imported_conversation:2",
                    ],
                    "conversation_titles": ["A", "B"],
                    "confidence": "low",
                }
            ],
            conversation_count=2,
            derived_from="canonical_imported_conversations",
            artifact_kind="topic_scan_v1",
        )
        append_topic_scan(default_topic_store_path(str(self.sqlite_path)), scan)

        with patch.dict(os.environ, self._env_clean, clear=True):
            response = self.client.post("/intelligence/digest/0")

        self.assertEqual(response.status_code, 400)

    def test_digest_invalid_index_returns_404(self):
        scan = TopicScan(
            scan_id="topic_scan:idx-test",
            generation_timestamp="2026-03-13T12:00:00+00:00",
            llm_provider_used="stub",
            clusters=[],
            conversation_count=0,
            derived_from="canonical_imported_conversations",
            artifact_kind="topic_scan_v1",
        )
        append_topic_scan(default_topic_store_path(str(self.sqlite_path)), scan)

        with patch.dict(os.environ, {"SOULPRINT_LLM_PROVIDER": "stub"}, clear=False):
            response = self.client.post("/intelligence/digest/99")

        self.assertEqual(response.status_code, 404)

    # --- Empty states ---

    def test_empty_states_render_safely(self):
        with patch.dict(os.environ, {"SOULPRINT_LLM_PROVIDER": "stub"}, clear=False):
            response = self.client.get("/intelligence")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("No summaries generated yet", html)
        self.assertIn("No topic scans yet", html)
        self.assertIn("No digests generated yet", html)

    # --- Unconfigured shows topic scan with keyword fallback ---

    def test_unconfigured_shows_topic_scan_button(self):
        with patch.dict(os.environ, self._env_clean, clear=True):
            response = self.client.get("/intelligence")

        html = response.get_data(as_text=True)
        self.assertIn("Scan topics", html)
        self.assertIn("keyword fallback", html)

    # --- Existing tests still pass (summaries unaffected) ---

    def test_summaries_section_still_works(self):
        """Phase 7.1 summaries still render in the configured state."""
        from src.intelligence.store import append_summary, default_summary_store_path
        from src.intelligence.summarizer import DerivedSummary

        store_path = default_summary_store_path(str(self.sqlite_path))
        summary = DerivedSummary(
            summary_id="derived_summary:compat-check",
            source_conversation_stable_id="imported_conversation:1",
            source_conversation_title="Compat Chat",
            generation_timestamp="2026-03-13T12:00:00+00:00",
            llm_provider_used="stub",
            prompt_template_version="v1",
            summary_text="Phase 7.1 summary still shows.",
            derived_from="canonical_imported_conversation",
            artifact_kind="derived_summary_v1",
        )
        append_summary(store_path, summary)

        with patch.dict(os.environ, {"SOULPRINT_LLM_PROVIDER": "stub"}, clear=False):
            response = self.client.get("/intelligence")

        html = response.get_data(as_text=True)
        self.assertIn("Phase 7.1 summary still shows.", html)
        self.assertIn("Compat Chat", html)


if __name__ == "__main__":
    unittest.main()
