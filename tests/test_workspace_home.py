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
        self.assertIn("Federated", html)
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
        self.assertIn('<h4 class="action-card__title">Ask your memory</h4>', html)
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

    def test_workspace_shows_action_tiles_when_only_traces_exist(self):
        """Traces alone must not gate orientation tiles — only imported conversations do.

        Guards against Codex P2 on PR #111: a user with only answer traces (or only
        native notes) and zero imported conversations should still see Start Here.
        """
        from pathlib import Path as _Path
        trace_path = _Path(self.workdir) / "answer_traces.jsonl"
        trace_path.write_text(
            json.dumps({
                "trace_id": "answer_trace:seed",
                "created_at": "2026-04-17T00:00:00+00:00",
                "question": "seed question",
                "status": "grounded",
            }) + "\n",
            encoding="utf-8",
        )
        html = self._get_workspace_html()
        self.assertIn("START HERE", html)
        self.assertIn('<h4 class="action-card__title">Ask your memory</h4>', html)
        self.assertIn("Import conversations", html)
        self.assertIn("Memory Passport", html)

    # ── Zero-count provider + connected-count field ──

    def test_zero_import_provider_appears_in_right_panel(self):
        """Providers with no imports still render in the Archive Status panel with count 0."""
        with self.app.app_context():
            self._seed_conv("chatgpt", "GPT conv")
            db.session.commit()
        html = self._get_workspace_html()
        # Grok has zero imports but must appear in the providers block.
        self.assertIn("grok", html.lower())
        # The providers block itself must be present.
        self.assertIn("PROVIDERS", html)

    def test_providers_connected_count_reflects_active_providers_only(self):
        """'N providers connected' counts only providers with imports, not zero-count entries."""
        with self.app.app_context():
            self._seed_conv("chatgpt", "GPT conv")
            self._seed_conv("claude", "Claude conv")
            db.session.commit()
        html = self._get_workspace_html()
        self.assertIn("2 providers connected", html)
        self.assertNotIn("5 providers connected", html)

    def test_providers_connected_count_all_five(self):
        """When all five providers have imports, the count reads '5 providers connected'."""
        with self.app.app_context():
            for provider in ("chatgpt", "claude", "claude_code", "gemini", "grok"):
                self._seed_conv(provider, f"{provider} conv")
            db.session.commit()
        html = self._get_workspace_html()
        self.assertIn("5 providers connected", html)


    # ── Health badge ──

    def test_workspace_renders_health_badge_when_healthy(self):
        """Healthy archive (all tables present) renders the green-dot badge."""
        html = self._get_workspace_html()
        self.assertIn("workspace-health-badge--healthy", html)
        self.assertIn("Archive available", html)

    def test_workspace_renders_needs_attention_badge_when_fts_missing(self):
        """Dropping FTS tables flips the badge to needs-attention."""
        import sqlite3 as _sqlite3

        db_uri = self.app.config["SQLALCHEMY_DATABASE_URI"]
        db_path = db_uri.removeprefix("sqlite:///")
        conn = _sqlite3.connect(db_path)
        try:
            conn.execute("DROP TABLE IF EXISTS fts_messages")
            conn.execute("DROP TABLE IF EXISTS fts_notes")
            conn.commit()
        finally:
            conn.close()

        html = self._get_workspace_html()
        self.assertIn("workspace-health-badge--needs-attention", html)
        self.assertIn("Needs attention", html)

    def test_workspace_renders_unknown_badge_when_db_missing(self):
        """Pointing the app at a nonexistent DB path renders the unknown-state badge."""
        original_uri = self.app.config["SQLALCHEMY_DATABASE_URI"]
        self.app.config["SQLALCHEMY_DATABASE_URI"] = (
            f"sqlite:///{self.workdir}/does-not-exist.db"
        )
        try:
            html = self._get_workspace_html()
        finally:
            self.app.config["SQLALCHEMY_DATABASE_URI"] = original_uri

        self.assertIn("workspace-health-badge--unknown", html)
        self.assertIn("No archive yet", html)

    def test_workspace_badge_links_to_archive_health(self):
        """The badge anchor always points to /archive/health."""
        html = self._get_workspace_html()
        self.assertIn("/archive/health", html)


if __name__ == "__main__":
    unittest.main()
