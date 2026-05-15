"""Tests for the /library route — the relocated workspace/archive surface.

B4 moves the historical `home()` view from `/` to `/library`. These tests
prove the workspace/archive content is reachable at its new path and that
the sidebar marks the Library nav item active when the user is there.
"""

from __future__ import annotations

import unittest

from src.app import create_app
from src.app.models import ImportedConversation
from src.app.models.db import db
from src.config import Config
from tests.temp_helpers import make_test_temp_dir, release_app_db_handles


class LibraryRouteTest(unittest.TestCase):
    def setUp(self):
        self.workdir = make_test_temp_dir(self, "library-route")
        self._old_uri = Config.SQLALCHEMY_DATABASE_URI
        Config.SQLALCHEMY_DATABASE_URI = f"sqlite:///{self.workdir}/test.db"
        self.addCleanup(self._restore_sqlite_uri)
        self.app = create_app()
        self.client = self.app.test_client()
        self.addCleanup(release_app_db_handles, self.app, drop_all=True)

    def _restore_sqlite_uri(self):
        Config.SQLALCHEMY_DATABASE_URI = self._old_uri

    def _seed_conv(self, source: str, title: str = "Test") -> ImportedConversation:
        conv = ImportedConversation(
            source=source,
            source_conversation_id=f"{source}-{title}-{id(object())}",
            title=title,
        )
        db.session.add(conv)
        db.session.flush()
        return conv

    def test_library_returns_200(self):
        response = self.client.get("/library")
        self.assertEqual(response.status_code, 200)

    def test_library_renders_workspace_search_hero(self):
        response = self.client.get("/library")
        html = response.get_data(as_text=True)
        self.assertIn("workspace-search-hero", html)
        self.assertIn("Search across all your conversations", html)

    def test_library_first_run_shows_bring_home_tagline(self):
        response = self.client.get("/library")
        html = response.get_data(as_text=True)
        self.assertIn("Bring your conversations home", html)
        self.assertIn("Import your ChatGPT, Claude, or Gemini history", html)

    def test_library_post_import_shows_provider_counts(self):
        with self.app.app_context():
            self._seed_conv("chatgpt", "GPT conv")
            self._seed_conv("claude", "Claude conv")
            db.session.commit()

        response = self.client.get("/library")
        html = response.get_data(as_text=True)
        self.assertIn("2 providers connected", html)
        self.assertIn("chatgpt", html.lower())
        self.assertIn("claude", html.lower())

    def test_library_sidebar_item_is_highlighted_on_library(self):
        response = self.client.get("/library")
        html = response.get_data(as_text=True)
        # The active Library nav item must carry both the active class and the label.
        self.assertIn("sidebar-item--active", html)
        # Confirm the active class sits on the Library nav anchor, not a different group.
        active_block = html[: html.find(">Library<") + len(">Library<")]
        self.assertIn("sidebar-item--active", active_block)

    def test_library_nonexistent_subpath_returns_404(self):
        response = self.client.get("/library/nonexistent-subpath")
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
