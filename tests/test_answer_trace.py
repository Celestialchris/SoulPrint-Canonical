"""Tests for derived Answer Trace audit residue."""

from __future__ import annotations

from contextlib import redirect_stdout
import json
from io import StringIO
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from src.answering import cli
from src.answering.local import GroundedAnswer
from src.answering.trace import (
    append_answer_trace,
    create_answer_trace,
    get_answer_trace,
    list_answer_traces,
)
from src.retrieval import FederatedReadResult


class AnswerTraceTest(unittest.TestCase):
    def test_create_trace_records_status_citations_and_lanes(self):
        answer = GroundedAnswer(
            answer_text="Grounded evidence... Sources: [1] memory:2 (native_memory).",
            status="grounded",
            citations=[],
            notes=[],
        )
        # use the answering boundary to produce real citations
        hits = [
            FederatedReadResult(
                source_lane="native_memory",
                stable_id="memory:2",
                title="Lisbon restaurant shortlist",
                timestamp_unix=1710000001.0,
                source_metadata={"role": "user", "tags": "travel,food"},
            )
        ]
        from src.answering.local import answer_from_federated_hits

        answer = answer_from_federated_hits("What do I have about Lisbon restaurants?", hits)
        trace = create_answer_trace(
            question="What do I have about Lisbon restaurants?",
            retrieval_terms="lisbon restaurants",
            answer=answer,
        )

        self.assertTrue(trace.trace_id.startswith("answer_trace:"))
        self.assertEqual(trace.status, "grounded")
        self.assertEqual(trace.retrieval_terms, "lisbon restaurants")
        self.assertEqual(trace.citations[0]["stable_id"], "memory:2")
        self.assertEqual(trace.source_lanes, ["native_memory"])
        self.assertEqual(trace.trace_kind, "answer_trace_derived_v1")
        self.assertEqual(trace.derived_from, "canonical_records")

    def test_insufficient_evidence_trace_carries_safe_fallback_and_empty_citations(self):
        answer = GroundedAnswer(
            answer_text="I could not find grounded evidence.",
            status="insufficient_evidence",
            citations=[],
            notes=["No federated retrieval hits were found."],
        )

        trace = create_answer_trace(
            question="Any notes about Porto?",
            retrieval_terms="porto",
            answer=answer,
        )

        self.assertEqual(trace.status, "insufficient_evidence")
        self.assertEqual(trace.citations, [])
        self.assertEqual(trace.source_lanes, [])
        self.assertEqual(trace.fallback_reason, "No federated retrieval hits were found.")

    def test_trace_store_append_list_and_get(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = Path(tmpdir) / "answer_traces.jsonl"
            answer = GroundedAnswer(
                answer_text="Grounded evidence.",
                status="grounded",
                citations=[],
                notes=[],
            )
            trace = create_answer_trace(
                question="Q1",
                retrieval_terms="q1",
                answer=answer,
            )
            append_answer_trace(store, trace)

            rows = list_answer_traces(store, limit=5)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["trace_id"], trace.trace_id)
            self.assertEqual(get_answer_trace(store, trace.trace_id)["question"], "Q1")

    def test_answering_cli_emit_trace_and_list_trace(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = Path(tmpdir) / "trace.jsonl"
            db_path = Path(tmpdir) / "test.db"

            fake_hits = [
                FederatedReadResult(
                    source_lane="native_memory",
                    stable_id="memory:1",
                    title="Lisbon food notes",
                    timestamp_unix=1710000000.0,
                    source_metadata={"role": "user", "tags": "travel"},
                )
            ]

            write_output = StringIO()
            with patch("src.answering.cli.federated_search", return_value=fake_hits):
                with patch(
                    "sys.argv",
                    [
                        "answer-cli",
                        "--db",
                        str(db_path),
                        "What did I note about Lisbon food?",
                        "--emit-trace",
                        "--trace-store",
                        str(store),
                    ],
                ):
                    with redirect_stdout(write_output):
                        exit_code = cli.main()

            self.assertEqual(exit_code, 0)
            self.assertIn("trace_id:", write_output.getvalue())

            list_output = StringIO()
            with patch("sys.argv", ["answer-cli", "--list-traces", "1", "--trace-store", str(store)]):
                with redirect_stdout(list_output):
                    list_code = cli.main()

            self.assertEqual(list_code, 0)
            trace_obj = json.loads(list_output.getvalue())
            self.assertEqual(trace_obj["question"], "What did I note about Lisbon food?")
            self.assertEqual(trace_obj["trace_kind"], "answer_trace_derived_v1")


if __name__ == "__main__":
    unittest.main()
