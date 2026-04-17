"""Tests for the redesigned workspace landing page."""

from __future__ import annotations

import json
import unittest
from datetime import datetime

from src.app import create_app
from src.app.models import ImportedConversation, ImportedMessage, MemoryEntry
from src.app.models.db import db
from src.config import Config
from tests.temp_helpers import make_test_temp_dir, release_app_db_handles


class WorkspaceHomeTest(unittest.TestCase):
    def setUp(self):
        self.workdir = make_test_temp_dir(self, "workspace-home")
        self._old_uri = Config.SQLALCHEMY_DATABASE_URI
        Config.SQLALCHEMY_DATABASE_URI = f"sqlite:///{self.workdir}/test.db"
        self.addCleanup(self._restore_sqlite_uri)
        self.app = create_app()
        self.client = self.app.test_client()
        self.addCleanup(release_app_db_handles, self.app, drop_all=True)

    def _restore_sqlite_uri(self):
        Config.SQLALCHEMY_DATABASE_URI = self._old_uri

    def _get_workspace_html(self) -> str:
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        return response.get_data(as_text=True)

    def _seed_conv(self, source: str, title: str = "Test") -> ImportedConversation:
        conv = ImportedConversation(
            source=source,
            source_conversation_id=f"{source}-{title}-{id(object())}",
            title=title,
        )
        db.session.add(conv)
        db.session.flush()
        return conv

    # ── First-run state ──

    def test_first_run_shows_tagline_and_sidebar_hint(self):
        """The first-run empty state tells the user how to get started."""
        html = self._get_workspace_html()
        self.assertIn("SoulPrint", html)
        self.assertIn("Bring your conversations home", html)
        self.assertIn("Import your ChatGPT, Claude, or Gemini history", html)

    def test_first_run_does_not_show_provider_stack(self):
        html = self._get_workspace_html()
        self.assertNotIn("YOUR ARCHIVE", html)
        self.assertNotIn("CONTINUITY", html)

    # ── Post-import state ──

    def test_post_import_shows_stats_and_provider_counts(self):
        with self.app.app_context():
            self._seed_conv("chatgpt", "Conv1")
            self._seed_conv("claude", "Conv2")
            db.session.commit()
        html = self._get_workspace_html()
        # Stats row shows conversation count and provider count labels
        self.assertIn("conversations", html.lower())
        self.assertIn("provider", html.lower())
        # Both providers appear in the provider-row list
        self.assertIn("chatgpt", html.lower())
        self.assertIn("claude", html.lower())

    def test_post_import_shows_provider_stack_with_lane_colors(self):
        with self.app.app_context():
            self._seed_conv("chatgpt", "GPT conversation")
            self._seed_conv("claude", "Claude conversation")
            db.session.commit()
        html = self._get_workspace_html()
        self.assertIn("chatgpt", html.lower())
        self.assertIn("claude", html.lower())
        self.assertIn("GPT conversation", html)
        self.assertIn("Claude conversation", html)

    def test_post_import_sidebar_contains_federated_link(self):
        """The sidebar nav always exposes the federated browser route."""
        with self.app.app_context():
            self._seed_conv("chatgpt", "Test")
            db.session.commit()
        html = self._get_workspace_html()
        self.assertIn("Everything, together", html)
        self.assertIn('href="/federated"', html)

    def test_post_import_shows_stats_grid(self):
        """The post-import state renders the four-card stats grid."""
        with self.app.app_context():
            self._seed_conv("chatgpt", "Test")
            db.session.commit()
        html = self._get_workspace_html()
        self.assertIn("conversations", html.lower())
        self.assertIn("notes", html.lower())
        self.assertIn("messages", html.lower())
        # Stats now render inline in a metadata line, not stat-card elements.
        self.assertIn("conversations imported", html)
        self.assertIn("messages indexed", html)

    def test_post_import_shows_sidebar_wordmark(self):
        """The SoulPrint wordmark is always rendered in the sidebar brand."""
        with self.app.app_context():
            self._seed_conv("chatgpt", "Test")
            db.session.commit()
        html = self._get_workspace_html()
        self.assertIn("SoulPrint", html)
        self.assertIn("sidebar-header__brand", html)

    def test_post_import_provider_row_links_to_explorer(self):
        with self.app.app_context():
            conv = self._seed_conv("chatgpt", "Linked conversation")
            db.session.commit()
            conv_id = conv.id
        html = self._get_workspace_html()
        self.assertIn(f'/imported/{conv_id}/explorer', html)

    # ── Phase 3: search-first workspace ──

    def test_workspace_search_hero_renders_before_action_tiles(self):
        """Search hero appears above the Start-here action tiles in the source order."""
        html = self._get_workspace_html()
        search_idx = html.find("workspace-search-hero")
        action_idx = html.find("workspace-actions")
        self.assertNotEqual(search_idx, -1, "search hero should render")
        self.assertNotEqual(action_idx, -1, "action tiles should render in empty state")
        self.assertLess(search_idx, action_idx, "search hero must precede action tiles")

    def test_workspace_shows_start_here_when_archive_empty(self):
        """Action tiles orient a fresh user on first run."""
        html = self._get_workspace_html()
        self.assertIn("START HERE", html)
        self.assertIn("Ask your memory", html)
        self.assertIn("Import conversations", html)
        self.assertIn("Memory Passport", html)

    def test_workspace_hides_start_here_when_archive_populated(self):
        """Action tiles are hidden once the archive has any imported conversations."""
        with self.app.app_context():
            self._seed_conv("chatgpt", "Test")
            db.session.commit()
        html = self._get_workspace_html()
        self.assertNotIn("START HERE", html)
        self.assertNotIn("action-card__title", html)

    def test_workspace_rail_omits_top_themes_and_recent_activity(self):
        """Phase 3 removes derived surfaces from the workspace rail — only Providers remains."""
        with self.app.app_context():
            self._seed_conv("chatgpt", "Test")
            db.session.commit()
        html = self._get_workspace_html()
        self.assertNotIn("TOP THEMES", html)
        self.assertNotIn("RECENT ACTIVITY", html)
        # Providers block must still render
        self.assertIn("PROVIDERS", html)


if __name__ == "__main__":
    unittest.main()
