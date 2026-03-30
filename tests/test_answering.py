"""Tests for minimal local answering on top of federated retrieval."""

from __future__ import annotations

import unittest

from src.answering.local import answer_from_federated_hits, extract_query_terms
from src.retrieval import FederatedReadResult


class AnsweringBoundaryTest(unittest.TestCase):
    def test_grounded_answer_assembly_uses_hits_and_evidence_text(self):
        hits = [
            FederatedReadResult(
                source_lane="native_memory",
                stable_id="memory:2",
                title="Lisbon restaurant shortlist",
                timestamp_unix=1710000001.0,
                source_metadata={"role": "user", "tags": "travel,food"},
            )
        ]

        result = answer_from_federated_hits("What do I have about Lisbon restaurants?", hits)

        self.assertEqual(result.status, "grounded")
        self.assertIn("memory:2", result.answer_text)
        self.assertIn("Lisbon restaurant shortlist", result.answer_text)
        self.assertIn("tags: travel,food", result.answer_text)
        self.assertEqual(len(result.citations), 1)

    def test_ambiguous_status_for_competing_top_hits(self):
        hits = [
            FederatedReadResult(
                source_lane="native_memory",
                stable_id="memory:10",
                title="Lisbon running plan",
                timestamp_unix=1710000600.0,
                source_metadata={"role": "user", "tags": "fitness"},
            ),
            FederatedReadResult(
                source_lane="native_memory",
                stable_id="memory:11",
                title="Lisbon running routes",
                timestamp_unix=1710000599.0,
                source_metadata={"role": "user", "tags": "travel"},
            ),
        ]

        result = answer_from_federated_hits("What are my Lisbon running notes?", hits)

        self.assertEqual(result.status, "ambiguous")
        self.assertIn("multiple plausible interpretations", result.answer_text)
        self.assertTrue(result.citations)

    def test_dominant_match_still_returns_grounded(self):
        hits = [
            FederatedReadResult(
                source_lane="native_memory",
                stable_id="memory:20",
                title="Lisbon restaurant budget and cuisine shortlist",
                timestamp_unix=1710000700.0,
                source_metadata={"role": "user", "tags": "travel,food"},
            ),
            FederatedReadResult(
                source_lane="imported_conversation",
                stable_id="imported_conversation:21",
                title="Lisbon packing checklist",
                timestamp_unix=1710000699.0,
                source_metadata={"source": "chatgpt", "source_conversation_id": "conv-21"},
            ),
        ]

        result = answer_from_federated_hits("Do I have Lisbon restaurant budget cuisine notes?", hits)
        self.assertEqual(result.status, "grounded")

    def test_citations_preserve_lane_id_timestamp_and_metadata(self):
        hits = [
            FederatedReadResult(
                source_lane="imported_conversation",
                stable_id="imported_conversation:7",
                title="Trip planning for Lisbon",
                timestamp_unix=1710000300.0,
                source_metadata={"source": "chatgpt", "source_conversation_id": "conv-7"},
            )
        ]

        result = answer_from_federated_hits("Show Lisbon planning", hits)

        citation = result.citations[0]
        self.assertEqual(citation.source_lane, "imported_conversation")
        self.assertEqual(citation.stable_id, "imported_conversation:7")
        self.assertEqual(citation.timestamp, "2024-03-09T16:05:00+00:00")
        self.assertEqual(citation.source_metadata["source_conversation_id"], "conv-7")

    def test_weak_retrieval_returns_insufficient_evidence(self):
        hits = [
            FederatedReadResult(
                source_lane="native_memory",
                stable_id="memory:9",
                title="Household chore reminders",
                timestamp_unix=1710000400.0,
                source_metadata={"role": "assistant", "tags": "home"},
            )
        ]

        result = answer_from_federated_hits("What did I note about Lisbon museums?", hits)

        self.assertEqual(result.status, "insufficient_evidence")
        self.assertTrue(result.citations)
        self.assertIn("limited evidence", result.answer_text)

    def test_short_or_acronym_query_terms_fallback(self):
        hits = [
            FederatedReadResult(
                source_lane="native_memory",
                stable_id="memory:3",
                title="NYC trip ideas",
                timestamp_unix=1710000500.0,
                source_metadata={"role": "user", "tags": "travel"},
            )
        ]

        self.assertEqual(extract_query_terms("NYC?") ,[])
        result = answer_from_federated_hits("NYC?", hits)

        self.assertEqual(result.status, "insufficient_evidence")
        self.assertIn("more specific question", " ".join(result.notes))

    def test_empty_retrieval_returns_safe_fallback(self):
        result = answer_from_federated_hits("Any notes about Porto?", [])

        self.assertEqual(result.status, "insufficient_evidence")
        self.assertEqual(result.citations, [])
        self.assertIn("could not find grounded evidence", result.answer_text)


class EvidenceTextIntegrationTest(unittest.TestCase):
    """Tests for evidence_text wiring from retrieval through answering."""

    def test_answering_uses_evidence_text_for_overlap_scoring(self):
        """When evidence_text is present, overlap scoring uses it instead of title."""

        hits = [
            FederatedReadResult(
                source_lane="imported_conversation",
                stable_id="imported_conversation:50",
                title="Trip planning",
                timestamp_unix=1710000001.0,
                source_metadata={"source": "chatgpt", "source_conversation_id": "conv-50"},
                evidence_text="We decided to fly into Lisbon on March 15 and stay near Alfama",
            )
        ]

        result = answer_from_federated_hits("What were my Lisbon travel plans?", hits)

        self.assertEqual(result.status, "grounded")
        self.assertIn("Lisbon", result.answer_text)
        self.assertIn("Alfama", result.answer_text)

    def test_answering_fallback_to_title_when_evidence_text_absent(self):
        """When evidence_text is None, falls back to title (no regression)."""

        hits = [
            FederatedReadResult(
                source_lane="native_memory",
                stable_id="memory:99",
                title="Lisbon restaurant shortlist with budget",
                timestamp_unix=1710000001.0,
                source_metadata={"role": "user", "tags": "travel,food"},
            )
        ]

        result = answer_from_federated_hits("What do I have about Lisbon restaurants?", hits)

        self.assertEqual(result.status, "grounded")
        self.assertIn("Lisbon restaurant shortlist", result.answer_text)
        self.assertIn("tags: travel,food", result.answer_text)

    def test_citation_includes_evidence_text(self):
        """Citation objects carry evidence_text when present on hit."""

        hits = [
            FederatedReadResult(
                source_lane="imported_conversation",
                stable_id="imported_conversation:60",
                title="Portugal research",
                timestamp_unix=1710000002.0,
                source_metadata={"source": "claude", "source_conversation_id": "conv-60"},
                evidence_text="The best time to visit Lisbon is spring, especially March-May",
            )
        ]

        result = answer_from_federated_hits("When should I visit Lisbon?", hits)

        self.assertEqual(len(result.citations), 1)
        citation = result.citations[0]
        self.assertEqual(citation.evidence_text, "The best time to visit Lisbon is spring, especially March-May")
        self.assertEqual(citation.stable_id, "imported_conversation:60")

    def test_citation_evidence_text_is_none_when_absent(self):
        """Citation evidence_text is None when hit has no evidence_text."""

        hits = [
            FederatedReadResult(
                source_lane="native_memory",
                stable_id="memory:70",
                title="Lisbon packing checklist items",
                timestamp_unix=1710000003.0,
                source_metadata={"role": "user", "tags": "travel"},
            )
        ]

        result = answer_from_federated_hits("What about Lisbon packing?", hits)

        self.assertEqual(len(result.citations), 1)
        self.assertIsNone(result.citations[0].evidence_text)

    def test_evidence_summary_with_evidence_text_quotes_content(self):
        """Evidence summary uses quoted evidence_text with title attribution."""

        from src.answering.local import _evidence_summary_for_hit

        hit = FederatedReadResult(
            source_lane="imported_conversation",
            stable_id="imported_conversation:80",
            title="Travel plans",
            timestamp_unix=1710000004.0,
            source_metadata={"source": "chatgpt", "source_conversation_id": "conv-80"},
            evidence_text="Fly into Lisbon on March 15",
        )

        summary = _evidence_summary_for_hit(hit)

        self.assertIn('"Fly into Lisbon on March 15"', summary)
        self.assertIn("Travel plans", summary)
        self.assertIn("chatgpt", summary)

    def test_evidence_summary_truncates_long_evidence(self):
        """Evidence text longer than 200 chars is truncated with ellipsis."""

        from src.answering.local import _evidence_summary_for_hit

        long_text = "A" * 250

        hit = FederatedReadResult(
            source_lane="imported_conversation",
            stable_id="imported_conversation:81",
            title="Long conversation",
            timestamp_unix=1710000005.0,
            source_metadata={"source": "claude", "source_conversation_id": "conv-81"},
            evidence_text=long_text,
        )

        summary = _evidence_summary_for_hit(hit)

        self.assertIn("\u2026", summary)
        self.assertNotIn("A" * 250, summary)

    def test_trace_records_evidence_text(self):
        """Answer trace JSONL includes evidence_text in citations."""

        from dataclasses import asdict
        from src.answering.trace import create_answer_trace

        hits = [
            FederatedReadResult(
                source_lane="imported_conversation",
                stable_id="imported_conversation:90",
                title="Trip planning",
                timestamp_unix=1710000006.0,
                source_metadata={"source": "chatgpt", "source_conversation_id": "conv-90"},
                evidence_text="We decided to fly into Lisbon on March 15",
            )
        ]

        answer = answer_from_federated_hits("Lisbon travel plans?", hits)
        trace = create_answer_trace(
            question="Lisbon travel plans?",
            retrieval_terms="lisbon travel plans",
            answer=answer,
        )

        self.assertEqual(len(trace.citations), 1)
        self.assertEqual(
            trace.citations[0]["evidence_text"],
            "We decided to fly into Lisbon on March 15",
        )

    def test_trace_records_none_evidence_when_absent(self):
        """Trace citations have evidence_text=None when hit lacks it."""

        from src.answering.trace import create_answer_trace

        hits = [
            FederatedReadResult(
                source_lane="native_memory",
                stable_id="memory:91",
                title="Lisbon restaurant budget notes",
                timestamp_unix=1710000007.0,
                source_metadata={"role": "user", "tags": "food"},
            )
        ]

        answer = answer_from_federated_hits("Lisbon restaurant budget?", hits)
        trace = create_answer_trace(
            question="Lisbon restaurant budget?",
            retrieval_terms="lisbon restaurant budget",
            answer=answer,
        )

        self.assertEqual(len(trace.citations), 1)
        self.assertIsNone(trace.citations[0]["evidence_text"])


if __name__ == "__main__":
    unittest.main()
