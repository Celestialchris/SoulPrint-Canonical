"""Tests for imported conversation transcript explorer route."""

from __future__ import annotations

import unittest

from src.app import create_app
from src.app.models import ImportedConversation, ImportedMessage
from src.app.models.db import db
from src.config import Config
from tests.temp_helpers import make_test_temp_dir, release_app_db_handles


class ImportedExplorerRouteTest(unittest.TestCase):
    def setUp(self):
        self.workdir = make_test_temp_dir(self, "imported-explorer")
        self._old_uri = Config.SQLALCHEMY_DATABASE_URI
        self.addCleanup(self._restore_sqlite_uri)
        sqlite_path = self.workdir / "explorer_test.db"
        Config.SQLALCHEMY_DATABASE_URI = f"sqlite:///{sqlite_path}"

        self.app = create_app()
        self.client = self.app.test_client()
        self.addCleanup(release_app_db_handles, self.app, drop_all=True)

    def _restore_sqlite_uri(self):
        Config.SQLALCHEMY_DATABASE_URI = self._old_uri

    def _create_conversation_with_messages(self) -> int:
        with self.app.app_context():
            conversation = ImportedConversation(
                source="chatgpt",
                source_conversation_id="conv-explorer-1",
                title="Explorer test conversation",
                created_at_unix=1710000000.0,
                updated_at_unix=1710000500.0,
            )
            db.session.add(conversation)
            db.session.flush()

            db.session.add_all(
                [
                    ImportedMessage(
                        conversation_id=conversation.id,
                        source_message_id="assistant-early",
                        role="assistant",
                        content="Second chronologically.",
                        sequence_index=1,
                        created_at_unix=1710000002.0,
                    ),
                    ImportedMessage(
                        conversation_id=conversation.id,
                        source_message_id="user-first",
                        role="user",
                        content="First prompt asks for a summary of Lisbon highlights.",
                        sequence_index=0,
                        created_at_unix=1710000001.0,
                    ),
                    ImportedMessage(
                        conversation_id=conversation.id,
                        source_message_id="user-third",
                        role="user",
                        content="Third prompt asks to add food recommendations.",
                        sequence_index=2,
                        created_at_unix=1710000003.0,
                    ),
                ]
            )
            db.session.commit()
            return conversation.id

    def test_imported_explorer_route_renders_and_keeps_canonical_order(self):
        conversation_id = self._create_conversation_with_messages()

        response = self.client.get(f"/imported/{conversation_id}/explorer")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)

        first_index = html.index("#0 · user")
        second_index = html.index("#1 · assistant")
        third_index = html.index("#2 · user")
        self.assertLess(first_index, second_index)
        self.assertLess(second_index, third_index)

    def test_imported_explorer_toc_uses_user_turns_only(self):
        conversation_id = self._create_conversation_with_messages()

        response = self.client.get(f"/imported/{conversation_id}/explorer")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("Prompt TOC", html)
        self.assertIn("[0] First prompt asks for a summary of Lisbon highlights.", html)
        self.assertIn("[2] Third prompt asks to add food recommendations.", html)
        self.assertNotIn("[1]", html)


    def test_imported_explorer_falls_back_for_blank_title(self):
        with self.app.app_context():
            conversation = ImportedConversation(
                source="chatgpt",
                source_conversation_id="conv-no-title",
                title="   ",
                created_at_unix=None,
                updated_at_unix=None,
            )
            db.session.add(conversation)
            db.session.commit()
            conversation_id = conversation.id

        response = self.client.get(f"/imported/{conversation_id}/explorer")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("<title>Untitled conversation · Transcript Explorer</title>", html)
        self.assertIn('<h1 class="main-header__title">Untitled conversation</h1>', html)
        self.assertEqual(html.count("<title>"), 1)
        self.assertEqual(html.count("<h1"), 1)

    def test_imported_explorer_missing_conversation_returns_404(self):
        response = self.client.get("/imported/9999/explorer")
        self.assertEqual(response.status_code, 404)

    def test_imported_explorer_empty_conversation_is_safe(self):
        with self.app.app_context():
            conversation = ImportedConversation(
                source="chatgpt",
                source_conversation_id="conv-empty-1",
                title="Empty conversation",
                created_at_unix=None,
                updated_at_unix=None,
            )
            db.session.add(conversation)
            db.session.commit()
            conversation_id = conversation.id

        response = self.client.get(f"/imported/{conversation_id}/explorer")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("This imported conversation has no messages.", html)
        self.assertIn("No user prompts available.", html)

    def test_export_link_has_no_download_attribute(self):
        """The Export as markdown link must NOT carry a `download` attribute.

        The route conditionally returns a redirect (SOULPRINT_EXPORT_DIR set)
        or a Content-Disposition: attachment response (fallback). Browsers
        that honor `download` on the <a> tag will try to save the redirect
        target as a file — users see the /imported HTML page land in their
        downloads folder instead of seeing the session notice. The link-side
        attribute is both redundant (the header does the work when needed)
        and actively harmful in redirect mode.
        """
        import re

        conversation_id = self._create_conversation_with_messages()

        response = self.client.get(f"/imported/{conversation_id}/explorer")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)

        match = re.search(
            rf'<a\s[^>]*href="/imported/{conversation_id}/export"[^>]*>',
            html,
        )
        self.assertIsNotNone(match, "export link not found on explorer page")
        self.assertNotIn(
            "download",
            match.group(0),
            f"export link must not have `download` attribute: {match.group(0)!r}",
        )

    def test_imported_explorer_shows_provider_identity_for_non_chatgpt_source(self):
        with self.app.app_context():
            conversation = ImportedConversation(
                source="claude",
                source_conversation_id="claude-conv-explorer-1",
                title="Claude explorer conversation",
                created_at_unix=1710000000.0,
                updated_at_unix=1710000500.0,
            )
            db.session.add(conversation)
            db.session.flush()
            db.session.add(
                ImportedMessage(
                    conversation_id=conversation.id,
                    source_message_id="claude-msg-1",
                    role="user",
                    content="Provider label check.",
                    sequence_index=0,
                    created_at_unix=1710000001.0,
                )
            )
            db.session.commit()
            conversation_id = conversation.id

        response = self.client.get(f"/imported/{conversation_id}/explorer")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("Provider: claude", html)
        self.assertIn("Source Conversation ID: claude-conv-explorer-1", html)


if __name__ == "__main__":
    unittest.main()
