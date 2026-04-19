"""Tests for intelligence JSONL summary store."""

from __future__ import annotations

import unittest

import json

from src.intelligence.store import (
    append_summary,
    get_summary,
    list_summaries,
    list_summaries_for_conversation,
    list_topic_scans_for_conversation,
    list_digests_for_conversation,
    list_distillations_for_conversation,
)
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


def _write_jsonl(path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")


class ListSummariesForConversationTest(unittest.TestCase):
    def setUp(self):
        self.workdir = make_test_temp_dir(self, "list-summaries-conv")
        self.store = self.workdir / "derived_summaries.jsonl"

    def test_returns_only_matching_row(self):
        _write_jsonl(self.store, [
            {"summary_id": "s1", "source_conversation_stable_id": "imported_conversation:1"},
            {"summary_id": "s2", "source_conversation_stable_id": "imported_conversation:2"},
            {"summary_id": "s3", "source_conversation_stable_id": "imported_conversation:2"},
        ])
        result = list_summaries_for_conversation(self.store, "imported_conversation:1")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["summary_id"], "s1")

    def test_returns_empty_when_no_match(self):
        _write_jsonl(self.store, [
            {"summary_id": "s1", "source_conversation_stable_id": "imported_conversation:2"},
        ])
        result = list_summaries_for_conversation(self.store, "imported_conversation:1")
        self.assertEqual(result, [])

    def test_missing_file_returns_empty(self):
        result = list_summaries_for_conversation(self.store, "imported_conversation:1")
        self.assertEqual(result, [])


class ListTopicScansForConversationTest(unittest.TestCase):
    def setUp(self):
        self.workdir = make_test_temp_dir(self, "list-topic-scans-conv")
        self.store = self.workdir / "topic_scans.jsonl"

    def test_returns_only_matching_row(self):
        _write_jsonl(self.store, [
            {
                "scan_id": "ts1",
                "clusters": [{"conversation_stable_ids": ["imported_conversation:1"]}],
            },
            {
                "scan_id": "ts2",
                "clusters": [{"conversation_stable_ids": ["imported_conversation:2"]}],
            },
            {
                "scan_id": "ts3",
                "clusters": [{"conversation_stable_ids": ["imported_conversation:2"]}],
            },
        ])
        result = list_topic_scans_for_conversation(self.store, "imported_conversation:1")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["scan_id"], "ts1")

    def test_returns_empty_when_no_match(self):
        _write_jsonl(self.store, [
            {"scan_id": "ts1", "clusters": [{"conversation_stable_ids": ["imported_conversation:9"]}]},
        ])
        result = list_topic_scans_for_conversation(self.store, "imported_conversation:1")
        self.assertEqual(result, [])

    def test_missing_file_returns_empty(self):
        result = list_topic_scans_for_conversation(self.store, "imported_conversation:1")
        self.assertEqual(result, [])


class ListDigestsForConversationTest(unittest.TestCase):
    def setUp(self):
        self.workdir = make_test_temp_dir(self, "list-digests-conv")
        self.store = self.workdir / "derived_digests.jsonl"

    def test_returns_only_matching_row(self):
        _write_jsonl(self.store, [
            {"digest_id": "d1", "source_conversation_stable_ids": ["imported_conversation:1"]},
            {"digest_id": "d2", "source_conversation_stable_ids": ["imported_conversation:2"]},
            {"digest_id": "d3", "source_conversation_stable_ids": ["imported_conversation:3"]},
        ])
        result = list_digests_for_conversation(self.store, "imported_conversation:1")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["digest_id"], "d1")

    def test_returns_empty_when_no_match(self):
        _write_jsonl(self.store, [
            {"digest_id": "d1", "source_conversation_stable_ids": ["imported_conversation:9"]},
        ])
        result = list_digests_for_conversation(self.store, "imported_conversation:1")
        self.assertEqual(result, [])

    def test_missing_file_returns_empty(self):
        result = list_digests_for_conversation(self.store, "imported_conversation:1")
        self.assertEqual(result, [])


class ListDistillationsForConversationTest(unittest.TestCase):
    def setUp(self):
        self.workdir = make_test_temp_dir(self, "list-distillations-conv")
        self.store = self.workdir / "derived_distillations.jsonl"

    def test_returns_only_matching_row(self):
        _write_jsonl(self.store, [
            {"distillation_id": "x1", "source_conversation_stable_ids": ["imported_conversation:1"]},
            {"distillation_id": "x2", "source_conversation_stable_ids": ["imported_conversation:2"]},
            {"distillation_id": "x3", "source_conversation_stable_ids": ["imported_conversation:2"]},
        ])
        result = list_distillations_for_conversation(self.store, "imported_conversation:1")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["distillation_id"], "x1")

    def test_returns_empty_when_no_match(self):
        _write_jsonl(self.store, [
            {"distillation_id": "x1", "source_conversation_stable_ids": ["imported_conversation:9"]},
        ])
        result = list_distillations_for_conversation(self.store, "imported_conversation:1")
        self.assertEqual(result, [])

    def test_missing_file_returns_empty(self):
        result = list_distillations_for_conversation(self.store, "imported_conversation:1")
        self.assertEqual(result, [])


if __name__ == "__main__":
    unittest.main()
