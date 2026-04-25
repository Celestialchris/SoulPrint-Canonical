"""Route tests for the aggregate Open Loops command center."""

from __future__ import annotations

import json
import unittest

from src.app import create_app
from src.app.models import ImportedConversation
from src.app.models.db import db
from src.config import Config, sqlite_uri_from_path
from src.intelligence.continuity.store import default_continuity_store_path
from tests.temp_helpers import make_test_temp_dir, release_app_db_handles


class OpenLoopsRouteTest(unittest.TestCase):

    def setUp(self):
        self.workdir = make_test_temp_dir(self, "open-loops-route")
        self._old_uri = Config.SQLALCHEMY_DATABASE_URI
        self.addCleanup(self._restore_sqlite_uri)
        self.sqlite_path = self.workdir / "open_loops_test.db"
        Config.SQLALCHEMY_DATABASE_URI = sqlite_uri_from_path(self.sqlite_path)
        self.app = create_app()
        self.client = self.app.test_client()
        self.addCleanup(release_app_db_handles, self.app, drop_all=True)

    def _restore_sqlite_uri(self):
        Config.SQLALCHEMY_DATABASE_URI = self._old_uri

    def _create_conversation(self, title: str = "Test Chat", source: str = "chatgpt") -> int:
        with self.app.app_context():
            conv = ImportedConversation(
                source=source,
                source_conversation_id=f"conv_{title.lower().replace(' ', '_')}",
                title=title,
                created_at_unix=1700000000.0,
                updated_at_unix=1700000300.0,
            )
            db.session.add(conv)
            db.session.commit()
            return conv.id

    def _write_artifact(self, artifact_dict: dict) -> None:
        """Write a raw artifact dict directly to the JSONL store."""
        store_path = default_continuity_store_path(str(self.sqlite_path))
        with open(store_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(artifact_dict) + "\n")

    def _make_artifact(
        self,
        *,
        conv_id: int,
        loops: list[str] | None = None,
        content_text: str | None = None,
        artifact_id: str = "continuity_artifact:test-1",
    ) -> dict:
        return {
            "artifact_id": artifact_id,
            "artifact_type": "open_loops",
            "source_conversation_ids": [f"imported_conversation:{conv_id}"],
            "generation_timestamp": "2026-04-25T12:00:00+00:00",
            "llm_provider_used": "stub",
            "prompt_template_version": "v1",
            "content_text": content_text or ("- " + "\n- ".join(loops or ["Default loop"])),
            "content_json": {"open_loops": loops} if loops is not None else None,
            "artifact_kind": "continuity_artifact_v1",
        }

    # --- empty state ---

    def test_empty_store_returns_200_and_empty_state(self):
        response = self.client.get("/continuity/open-loops")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("No open loops yet", html)

    # --- populated rows ---

    def test_two_conversations_render_titles_and_loop_texts(self):
        id1 = self._create_conversation("Job Decision Chat")
        id2 = self._create_conversation("Novel Planning")
        self._write_artifact(self._make_artifact(
            conv_id=id1,
            loops=["Decide about the freelance project"],
            artifact_id="continuity_artifact:a1",
        ))
        self._write_artifact(self._make_artifact(
            conv_id=id2,
            loops=["Finish chapter 3"],
            artifact_id="continuity_artifact:a2",
        ))

        response = self.client.get("/continuity/open-loops")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)

        self.assertIn("Job Decision Chat", html)
        self.assertIn("Novel Planning", html)
        self.assertIn("Decide about the freelance project", html)
        self.assertIn("Finish chapter 3", html)

    def test_rows_link_to_explorer_and_continuity(self):
        conv_id = self._create_conversation("Work Chat")
        self._write_artifact(self._make_artifact(
            conv_id=conv_id,
            loops=["Follow up on promotion"],
        ))

        response = self.client.get("/continuity/open-loops")
        html = response.get_data(as_text=True)

        self.assertIn(f"/imported/{conv_id}/explorer", html)
        self.assertIn(f"/intelligence/continuity/{conv_id}", html)

    # --- content_text fallback ---

    def test_artifact_without_content_json_falls_back_to_content_text(self):
        conv_id = self._create_conversation("Fallback Test")
        self._write_artifact(self._make_artifact(
            conv_id=conv_id,
            loops=None,
            content_text="- Loop from text only\n- Second loop from text",
        ))

        response = self.client.get("/continuity/open-loops")
        html = response.get_data(as_text=True)

        self.assertIn("Loop from text only", html)
        self.assertIn("Second loop from text", html)

    # --- missing / unsupported stable IDs ---

    def test_unknown_stable_id_does_not_crash(self):
        """Artifact references a conv_id that doesn't exist in the DB."""
        artifact = {
            "artifact_id": "continuity_artifact:orphan",
            "artifact_type": "open_loops",
            "source_conversation_ids": ["imported_conversation:99999"],
            "generation_timestamp": "2026-04-25T12:00:00+00:00",
            "llm_provider_used": "stub",
            "prompt_template_version": "v1",
            "content_text": "- Orphaned loop",
            "content_json": None,
            "artifact_kind": "continuity_artifact_v1",
        }
        self._write_artifact(artifact)

        response = self.client.get("/continuity/open-loops")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("Orphaned loop", html)

    def test_unsupported_stable_id_format_does_not_crash(self):
        """Artifact has a stable ID that is not in the imported_conversation: format."""
        artifact = {
            "artifact_id": "continuity_artifact:weird",
            "artifact_type": "open_loops",
            "source_conversation_ids": ["some_other_format:abc"],
            "generation_timestamp": "2026-04-25T12:00:00+00:00",
            "llm_provider_used": "stub",
            "prompt_template_version": "v1",
            "content_text": "- Loop with unsupported stable ID",
            "content_json": None,
            "artifact_kind": "continuity_artifact_v1",
        }
        self._write_artifact(artifact)

        response = self.client.get("/continuity/open-loops")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("Loop with unsupported stable ID", html)

    # --- sidebar ---

    def test_sidebar_contains_open_loops_link(self):
        response = self.client.get("/continuity/open-loops")
        html = response.get_data(as_text=True)
        self.assertIn("/continuity/open-loops", html)
        self.assertIn("Open loops", html)


if __name__ == "__main__":
    unittest.main()
