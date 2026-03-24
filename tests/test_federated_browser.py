"""Tests for federated read-only browser route."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from src.app import create_app
from src.config import Config
from src.retrieval.federated import FederatedReadResult
from tests.temp_helpers import make_test_temp_dir, release_app_db_handles


class FederatedBrowserRouteTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = make_test_temp_dir(self, "federated-browser")
        self._old_uri = Config.SQLALCHEMY_DATABASE_URI
        self.addCleanup(self._restore_sqlite_uri)
        sqlite_path = self.tmpdir / "federated_browser_test.db"
        Config.SQLALCHEMY_DATABASE_URI = f"sqlite:///{sqlite_path}"

        self.app = create_app()
        self.client = self.app.test_client()
        self.addCleanup(release_app_db_handles, self.app, drop_all=True)

    def _restore_sqlite_uri(self):
        Config.SQLALCHEMY_DATABASE_URI = self._old_uri

    def test_federated_route_renders_successfully(self):
        with patch("src.app.federated_search", return_value=[]):
            response = self.client.get("/federated")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("Everything, together", html)

    def test_no_query_federated_results_render_safely(self):
        results = [
            FederatedReadResult(
                source_lane="native_memory",
                stable_id="memory:11",
                title="<script>alert(1)</script>",
                timestamp_unix=1710000000.0,
                source_metadata={"role": "assistant", "tags": "safe"},
            )
        ]
        with patch("src.app.federated_search", return_value=results):
            response = self.client.get("/federated")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", html)
        self.assertNotIn("<script>alert(1)</script>", html)

    def test_keyword_query_is_passed_through_to_federated_search(self):
        with patch("src.app.federated_search", return_value=[]) as search_mock:
            response = self.client.get("/federated?q=travel")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(search_mock.call_count, 1)
        self.assertEqual(search_mock.call_args.kwargs["keyword"], "travel")

    def test_results_show_source_lane_and_stable_id(self):
        results = [
            FederatedReadResult(
                source_lane="imported_conversation",
                stable_id="imported_conversation:9",
                title="Lisbon planning",
                timestamp_unix=1710001000.0,
                source_metadata={"source": "chatgpt", "source_conversation_id": "abc-9"},
            )
        ]
        with patch("src.app.federated_search", return_value=results):
            response = self.client.get("/federated")

        html = response.get_data(as_text=True)
        self.assertIn("Source: imported_conversation", html)
        self.assertIn("ID: imported_conversation:9", html)

    def test_imported_conversation_handoff_link_renders_when_possible(self):
        results = [
            FederatedReadResult(
                source_lane="imported_conversation",
                stable_id="imported_conversation:42",
                title="Imported thread",
                timestamp_unix=1710002000.0,
                source_metadata={"source": "chatgpt", "source_conversation_id": "conv-42"},
            )
        ]
        with patch("src.app.federated_search", return_value=results):
            response = self.client.get("/federated")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn('href="/imported/42/explorer"', html)

    def test_native_memory_handoff_link_targets_native_detail_route(self):
        results = [
            FederatedReadResult(
                source_lane="native_memory",
                stable_id="memory:42",
                title="Native memory row",
                timestamp_unix=1710002000.0,
                source_metadata={"role": "user", "tags": "travel"},
            )
        ]
        with patch("src.app.federated_search", return_value=results):
            response = self.client.get("/federated?q=travel")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn('href="/memory/42?from=federated&amp;q=travel"', html)

    def test_empty_result_handling_is_safe(self):
        with patch("src.app.federated_search", return_value=[]):
            response = self.client.get("/federated")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("No results found.", html)


if __name__ == "__main__":
    unittest.main()
