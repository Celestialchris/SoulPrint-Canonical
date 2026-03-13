"""Tests for intelligence JSONL summary store."""

from __future__ import annotations

import unittest

from src.intelligence.store import append_summary, get_summary, list_summaries
from src.intelligence.summarizer import DerivedSummary
from tests.temp_helpers import make_test_temp_dir


def _make_summary(summary_id: str = "derived_summary:test-001", title: str = "Test") -> DerivedSummary:
    return DerivedSummary(
        summary_id=summary_id,
        source_conversation_stable_id="imported_conversation:1",
        source_conversation_title=title,
        generation_timestamp="2026-03-13T12:00:00+00:00",
        llm_provider_used="stub",
        prompt_template_version="v1",
        summary_text="A test summary.",
        derived_from="canonical_imported_conversation",
        artifact_kind="derived_summary_v1",
    )


class SummaryStoreTest(unittest.TestCase):
    def setUp(self):
        self.workdir = make_test_temp_dir(self, "intel-store")
        self.store_path = self.workdir / "derived_summaries.jsonl"

    def test_empty_store_returns_empty_list(self):
        result = list_summaries(self.store_path)
        self.assertEqual(result, [])

    def test_append_and_list_round_trip(self):
        summary = _make_summary()
        append_summary(self.store_path, summary)

        results = list_summaries(self.store_path)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["summary_id"], "derived_summary:test-001")

    def test_get_existing_summary(self):
        summary = _make_summary()
        append_summary(self.store_path, summary)

        result = get_summary(self.store_path, "derived_summary:test-001")
        self.assertIsNotNone(result)
        self.assertEqual(result["summary_text"], "A test summary.")

    def test_get_nonexistent_returns_none(self):
        summary = _make_summary()
        append_summary(self.store_path, summary)

        result = get_summary(self.store_path, "derived_summary:nonexistent")
        self.assertIsNone(result)

    def test_get_from_missing_file_returns_none(self):
        result = get_summary(self.store_path, "derived_summary:any")
        self.assertIsNone(result)

    def test_list_returns_newest_first(self):
        append_summary(self.store_path, _make_summary("derived_summary:a", "First"))
        append_summary(self.store_path, _make_summary("derived_summary:b", "Second"))

        results = list_summaries(self.store_path)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["summary_id"], "derived_summary:b")
        self.assertEqual(results[1]["summary_id"], "derived_summary:a")


if __name__ == "__main__":
    unittest.main()
