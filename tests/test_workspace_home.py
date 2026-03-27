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

    def test_first_run_shows_trust_block_and_cta(self):
        html = self._get_workspace_html()
        self.assertIn("SoulPrint", html)
        self.assertIn("Bring your first conversation home", html)
        self.assertIn("Nothing is sent anywhere", html)
        self.assertIn("Everything stays on your machine", html)

    def test_first_run_does_not_show_provider_stack(self):
        html = self._get_workspace_html()
        self.assertNotIn("YOUR ARCHIVE", html)
        self.assertNotIn("CONTINUITY", html)

    # ── Post-import state ──

    def test_post_import_shows_trust_oneliner(self):
        with self.app.app_context():
            self._seed_conv("chatgpt", "Test conv")
            db.session.commit()
        html = self._get_workspace_html()
        self.assertIn("Your AI memory. Always with you.", html)

    def test_post_import_shows_continuity_card_with_simplified_sentence(self):
        with self.app.app_context():
            self._seed_conv("chatgpt", "Conv1")
            self._seed_conv("claude", "Conv2")
            db.session.commit()
        html = self._get_workspace_html()
        self.assertIn("Continuity Status", html)
        self.assertIn(
            "You have 2 imported conversations across 2 providers and 0 native memory entries.",
            html,
        )
        self.assertIn("workspace-counts", html)
        self.assertIn("provider-badges", html)
        self.assertIn("chatgpt · 1", html)
        self.assertIn("claude · 1", html)
        self.assertIn("Import more conversations", html)

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

    def test_post_import_shows_browse_everything_link(self):
        with self.app.app_context():
            self._seed_conv("chatgpt", "Test")
            db.session.commit()
        html = self._get_workspace_html()
        self.assertIn("Browse everything together", html)
        self.assertIn("/federated", html)

    def test_post_import_shows_workspace_counts_and_current_sections(self):
        with self.app.app_context():
            self._seed_conv("chatgpt", "Test")
            db.session.commit()
        html = self._get_workspace_html()
        self.assertIn("workspace-counts", html)
        self.assertIn("Resume Recent Work", html)
        self.assertIn("Next Actions", html)

    def test_post_import_uses_current_surface_card_class(self):
        with self.app.app_context():
            self._seed_conv("chatgpt", "Test")
            db.session.commit()
        html = self._get_workspace_html()
        self.assertIn("surface-card", html)

    def test_post_import_provider_row_links_to_explorer(self):
        with self.app.app_context():
            conv = self._seed_conv("chatgpt", "Linked conversation")
            db.session.commit()
            conv_id = conv.id
        html = self._get_workspace_html()
        self.assertIn(f'/imported/{conv_id}/explorer', html)


if __name__ == "__main__":
    unittest.main()
