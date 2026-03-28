"""Tests for handoff briefing formatter and file proof on passport page."""

from __future__ import annotations

import unittest

from src.app import create_app
from src.app import format_handoff_briefing
from src.config import Config
from tests.temp_helpers import make_test_temp_dir, release_app_db_handles


# ---------------------------------------------------------------------------
# Feature A — format_handoff_briefing unit tests
# ---------------------------------------------------------------------------


class FormatHandoffBriefingTest(unittest.TestCase):
    """Unit tests for the handoff briefing formatter."""

    STRUCTURED_MD = (
        "## Summary\n"
        "The project uses local-first architecture.\n"
        "Data stays on the user's machine.\n"
        "Export is non-destructive.\n"
        "Privacy is the default.\n"
        "\n"
        "## Decisions\n"
        "- Use SQLite as canonical store\n"
        "- No cloud dependency\n"
        "\n"
        "## Open Loops\n"
        "- Passport validation edge cases\n"
        "- FTS5 ranking tuning\n"
        "\n"
        "## How Thinking Evolved\n"
        "Started with cloud sync.\n\n"
        "Shifted to local-only after user research."
    )

    def test_produces_valid_markdown_header(self):
        result = format_handoff_briefing(self.STRUCTURED_MD, 5, "2 months")
        self.assertTrue(result.startswith("## Context from SoulPrint"))

    def test_contains_conversation_count_and_time_span(self):
        result = format_handoff_briefing(self.STRUCTURED_MD, 5, "2 months")
        self.assertIn("5 conversations", result)
        self.assertIn("2 months", result)

    def test_ends_with_continue_line(self):
        result = format_handoff_briefing(self.STRUCTURED_MD, 3, "1 week")
        self.assertTrue(result.rstrip().endswith("Please continue from this context."))

    def test_contains_decisions_section(self):
        result = format_handoff_briefing(self.STRUCTURED_MD, 3, "1 week")
        self.assertIn("**Decisions made:**", result)
        self.assertIn("SQLite", result)

    def test_contains_open_loops_section(self):
        result = format_handoff_briefing(self.STRUCTURED_MD, 3, "1 week")
        self.assertIn("**Open loops:**", result)
        self.assertIn("Passport validation", result)

    def test_contains_key_context_from_summary(self):
        result = format_handoff_briefing(self.STRUCTURED_MD, 3, "1 week")
        self.assertIn("**Key context:**", result)
        self.assertIn("local-first", result)

    def test_contains_where_i_left_off(self):
        result = format_handoff_briefing(self.STRUCTURED_MD, 3, "1 week")
        self.assertIn("**Where I left off:**", result)
        self.assertIn("local-only", result)

    def test_handles_missing_sections_gracefully(self):
        minimal = "Just some raw text without any headings."
        result = format_handoff_briefing(minimal, 1, "1 day")
        self.assertIn("## Context from SoulPrint", result)
        self.assertIn("1 conversations", result)
        self.assertIn("Just some raw text", result)
        self.assertTrue(result.rstrip().endswith("Please continue from this context."))

    def test_handles_none_date_range(self):
        result = format_handoff_briefing("Some text", 2, None)
        self.assertIn("an unknown period", result)


# ---------------------------------------------------------------------------
# Feature A — distill result page integration
# ---------------------------------------------------------------------------


class DistillResultCopyButtonTest(unittest.TestCase):
    """Verify distill_result.html renders the copy button with briefing."""

    def setUp(self):
        self.workdir = make_test_temp_dir(self, "handoff-briefing")
        self._old_uri = Config.SQLALCHEMY_DATABASE_URI
        self.addCleanup(self._restore_sqlite_uri)
        sqlite_path = self.workdir / "briefing_test.db"
        Config.SQLALCHEMY_DATABASE_URI = f"sqlite:///{sqlite_path}"

        self.app = create_app()
        self.client = self.app.test_client()
        self.addCleanup(release_app_db_handles, self.app, drop_all=True)

    def _restore_sqlite_uri(self):
        Config.SQLALCHEMY_DATABASE_URI = self._old_uri

    def test_distill_result_template_renders_copy_button(self):
        """Render distill_result.html directly and check for the copy button."""
        from dataclasses import dataclass

        @dataclass(frozen=True)
        class FakeResult:
            distillation_id: str = "test-001"
            source_conversation_stable_ids: list = None
            source_conversation_titles: list = None
            source_providers: list = None
            generation_timestamp: str = "2026-03-28"
            llm_provider_used: str = "test"
            prompt_template_version: str = "v1"
            distilled_text: str = "## Summary\nTest content"
            conversation_count: int = 2
            total_message_count: int = 10
            derived_from: str = "test"
            artifact_kind: str = "test"

            def __post_init__(self):
                if self.source_conversation_stable_ids is None:
                    object.__setattr__(self, 'source_conversation_stable_ids', [])
                if self.source_conversation_titles is None:
                    object.__setattr__(self, 'source_conversation_titles', [])
                if self.source_providers is None:
                    object.__setattr__(self, 'source_providers', [])

        result = FakeResult()
        briefing = format_handoff_briefing(
            result.distilled_text, result.conversation_count, "1 week"
        )

        with self.app.test_request_context():
            from flask import render_template
            html = render_template(
                "distill_result.html",
                result=result,
                source_meta=None,
                handoff_briefing=briefing,
            )

        self.assertIn("Copy handoff to clipboard", html)
        self.assertIn("Context from SoulPrint", html)


# ---------------------------------------------------------------------------
# Feature B — file proof on passport page
# ---------------------------------------------------------------------------


class FileProofOnPassportTest(unittest.TestCase):
    """Verify passport page shows the database file path."""

    def setUp(self):
        self.workdir = make_test_temp_dir(self, "file-proof")
        self._old_uri = Config.SQLALCHEMY_DATABASE_URI
        self.addCleanup(self._restore_sqlite_uri)
        sqlite_path = self.workdir / "file_proof_test.db"
        Config.SQLALCHEMY_DATABASE_URI = f"sqlite:///{sqlite_path}"

        self.app = create_app()
        self.client = self.app.test_client()
        self.addCleanup(release_app_db_handles, self.app, drop_all=True)

    def _restore_sqlite_uri(self):
        Config.SQLALCHEMY_DATABASE_URI = self._old_uri

    def test_passport_contains_your_archive_label(self):
        resp = self.client.get("/passport")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"YOUR ARCHIVE", resp.data)

    def test_passport_contains_db_path(self):
        resp = self.client.get("/passport")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"file_proof_test.db", resp.data)

    def test_passport_contains_its_yours(self):
        resp = self.client.get("/passport")
        self.assertEqual(resp.status_code, 200)
        html = resp.data.decode()
        self.assertTrue(
            "It's yours." in html or "It&#39;s yours." in html,
            "Expected 'It's yours.' in passport page",
        )


if __name__ == "__main__":
    unittest.main()
