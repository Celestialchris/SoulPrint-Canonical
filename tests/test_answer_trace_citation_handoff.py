"""Tests for Answer Trace citation handoff resolution."""

from __future__ import annotations

import unittest

from src.app.citation_handoff import (
    build_answer_trace_citation_view,
    resolve_citation_target,
)


class CitationHandoffResolutionTest(unittest.TestCase):
    def test_resolve_native_memory_citation(self):
        target = resolve_citation_target(
            {
                "source_lane": "native_memory",
                "stable_id": "memory:42",
            }
        )

        self.assertIsNotNone(target)
        assert target is not None
        self.assertEqual(target.label, "memory:42")
        self.assertEqual(target.href, "/memory/42")
        self.assertEqual(target.lane, "native_memory")
        self.assertEqual(target.stable_id, "memory:42")

    def test_resolve_imported_conversation_citation(self):
        target = resolve_citation_target(
            {
                "source_lane": "imported_conversation",
                "stable_id": "imported_conversation:9",
            }
        )

        self.assertIsNotNone(target)
        assert target is not None
        self.assertEqual(target.label, "imported_conversation:9")
        self.assertEqual(target.href, "/imported/9/explorer")
        self.assertEqual(target.lane, "imported_conversation")
        self.assertEqual(target.stable_id, "imported_conversation:9")

    def test_resolve_unknown_citation_returns_none(self):
        target = resolve_citation_target(
            {
                "source_lane": "federated_external",
                "stable_id": "web:abc123",
            }
        )

        self.assertIsNone(target)

    def test_build_view_model_keeps_unmapped_citation_visible(self):
        citation = build_answer_trace_citation_view(
            {
                "source_lane": "federated_external",
                "stable_id": "web:abc123",
                "timestamp": "2026-03-09T20:10:00+00:00",
            }
        )

        self.assertEqual(citation.source_lane, "federated_external")
        self.assertEqual(citation.stable_id, "web:abc123")
        self.assertEqual(citation.timestamp, "2026-03-09T20:10:00+00:00")
        self.assertIsNone(citation.target)


if __name__ == "__main__":
    unittest.main()
