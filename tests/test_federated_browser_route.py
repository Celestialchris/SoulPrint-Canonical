"""Tests for federated browser route sort toggle and archaeology mode (CP5)."""

from __future__ import annotations

import unittest

from src.app import create_app
from src.app.models.db import db
from src.app.models import ImportedConversation, ImportedMessage
from src.config import Config
from src.retrieval.fts import rebuild_fts
from tests.temp_helpers import make_test_temp_dir, release_app_db_handles


def _seed_chronological_data(app):
    """Seed three conversations with the same keyword at distinct timestamps."""
    with app.app_context():
        for title, src_id, ts in [
            ("March archaeology conversation", "conv-mar", 1709251200.0),   # 2024-03-01
            ("June archaeology conversation", "conv-jun", 1717200000.0),    # 2024-06-01
            ("December archaeology conversation", "conv-dec", 1733011200.0),  # 2024-12-01
        ]:
            conv = ImportedConversation(
                source="chatgpt",
                source_conversation_id=src_id,
                title=title,
                created_at_unix=ts,
                updated_at_unix=ts,
            )
            db.session.add(conv)
            db.session.flush()
            db.session.add(ImportedMessage(
                conversation_id=conv.id,
                source_message_id=f"msg-{src_id}",
                role="user",
                content=f"Discussing archaeology in {title}.",
                sequence_index=0,
                created_at_unix=ts,
            ))
        db.session.commit()


class FederatedBrowserSortTest(unittest.TestCase):
    """Tests for ?sort= query param on /federated."""

    def setUp(self):
        self.tmpdir = make_test_temp_dir(self, "fed-sort-route")
        self.db_path = str(self.tmpdir / "test.db")
        self._old_uri = Config.SQLALCHEMY_DATABASE_URI
        Config.SQLALCHEMY_DATABASE_URI = f"sqlite:///{self.db_path}"
        self.app = create_app()
        self.client = self.app.test_client()
        _seed_chronological_data(self.app)
        rebuild_fts(self.db_path)
        self.addCleanup(release_app_db_handles, self.app, drop_all=True)
        self.addCleanup(self._restore_uri)

    def _restore_uri(self):
        Config.SQLALCHEMY_DATABASE_URI = self._old_uri

    def test_sort_oldest_returns_200(self):
        response = self.client.get("/federated?q=archaeology&sort=oldest")
        self.assertEqual(response.status_code, 200)

    def test_sort_oldest_orders_march_before_december(self):
        response = self.client.get("/federated?q=archaeology&sort=oldest")
        html = response.get_data(as_text=True)
        # Check within the results container only (provenance callout always shows oldest regardless of sort)
        container_start = html.find('class="container-card"')
        self.assertGreater(container_start, -1, "container-card not found")
        results_html = html[container_start:]
        march_pos = results_html.find("March archaeology")
        dec_pos = results_html.find("December archaeology")
        self.assertGreater(march_pos, -1, "March not found in results")
        self.assertGreater(dec_pos, -1, "December not found in results")
        self.assertLess(march_pos, dec_pos, "March should appear before December for oldest sort")

    def test_sort_newest_returns_200(self):
        response = self.client.get("/federated?q=archaeology&sort=newest")
        self.assertEqual(response.status_code, 200)

    def test_sort_newest_orders_december_before_march(self):
        response = self.client.get("/federated?q=archaeology&sort=newest")
        html = response.get_data(as_text=True)
        # Check within the results container only (provenance callout always shows oldest regardless of sort)
        container_start = html.find('class="container-card"')
        self.assertGreater(container_start, -1, "container-card not found")
        results_html = html[container_start:]
        march_pos = results_html.find("March archaeology")
        dec_pos = results_html.find("December archaeology")
        self.assertGreater(march_pos, -1, "March not found in results")
        self.assertGreater(dec_pos, -1, "December not found in results")
        self.assertLess(dec_pos, march_pos, "December should appear before March for newest sort")

    def test_sort_garbage_falls_back_to_relevance(self):
        response = self.client.get("/federated?q=archaeology&sort=garbage")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("Most relevant", html)
        self.assertIn('aria-current="true"', html)

    def test_sort_toggle_visible_in_normal_mode(self):
        response = self.client.get("/federated?q=archaeology")
        html = response.get_data(as_text=True)
        self.assertIn("sort-toggle", html)

    def test_sort_relevance_active_marker_present_by_default(self):
        response = self.client.get("/federated?q=archaeology")
        html = response.get_data(as_text=True)
        self.assertIn("Most relevant", html)


class FederatedBrowserArchaeologyTest(unittest.TestCase):
    """Tests for ?mode=archaeology on /federated."""

    def setUp(self):
        self.tmpdir = make_test_temp_dir(self, "fed-arch-route")
        self.db_path = str(self.tmpdir / "test.db")
        self._old_uri = Config.SQLALCHEMY_DATABASE_URI
        Config.SQLALCHEMY_DATABASE_URI = f"sqlite:///{self.db_path}"
        self.app = create_app()
        self.client = self.app.test_client()
        _seed_chronological_data(self.app)
        rebuild_fts(self.db_path)
        self.addCleanup(release_app_db_handles, self.app, drop_all=True)
        self.addCleanup(self._restore_uri)

    def _restore_uri(self):
        Config.SQLALCHEMY_DATABASE_URI = self._old_uri

    def test_archaeology_matching_returns_200(self):
        response = self.client.get("/federated?q=archaeology&mode=archaeology")
        self.assertEqual(response.status_code, 200)

    def test_archaeology_matching_renders_card(self):
        response = self.client.get("/federated?q=archaeology&mode=archaeology")
        html = response.get_data(as_text=True)
        self.assertIn("archaeology-card", html)

    def test_archaeology_matching_shows_framing_text(self):
        response = self.client.get("/federated?q=archaeology&mode=archaeology")
        html = response.get_data(as_text=True)
        self.assertIn("Your first conversation about this was", html)

    def test_archaeology_matching_shows_earliest_result(self):
        response = self.client.get("/federated?q=archaeology&mode=archaeology")
        html = response.get_data(as_text=True)
        self.assertIn("March", html)

    def test_archaeology_no_match_shows_empty_state(self):
        response = self.client.get("/federated?q=xyznonexistent&mode=archaeology")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("No earliest mention found", html)

    def test_archaeology_mode_hides_sort_toggle(self):
        response = self.client.get("/federated?q=archaeology&mode=archaeology")
        html = response.get_data(as_text=True)
        self.assertNotIn("sort-toggle", html)

    def test_archaeology_mode_hides_provenance_callout(self):
        response = self.client.get("/federated?q=archaeology&mode=archaeology")
        html = response.get_data(as_text=True)
        self.assertNotIn("provenance-callout", html)
