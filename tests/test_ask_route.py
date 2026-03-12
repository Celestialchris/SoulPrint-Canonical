"""Route tests for the in-app Ask surface."""

from __future__ import annotations

import unittest
from datetime import datetime
from unittest.mock import patch

from src.answering.local import AnswerCitation, GroundedAnswer
from src.answering.trace import default_trace_store_path, list_answer_traces
from src.app import create_app
from src.app.models import ImportedConversation, MemoryEntry
from src.app.models.db import db
from src.config import Config, sqlite_uri_from_path
from tests.temp_helpers import make_test_temp_dir, release_app_db_handles


class AskRouteTest(unittest.TestCase):
    def setUp(self):
        self.workdir = make_test_temp_dir(self, "ask-route")
        self._old_uri = Config.SQLALCHEMY_DATABASE_URI
        self.addCleanup(self._restore_sqlite_uri)
        self.sqlite_path = self.workdir / "ask_route_test.db"
        Config.SQLALCHEMY_DATABASE_URI = sqlite_uri_from_path(self.sqlite_path)

        self.app = create_app()
        self.client = self.app.test_client()
        self.addCleanup(release_app_db_handles, self.app, drop_all=True)

    def _restore_sqlite_uri(self):
        Config.SQLALCHEMY_DATABASE_URI = self._old_uri

    def test_get_ask_route_renders_successfully(self):
        response = self.client.get("/ask")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("Ask SoulPrint", html)
        self.assertIn('name="question"', html)

    def test_submit_empty_question_shows_validation_error(self):
        response = self.client.post("/ask", data={"question": "   "})

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("Enter a question before asking.", html)

    def test_submit_valid_question_returns_answer_and_trace_and_citations(self):
        with self.app.app_context():
            memory = MemoryEntry(
                timestamp=datetime(2026, 3, 10, 9, 0, 0),
                role="user",
                content="Remember to buy apples and oats.",
                tags="shopping,food",
            )
            imported = ImportedConversation(
                source="chatgpt",
                source_conversation_id="conv_1",
                title="Trip planning and lists",
                created_at_unix=1700000000.0,
                updated_at_unix=1700000300.0,
            )
            db.session.add(memory)
            db.session.add(imported)
            db.session.commit()

        response = self.client.post("/ask", data={"question": "What did I note about apples?"})

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("Answer", html)
        self.assertIn("View full trace", html)
        self.assertIn("memory:", html)
        self.assertIn('href="/memory/', html)

        traces = list_answer_traces(default_trace_store_path(self.sqlite_path), limit=5)
        self.assertGreaterEqual(len(traces), 1)
        self.assertIn(traces[0]["status"], {"grounded", "ambiguous", "insufficient_evidence"})

    def test_answer_status_is_rendered_honestly_for_ambiguous_result(self):
        mocked = GroundedAnswer(
            answer_text="Mocked ambiguous answer.",
            status="ambiguous",
            citations=[],
            notes=["Please clarify what you meant."],
        )

        with patch("src.app.federated_search", return_value=[]), patch(
            "src.answering.local.answer_from_federated_hits", return_value=mocked
        ):
            response = self.client.post("/ask", data={"question": "roadmap review planning"})

        html = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Ambiguous", html)


    def test_imported_citation_link_renders_on_ask(self):
        mocked = GroundedAnswer(
            answer_text="Mocked answer with imported citation.",
            status="grounded",
            citations=[
                AnswerCitation(
                    source_lane="imported_conversation",
                    stable_id="imported_conversation:9",
                    timestamp="2026-03-10T09:00:00+00:00",
                    source_metadata={},
                )
            ],
            notes=[],
        )

        with patch("src.app.federated_search", return_value=[]), patch(
            "src.answering.local.answer_from_federated_hits", return_value=mocked
        ):
            response = self.client.post("/ask", data={"question": "trip planning"})

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn('href="/imported/9/explorer"', html)
        self.assertIn("imported_conversation:9", html)

    def test_unmapped_citation_stays_plain_text_on_ask(self):
        mocked = GroundedAnswer(
            answer_text="Mocked answer with unmapped citation.",
            status="insufficient_evidence",
            citations=[
                AnswerCitation(
                    source_lane="external",
                    stable_id="web:abc123",
                    timestamp="2026-03-10T09:00:00+00:00",
                    source_metadata={},
                )
            ],
            notes=["Try adding a local keyword."],
        )

        with patch("src.app.federated_search", return_value=[]), patch(
            "src.answering.local.answer_from_federated_hits", return_value=mocked
        ):
            response = self.client.post("/ask", data={"question": "external clue"})

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("web:abc123", html)
        self.assertIn("no direct handoff view yet", html)
        self.assertNotIn('href="/memory/', html)
        self.assertNotIn('href="/imported/', html)

    def test_insufficient_evidence_path_renders_honestly(self):
        response = self.client.post("/ask", data={"question": "xkcd quasar nebula synapse"})

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("Insufficient evidence", html)

    def test_no_meaningful_hits_shows_honest_feedback(self):
        with patch("src.app.federated_search", return_value=[]):
            response = self.client.post("/ask", data={"question": "where is my dragonfruit log"})

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("Insufficient evidence", html)
        self.assertIn("could not find grounded evidence", html.lower())


if __name__ == "__main__":
    unittest.main()
