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


if __name__ == "__main__":
    unittest.main()
