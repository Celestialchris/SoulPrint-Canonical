"""Tests for read-only web Answer Trace inspection surfaces."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.answering.local import AnswerCitation, GroundedAnswer
from src.answering.trace import append_answer_trace, create_answer_trace
from src.app import create_app
from src.app.models.db import db
from src.config import Config


class AnswerTraceBrowserRouteTest(unittest.TestCase):
    def setUp(self):
        self._old_uri = Config.SQLALCHEMY_DATABASE_URI
        self.tmpdir = tempfile.TemporaryDirectory()
        sqlite_path = Path(self.tmpdir.name) / "trace_browser_test.db"
        Config.SQLALCHEMY_DATABASE_URI = f"sqlite:///{sqlite_path}"

        self.app = create_app()
        self.client = self.app.test_client()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
            db.engine.dispose()
        Config.SQLALCHEMY_DATABASE_URI = self._old_uri
        self.tmpdir.cleanup()

    def _append_trace(self, *, question: str, citations: list[AnswerCitation] | None = None) -> str:
        if citations is None:
            citations = [
                AnswerCitation(
                    source_lane="native_memory",
                    stable_id="memory:7",
                    timestamp="2026-03-09T20:10:00+00:00",
                    source_metadata={"role": "assistant"},
                )
            ]

        answer = GroundedAnswer(
            answer_text="Answer text for trace.",
            status="grounded",
            citations=citations,
            notes=["note one"],
        )
        trace = create_answer_trace(
            question=question,
            retrieval_terms="lisbon memory",
            answer=answer,
        )
        append_answer_trace(Path(self.tmpdir.name) / "answer_traces.jsonl", trace)
        return trace.trace_id

    def test_answer_trace_list_route_renders(self):
        response = self.client.get("/answer-traces")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("Answer Traces", html)

    def test_answer_trace_list_safe_empty_state(self):
        response = self.client.get("/answer-traces")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("No derived Answer Traces found yet.", html)

    def test_answer_trace_detail_route_renders_fields_and_derived_label(self):
        trace_id = self._append_trace(question="What do I have about Lisbon?")

        response = self.client.get(f"/answer-traces/{trace_id}")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn(trace_id, html)
        self.assertIn("What do I have about Lisbon?", html)
        self.assertIn("lisbon memory", html)
        self.assertIn("Answer text for trace.", html)
        self.assertIn("memory:7", html)
        self.assertIn("native_memory", html)
        self.assertIn("note one", html)
        self.assertIn("Derived / non-canonical", html)

    def test_answer_trace_detail_native_memory_handoff_link_renders(self):
        trace_id = self._append_trace(
            question="Memory handoff",
            citations=[
                AnswerCitation(
                    source_lane="native_memory",
                    stable_id="memory:42",
                    timestamp="2026-03-09T20:10:00+00:00",
                    source_metadata={},
                )
            ],
        )

        response = self.client.get(f"/answer-traces/{trace_id}")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn('href="/memory/42"', html)
        self.assertIn("memory:42", html)

    def test_answer_trace_detail_imported_conversation_handoff_link_renders(self):
        trace_id = self._append_trace(
            question="Imported handoff",
            citations=[
                AnswerCitation(
                    source_lane="imported_conversation",
                    stable_id="imported_conversation:9",
                    timestamp="2026-03-09T20:10:00+00:00",
                    source_metadata={},
                )
            ],
        )

        response = self.client.get(f"/answer-traces/{trace_id}")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn('href="/imported/9/explorer"', html)
        self.assertIn("imported_conversation:9", html)

    def test_answer_trace_detail_unmapped_citation_is_plain_text(self):
        trace_id = self._append_trace(
            question="Unmapped citation",
            citations=[
                AnswerCitation(
                    source_lane="federated_external",
                    stable_id="web:abc123",
                    timestamp="2026-03-09T20:10:00+00:00",
                    source_metadata={},
                )
            ],
        )

        response = self.client.get(f"/answer-traces/{trace_id}")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("web:abc123", html)
        self.assertIn("no direct handoff view yet", html)
        self.assertNotIn('href="/memory/', html)
        self.assertNotIn('href="/imported/', html)

    def test_answer_trace_detail_malformed_stable_id_is_plain_text(self):
        trace_id = self._append_trace(
            question="Malformed stable id",
            citations=[
                AnswerCitation(
                    source_lane="native_memory",
                    stable_id="memory:not-a-number",
                    timestamp="2026-03-09T20:10:00+00:00",
                    source_metadata={},
                )
            ],
        )

        response = self.client.get(f"/answer-traces/{trace_id}")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("memory:not-a-number", html)
        self.assertIn("no direct handoff view yet", html)
        self.assertNotIn('href="/memory/not-a-number"', html)

    def test_answer_trace_detail_renders_when_citations_are_absent(self):
        trace_id = self._append_trace(question="No citations", citations=[])

        response = self.client.get(f"/answer-traces/{trace_id}")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("No citations captured.", html)

    def test_answer_trace_detail_missing_trace_returns_404(self):
        response = self.client.get("/answer-traces/answer_trace:missing")

        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
