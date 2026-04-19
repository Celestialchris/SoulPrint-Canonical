"""Tests for cascade-delete helpers in derived intelligence stores."""

from __future__ import annotations

import json
import os
import time
import unittest
from pathlib import Path

from tests.temp_helpers import make_test_temp_dir
from src.intelligence.store import (
    delete_digests_for_conversation,
    delete_distillations_for_conversation,
    delete_summaries_for_conversation,
    delete_topic_scans_for_conversation,
)
from src.intelligence.continuity.store import delete_artifacts_for_conversation


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            cleaned = line.strip()
            if cleaned:
                rows.append(json.loads(cleaned))
    return rows


# ---------------------------------------------------------------------------
# Summaries — singular str field
# ---------------------------------------------------------------------------

class DeleteSummariesForConversationTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = make_test_temp_dir(self, "del-summaries")
        self.store = self.tmpdir / "derived_summaries.jsonl"

    def _row(self, stable_id: str, summary_id: str = "s1") -> dict:
        return {
            "summary_id": summary_id,
            "source_conversation_stable_id": stable_id,
            "text": "x",
        }

    def test_deletes_matching_rows(self):
        _write_jsonl(self.store, [self._row("conv-A"), self._row("conv-B", "s2")])
        delete_summaries_for_conversation(self.store, "conv-A")
        rows = _read_jsonl(self.store)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["source_conversation_stable_id"], "conv-B")

    def test_leaves_other_rows_intact(self):
        _write_jsonl(self.store, [self._row("conv-A"), self._row("conv-B", "s2")])
        delete_summaries_for_conversation(self.store, "conv-A")
        rows = _read_jsonl(self.store)
        self.assertEqual(rows[0]["summary_id"], "s2")
        self.assertEqual(rows[0]["source_conversation_stable_id"], "conv-B")

    def test_returns_correct_count(self):
        _write_jsonl(self.store, [
            self._row("conv-A"),
            self._row("conv-A", "s2"),
            self._row("conv-B", "s3"),
        ])
        count = delete_summaries_for_conversation(self.store, "conv-A")
        self.assertEqual(count, 2)

    def test_no_match_returns_zero_and_does_not_rewrite_file(self):
        _write_jsonl(self.store, [self._row("conv-B"), self._row("conv-C", "s2")])
        mtime_before = os.path.getmtime(self.store)
        time.sleep(0.02)
        count = delete_summaries_for_conversation(self.store, "conv-A")
        self.assertEqual(count, 0)
        self.assertEqual(os.path.getmtime(self.store), mtime_before)

    def test_nonexistent_file_returns_zero(self):
        count = delete_summaries_for_conversation(self.store, "conv-A")
        self.assertEqual(count, 0)

    def test_does_not_match_on_wrong_field_name(self):
        # Uses plural "source_conversation_stable_ids" (list); helper checks singular str
        row = {"summary_id": "s1", "source_conversation_stable_ids": ["conv-A"]}
        _write_jsonl(self.store, [row])
        count = delete_summaries_for_conversation(self.store, "conv-A")
        self.assertEqual(count, 0)
        self.assertEqual(_read_jsonl(self.store), [row])


# ---------------------------------------------------------------------------
# Distillations — plural list field
# ---------------------------------------------------------------------------

class DeleteDistillationsForConversationTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = make_test_temp_dir(self, "del-distillations")
        self.store = self.tmpdir / "derived_distillations.jsonl"

    def _row(self, stable_ids: list[str], distillation_id: str = "d1") -> dict:
        return {
            "distillation_id": distillation_id,
            "source_conversation_stable_ids": stable_ids,
            "text": "x",
        }

    def test_deletes_matching_rows(self):
        _write_jsonl(self.store, [
            self._row(["conv-A", "conv-B"]),
            self._row(["conv-C"], "d2"),
        ])
        delete_distillations_for_conversation(self.store, "conv-A")
        rows = _read_jsonl(self.store)
        self.assertEqual(len(rows), 1)
        self.assertNotIn("conv-A", rows[0]["source_conversation_stable_ids"])

    def test_leaves_other_rows_intact(self):
        _write_jsonl(self.store, [
            self._row(["conv-A"]),
            self._row(["conv-B", "conv-C"], "d2"),
        ])
        delete_distillations_for_conversation(self.store, "conv-A")
        rows = _read_jsonl(self.store)
        self.assertEqual(rows[0]["distillation_id"], "d2")
        self.assertEqual(rows[0]["source_conversation_stable_ids"], ["conv-B", "conv-C"])

    def test_returns_correct_count(self):
        _write_jsonl(self.store, [
            self._row(["conv-A"]),
            self._row(["conv-A", "conv-B"], "d2"),
            self._row(["conv-C"], "d3"),
        ])
        count = delete_distillations_for_conversation(self.store, "conv-A")
        self.assertEqual(count, 2)

    def test_no_match_returns_zero_and_does_not_rewrite_file(self):
        _write_jsonl(self.store, [self._row(["conv-B"]), self._row(["conv-C"], "d2")])
        mtime_before = os.path.getmtime(self.store)
        time.sleep(0.02)
        count = delete_distillations_for_conversation(self.store, "conv-A")
        self.assertEqual(count, 0)
        self.assertEqual(os.path.getmtime(self.store), mtime_before)

    def test_nonexistent_file_returns_zero(self):
        count = delete_distillations_for_conversation(self.store, "conv-A")
        self.assertEqual(count, 0)

    def test_does_not_match_on_wrong_field_name(self):
        # Uses singular "source_conversation_stable_id" (str); helper checks plural list
        row = {"distillation_id": "d1", "source_conversation_stable_id": "conv-A"}
        _write_jsonl(self.store, [row])
        count = delete_distillations_for_conversation(self.store, "conv-A")
        self.assertEqual(count, 0)
        self.assertEqual(_read_jsonl(self.store), [row])


# ---------------------------------------------------------------------------
# Digests — plural list field
# ---------------------------------------------------------------------------

class DeleteDigestsForConversationTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = make_test_temp_dir(self, "del-digests")
        self.store = self.tmpdir / "derived_digests.jsonl"

    def _row(self, stable_ids: list[str], digest_id: str = "dg1") -> dict:
        return {
            "digest_id": digest_id,
            "source_conversation_stable_ids": stable_ids,
            "text": "x",
        }

    def test_deletes_matching_rows(self):
        _write_jsonl(self.store, [
            self._row(["conv-A"]),
            self._row(["conv-B"], "dg2"),
        ])
        delete_digests_for_conversation(self.store, "conv-A")
        rows = _read_jsonl(self.store)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["digest_id"], "dg2")

    def test_leaves_other_rows_intact(self):
        _write_jsonl(self.store, [
            self._row(["conv-A"]),
            self._row(["conv-B", "conv-C"], "dg2"),
        ])
        delete_digests_for_conversation(self.store, "conv-A")
        rows = _read_jsonl(self.store)
        self.assertEqual(rows[0]["source_conversation_stable_ids"], ["conv-B", "conv-C"])

    def test_returns_correct_count(self):
        _write_jsonl(self.store, [
            self._row(["conv-A"]),
            self._row(["conv-A", "conv-B"], "dg2"),
            self._row(["conv-C"], "dg3"),
        ])
        count = delete_digests_for_conversation(self.store, "conv-A")
        self.assertEqual(count, 2)

    def test_no_match_returns_zero_and_does_not_rewrite_file(self):
        _write_jsonl(self.store, [self._row(["conv-B"]), self._row(["conv-C"], "dg2")])
        mtime_before = os.path.getmtime(self.store)
        time.sleep(0.02)
        count = delete_digests_for_conversation(self.store, "conv-A")
        self.assertEqual(count, 0)
        self.assertEqual(os.path.getmtime(self.store), mtime_before)

    def test_nonexistent_file_returns_zero(self):
        count = delete_digests_for_conversation(self.store, "conv-A")
        self.assertEqual(count, 0)

    def test_does_not_match_on_wrong_field_name(self):
        # Uses continuity's "source_conversation_ids"; helper checks "source_conversation_stable_ids"
        row = {"digest_id": "dg1", "source_conversation_ids": ["conv-A"]}
        _write_jsonl(self.store, [row])
        count = delete_digests_for_conversation(self.store, "conv-A")
        self.assertEqual(count, 0)
        self.assertEqual(_read_jsonl(self.store), [row])


# ---------------------------------------------------------------------------
# Topic scans — nested clusters field
# ---------------------------------------------------------------------------

class DeleteTopicScansForConversationTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = make_test_temp_dir(self, "del-topic-scans")
        self.store = self.tmpdir / "topic_scans.jsonl"

    def _row_with_conv(self, stable_id: str, scan_id: str = "ts1") -> dict:
        return {
            "scan_id": scan_id,
            "clusters": [
                {
                    "cluster_id": "c1",
                    "conversation_stable_ids": [stable_id],
                    "label": "test",
                },
            ],
        }

    def _row_without_target(self, scan_id: str = "ts2") -> dict:
        return {
            "scan_id": scan_id,
            "clusters": [
                {
                    "cluster_id": "c2",
                    "conversation_stable_ids": ["conv-Z"],
                    "label": "other",
                },
            ],
        }

    def test_deletes_matching_rows(self):
        _write_jsonl(self.store, [
            self._row_with_conv("conv-A"),
            self._row_without_target(),
        ])
        delete_topic_scans_for_conversation(self.store, "conv-A")
        rows = _read_jsonl(self.store)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["scan_id"], "ts2")

    def test_leaves_other_rows_intact(self):
        _write_jsonl(self.store, [
            self._row_with_conv("conv-A"),
            self._row_without_target(),
        ])
        delete_topic_scans_for_conversation(self.store, "conv-A")
        rows = _read_jsonl(self.store)
        self.assertEqual(rows[0]["clusters"][0]["conversation_stable_ids"], ["conv-Z"])

    def test_returns_correct_count(self):
        _write_jsonl(self.store, [
            self._row_with_conv("conv-A"),
            self._row_with_conv("conv-A", "ts3"),
            self._row_without_target(),
        ])
        count = delete_topic_scans_for_conversation(self.store, "conv-A")
        self.assertEqual(count, 2)

    def test_no_match_returns_zero_and_does_not_rewrite_file(self):
        _write_jsonl(self.store, [
            self._row_without_target(),
            self._row_without_target("ts3"),
        ])
        mtime_before = os.path.getmtime(self.store)
        time.sleep(0.02)
        count = delete_topic_scans_for_conversation(self.store, "conv-A")
        self.assertEqual(count, 0)
        self.assertEqual(os.path.getmtime(self.store), mtime_before)

    def test_nonexistent_file_returns_zero(self):
        count = delete_topic_scans_for_conversation(self.store, "conv-A")
        self.assertEqual(count, 0)

    def test_does_not_match_on_wrong_field_name(self):
        # Top-level "source_conversation_stable_ids" with no "clusters" key
        row = {"scan_id": "ts1", "source_conversation_stable_ids": ["conv-A"]}
        _write_jsonl(self.store, [row])
        count = delete_topic_scans_for_conversation(self.store, "conv-A")
        self.assertEqual(count, 0)
        self.assertEqual(_read_jsonl(self.store), [row])

    def test_matches_when_any_cluster_references_conversation(self):
        row = {
            "scan_id": "ts1",
            "clusters": [
                {"cluster_id": "c1", "conversation_stable_ids": ["conv-Z"], "label": "other"},
                {"cluster_id": "c2", "conversation_stable_ids": ["conv-A", "conv-B"], "label": "test"},
            ],
        }
        _write_jsonl(self.store, [row])
        count = delete_topic_scans_for_conversation(self.store, "conv-A")
        self.assertEqual(count, 1)
        self.assertEqual(_read_jsonl(self.store), [])

    def test_does_not_match_when_no_cluster_references_conversation(self):
        row = {
            "scan_id": "ts1",
            "clusters": [
                {"cluster_id": "c1", "conversation_stable_ids": ["conv-Z"], "label": "other"},
            ],
        }
        _write_jsonl(self.store, [row])
        count = delete_topic_scans_for_conversation(self.store, "conv-A")
        self.assertEqual(count, 0)

    def test_does_not_match_on_top_level_field_only_nested_clusters_count(self):
        # Verifies that only nested cluster membership triggers a delete
        row = {"scan_id": "ts1", "source_conversation_stable_ids": ["conv-A"]}
        _write_jsonl(self.store, [row])
        count = delete_topic_scans_for_conversation(self.store, "conv-A")
        self.assertEqual(count, 0)
        self.assertEqual(_read_jsonl(self.store), [row])


# ---------------------------------------------------------------------------
# Continuity artifacts — source_conversation_ids (no "stable_" prefix)
# ---------------------------------------------------------------------------

class DeleteArtifactsForConversationTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = make_test_temp_dir(self, "del-continuity")
        self.store = self.tmpdir / "continuity_artifacts.jsonl"

    def _row(self, stable_ids: list[str], artifact_id: str = "a1") -> dict:
        return {
            "artifact_id": artifact_id,
            "source_conversation_ids": stable_ids,
            "artifact_type": "summary",
        }

    def test_deletes_matching_rows(self):
        _write_jsonl(self.store, [
            self._row(["conv-A"]),
            self._row(["conv-B"], "a2"),
        ])
        delete_artifacts_for_conversation(self.store, "conv-A")
        rows = _read_jsonl(self.store)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["artifact_id"], "a2")

    def test_leaves_other_rows_intact(self):
        _write_jsonl(self.store, [
            self._row(["conv-A"]),
            self._row(["conv-B", "conv-C"], "a2"),
        ])
        delete_artifacts_for_conversation(self.store, "conv-A")
        rows = _read_jsonl(self.store)
        self.assertEqual(rows[0]["source_conversation_ids"], ["conv-B", "conv-C"])

    def test_returns_correct_count(self):
        _write_jsonl(self.store, [
            self._row(["conv-A"]),
            self._row(["conv-A", "conv-B"], "a2"),
            self._row(["conv-C"], "a3"),
        ])
        count = delete_artifacts_for_conversation(self.store, "conv-A")
        self.assertEqual(count, 2)

    def test_no_match_returns_zero_and_does_not_rewrite_file(self):
        _write_jsonl(self.store, [self._row(["conv-B"]), self._row(["conv-C"], "a2")])
        mtime_before = os.path.getmtime(self.store)
        time.sleep(0.02)
        count = delete_artifacts_for_conversation(self.store, "conv-A")
        self.assertEqual(count, 0)
        self.assertEqual(os.path.getmtime(self.store), mtime_before)

    def test_nonexistent_file_returns_zero(self):
        count = delete_artifacts_for_conversation(self.store, "conv-A")
        self.assertEqual(count, 0)

    def test_does_not_match_on_wrong_field_name(self):
        # Uses "source_conversation_stable_ids" (the other stores' name, with "stable_")
        row = {"artifact_id": "a1", "source_conversation_stable_ids": ["conv-A"]}
        _write_jsonl(self.store, [row])
        count = delete_artifacts_for_conversation(self.store, "conv-A")
        self.assertEqual(count, 0)
        self.assertEqual(_read_jsonl(self.store), [row])


if __name__ == "__main__":
    unittest.main()
