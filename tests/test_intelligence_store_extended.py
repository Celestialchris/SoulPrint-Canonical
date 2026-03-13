"""Tests for extended intelligence store (topic scans + digests)."""

from __future__ import annotations

import unittest

from src.intelligence.digest import DerivedDigest
from src.intelligence.store import (
    append_digest,
    append_summary,
    append_topic_scan,
    get_digest,
    get_summary,
    get_topic_scan,
    list_digests,
    list_summaries,
    list_topic_scans,
)
from src.intelligence.summarizer import DerivedSummary
from src.intelligence.topics import TopicScan
from tests.temp_helpers import make_test_temp_dir


def _make_topic_scan(scan_id: str = "topic_scan:test-001") -> TopicScan:
    return TopicScan(
        scan_id=scan_id,
        generation_timestamp="2026-03-13T12:00:00+00:00",
        llm_provider_used="stub",
        clusters=[
            {
                "topic_label": "Python",
                "conversation_stable_ids": ["imported_conversation:1", "imported_conversation:2"],
                "conversation_titles": ["Chat A", "Chat B"],
                "confidence": "high",
            }
        ],
        conversation_count=2,
        derived_from="canonical_imported_conversations",
        artifact_kind="topic_scan_v1",
    )


def _make_digest(digest_id: str = "derived_digest:test-001") -> DerivedDigest:
    return DerivedDigest(
        digest_id=digest_id,
        topic_label="Python",
        source_conversation_stable_ids=["imported_conversation:1", "imported_conversation:2"],
        source_conversation_titles=["Chat A", "Chat B"],
        generation_timestamp="2026-03-13T12:00:00+00:00",
        llm_provider_used="stub",
        prompt_template_version="v1",
        digest_text="A test digest about Python.",
        derived_from="canonical_imported_conversations",
        artifact_kind="derived_digest_v1",
    )


class TopicScanStoreTest(unittest.TestCase):
    def setUp(self):
        self.workdir = make_test_temp_dir(self, "intel-topics-store")
        self.store_path = self.workdir / "topic_scans.jsonl"

    def test_empty_store_returns_empty_list(self):
        self.assertEqual(list_topic_scans(self.store_path), [])

    def test_append_and_list_round_trip(self):
        scan = _make_topic_scan()
        append_topic_scan(self.store_path, scan)

        results = list_topic_scans(self.store_path)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["scan_id"], "topic_scan:test-001")

    def test_get_existing_topic_scan(self):
        append_topic_scan(self.store_path, _make_topic_scan())

        result = get_topic_scan(self.store_path, "topic_scan:test-001")
        self.assertIsNotNone(result)
        self.assertEqual(len(result["clusters"]), 1)
        self.assertEqual(result["clusters"][0]["topic_label"], "Python")

    def test_get_nonexistent_returns_none(self):
        append_topic_scan(self.store_path, _make_topic_scan())
        self.assertIsNone(get_topic_scan(self.store_path, "topic_scan:missing"))

    def test_get_from_missing_file_returns_none(self):
        self.assertIsNone(get_topic_scan(self.store_path, "topic_scan:any"))

    def test_list_returns_newest_first(self):
        append_topic_scan(self.store_path, _make_topic_scan("topic_scan:a"))
        append_topic_scan(self.store_path, _make_topic_scan("topic_scan:b"))

        results = list_topic_scans(self.store_path)
        self.assertEqual(results[0]["scan_id"], "topic_scan:b")
        self.assertEqual(results[1]["scan_id"], "topic_scan:a")


class DigestStoreTest(unittest.TestCase):
    def setUp(self):
        self.workdir = make_test_temp_dir(self, "intel-digest-store")
        self.store_path = self.workdir / "derived_digests.jsonl"

    def test_empty_store_returns_empty_list(self):
        self.assertEqual(list_digests(self.store_path), [])

    def test_append_and_list_round_trip(self):
        digest = _make_digest()
        append_digest(self.store_path, digest)

        results = list_digests(self.store_path)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["digest_id"], "derived_digest:test-001")

    def test_get_existing_digest(self):
        append_digest(self.store_path, _make_digest())

        result = get_digest(self.store_path, "derived_digest:test-001")
        self.assertIsNotNone(result)
        self.assertEqual(result["digest_text"], "A test digest about Python.")

    def test_get_nonexistent_returns_none(self):
        append_digest(self.store_path, _make_digest())
        self.assertIsNone(get_digest(self.store_path, "derived_digest:missing"))

    def test_get_from_missing_file_returns_none(self):
        self.assertIsNone(get_digest(self.store_path, "derived_digest:any"))

    def test_list_returns_newest_first(self):
        append_digest(self.store_path, _make_digest("derived_digest:a"))
        append_digest(self.store_path, _make_digest("derived_digest:b"))

        results = list_digests(self.store_path)
        self.assertEqual(results[0]["digest_id"], "derived_digest:b")
        self.assertEqual(results[1]["digest_id"], "derived_digest:a")


class ExistingSummaryStoreStillWorksTest(unittest.TestCase):
    """Verify that Phase 7.1 summary store is unchanged."""

    def setUp(self):
        self.workdir = make_test_temp_dir(self, "intel-compat")
        self.store_path = self.workdir / "derived_summaries.jsonl"

    def test_summary_round_trip_unchanged(self):
        summary = DerivedSummary(
            summary_id="derived_summary:compat-001",
            source_conversation_stable_id="imported_conversation:1",
            source_conversation_title="Compat Test",
            generation_timestamp="2026-03-13T12:00:00+00:00",
            llm_provider_used="stub",
            prompt_template_version="v1",
            summary_text="Compatibility check.",
            derived_from="canonical_imported_conversation",
            artifact_kind="derived_summary_v1",
        )
        append_summary(self.store_path, summary)

        results = list_summaries(self.store_path)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["summary_id"], "derived_summary:compat-001")

        result = get_summary(self.store_path, "derived_summary:compat-001")
        self.assertIsNotNone(result)
        self.assertEqual(result["summary_text"], "Compatibility check.")


if __name__ == "__main__":
    unittest.main()
