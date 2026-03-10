"""Route tests for Answer Trace citation handoff surfaces."""

from __future__ import annotations

import shutil
import unittest
import uuid
from pathlib import Path

from src.answering.local import AnswerCitation, GroundedAnswer
from src.answering.trace import append_answer_trace, create_answer_trace
from src.app import create_app
from src.app.models.db import db
from src.config import Config, sqlite_uri_from_path


class AnswerTraceHandoffRouteTest(unittest.TestCase):
    def setUp(self):
        self._old_uri = Config.SQLALCHEMY_DATABASE_URI
        self.workdir = Path.cwd() / ".tmp" / f"answer-trace-route-{uuid.uuid4().hex}"
        self.workdir.mkdir(parents=True, exist_ok=True)
        self.sqlite_path = self.workdir / "trace_browser_test.db"
        Config.SQLALCHEMY_DATABASE_URI = sqlite_uri_from_path(self.sqlite_path)

        self.app = create_app()
        self.client = self.app.test_client()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
            db.engine.dispose()
        Config.SQLALCHEMY_DATABASE_URI = self._old_uri
        shutil.rmtree(self.workdir, ignore_errors=True)

    def _append_trace(self, *, citations: list[AnswerCitation]) -> str:
        answer = GroundedAnswer(
            answer_text="Answer text for trace.",
            status="grounded",
            citations=citations,
            notes=["note one"],
        )
        trace = create_answer_trace(
            question="Trace handoff",
            retrieval_terms="trace handoff",
            answer=answer,
        )
        append_answer_trace(self.workdir / "answer_traces.jsonl", trace)
        return trace.trace_id

    def test_trace_detail_renders_clickable_links_for_mapped_citations(self):
        trace_id = self._append_trace(
            citations=[
                AnswerCitation(
                    source_lane="native_memory",
                    stable_id="memory:42",
                    timestamp="2026-03-09T20:10:00+00:00",
                    source_metadata={},
                ),
                AnswerCitation(
                    source_lane="imported_conversation",
                    stable_id="imported_conversation:9",
                    timestamp="2026-03-09T20:10:00+00:00",
                    source_metadata={},
                ),
            ]
        )

        response = self.client.get(f"/answer-traces/{trace_id}")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn('href="/memory/42"', html)
        self.assertIn('href="/imported/9/explorer"', html)
        self.assertIn("memory:42", html)
        self.assertIn("imported_conversation:9", html)

    def test_trace_detail_keeps_unmapped_citation_as_plain_text(self):
        trace_id = self._append_trace(
            citations=[
                AnswerCitation(
                    source_lane="federated_external",
                    stable_id="web:abc123",
                    timestamp="2026-03-09T20:10:00+00:00",
                    source_metadata={},
                )
            ]
        )

        response = self.client.get(f"/answer-traces/{trace_id}")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("web:abc123", html)
        self.assertIn("no direct handoff view yet", html)
        self.assertNotIn('href="/memory/', html)
        self.assertNotIn('href="/imported/', html)


if __name__ == "__main__":
    unittest.main()
