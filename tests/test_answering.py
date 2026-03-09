"""Tests for minimal local answering on top of federated retrieval."""

from __future__ import annotations

import unittest

from src.answering.local import answer_from_federated_hits
from src.retrieval import FederatedReadResult


class AnsweringBoundaryTest(unittest.TestCase):
    def test_grounded_answer_assembly_uses_hits(self):
        hits = [
            FederatedReadResult(
                source_lane="native_memory",
                stable_id="memory:2",
                title="Lisbon restaurant shortlist",
                timestamp_unix=1710000001.0,
                source_metadata={"role": "user", "tags": "travel"},
            )
        ]

        result = answer_from_federated_hits("What do I have about Lisbon restaurants?", hits)

        self.assertEqual(result.status, "grounded")
        self.assertIn("memory:2", result.answer_text)
        self.assertEqual(len(result.citations), 1)

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
        self.assertTrue(any("limited evidence" in result.answer_text for _ in [0]))

    def test_empty_retrieval_returns_safe_fallback(self):
        result = answer_from_federated_hits("Any notes about Porto?", [])

        self.assertEqual(result.status, "insufficient_evidence")
        self.assertEqual(result.citations, [])
        self.assertIn("could not find grounded evidence", result.answer_text)


if __name__ == "__main__":
    unittest.main()
