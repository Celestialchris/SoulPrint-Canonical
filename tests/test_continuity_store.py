"""Tests for continuity artifact JSONL persistence."""

from __future__ import annotations

import unittest

from src.intelligence.continuity.models import ContinuityArtifact
from src.intelligence.continuity.store import (
    append_artifact,
    default_continuity_store_path,
    get_artifact,
    list_artifacts,
    list_artifacts_by_type,
    list_artifacts_for_conversation,
)
from tests.temp_helpers import make_test_temp_dir


def _make_artifact(
    artifact_id: str = "continuity_artifact:test-001",
    artifact_type: str = "summary",
    source_ids: list[str] | None = None,
    provider: str = "stub",
    timestamp: str = "2026-03-13T12:00:00+00:00",
    prompt_version: str = "v1",
    content: str = "Test content.",
    parent_ids: list[str] | None = None,
    content_json: dict | None = None,
    ambiguity_notes: str | None = None,
) -> ContinuityArtifact:
    return ContinuityArtifact(
        artifact_id=artifact_id,
        artifact_type=artifact_type,  # type: ignore[arg-type]
        source_conversation_ids=source_ids or ["imported_conversation:1"],
        generation_timestamp=timestamp,
        llm_provider_used=provider,
        prompt_template_version=prompt_version,
        content_text=content,
        parent_packet_ids=parent_ids or [],
        content_json=content_json,
        ambiguity_notes=ambiguity_notes,
    )


class ContinuityStoreTest(unittest.TestCase):

    def setUp(self):
        self.workdir = make_test_temp_dir(self, "continuity-store")
        self.store_path = self.workdir / "continuity_artifacts.jsonl"

    # ── default path ──

    def test_default_path_beside_sqlite(self):
        path = default_continuity_store_path("/data/instance/soulprint.db")
        self.assertEqual(path.name, "continuity_artifacts.jsonl")
        self.assertIn("instance", str(path))

    # ── empty store ──

    def test_empty_store_returns_empty_list(self):
        self.assertEqual(list_artifacts(self.store_path), [])

    def test_get_from_missing_file_returns_none(self):
        self.assertIsNone(get_artifact(self.store_path, "continuity_artifact:any"))

    # ── round-trip persistence ──

    def test_append_and_list_round_trip(self):
        artifact = _make_artifact()
        append_artifact(self.store_path, artifact)

        results = list_artifacts(self.store_path)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["artifact_id"], "continuity_artifact:test-001")
        self.assertEqual(results[0]["artifact_type"], "summary")

    def test_append_and_get_round_trip(self):
        artifact = _make_artifact()
        append_artifact(self.store_path, artifact)

        result = get_artifact(self.store_path, "continuity_artifact:test-001")
        self.assertIsNotNone(result)
        self.assertEqual(result["content_text"], "Test content.")

    def test_get_nonexistent_returns_none(self):
        append_artifact(self.store_path, _make_artifact())
        self.assertIsNone(get_artifact(self.store_path, "continuity_artifact:nope"))

    # ── provenance fields persist ──

    def test_source_conversation_ids_persist(self):
        ids = ["imported_conversation:10", "imported_conversation:20", "memory:5"]
        artifact = _make_artifact(source_ids=ids)
        append_artifact(self.store_path, artifact)

        result = get_artifact(self.store_path, "continuity_artifact:test-001")
        self.assertEqual(result["source_conversation_ids"], ids)

    def test_provider_and_prompt_version_persist(self):
        artifact = _make_artifact(provider="anthropic", prompt_version="v2-beta")
        append_artifact(self.store_path, artifact)

        result = get_artifact(self.store_path, "continuity_artifact:test-001")
        self.assertEqual(result["llm_provider_used"], "anthropic")
        self.assertEqual(result["prompt_template_version"], "v2-beta")

    def test_generation_timestamp_persists(self):
        ts = "2026-03-14T08:30:00+00:00"
        artifact = _make_artifact(timestamp=ts)
        append_artifact(self.store_path, artifact)

        result = get_artifact(self.store_path, "continuity_artifact:test-001")
        self.assertEqual(result["generation_timestamp"], ts)

    def test_derived_from_and_artifact_kind_persist(self):
        artifact = _make_artifact()
        append_artifact(self.store_path, artifact)

        result = get_artifact(self.store_path, "continuity_artifact:test-001")
        self.assertEqual(result["derived_from"], "canonical_conversations")
        self.assertEqual(result["artifact_kind"], "continuity_artifact_v1")

    # ── optional fields ──

    def test_parent_packet_ids_persist(self):
        artifact = _make_artifact(parent_ids=["continuity_artifact:parent-a"])
        append_artifact(self.store_path, artifact)

        result = get_artifact(self.store_path, "continuity_artifact:test-001")
        self.assertEqual(result["parent_packet_ids"], ["continuity_artifact:parent-a"])

    def test_content_json_persists(self):
        cj = {"key_decisions": ["SQLite canonical", "BYOK providers"]}
        artifact = _make_artifact(content_json=cj)
        append_artifact(self.store_path, artifact)

        result = get_artifact(self.store_path, "continuity_artifact:test-001")
        self.assertEqual(result["content_json"], cj)

    def test_ambiguity_notes_persist(self):
        artifact = _make_artifact(ambiguity_notes="Sources disagree on timeline.")
        append_artifact(self.store_path, artifact)

        result = get_artifact(self.store_path, "continuity_artifact:test-001")
        self.assertEqual(result["ambiguity_notes"], "Sources disagree on timeline.")

    def test_null_optional_fields_persist(self):
        artifact = _make_artifact()
        append_artifact(self.store_path, artifact)

        result = get_artifact(self.store_path, "continuity_artifact:test-001")
        self.assertEqual(result["parent_packet_ids"], [])
        self.assertIsNone(result["content_json"])
        self.assertIsNone(result["ambiguity_notes"])

    # ── ordering ──

    def test_list_returns_newest_first(self):
        append_artifact(self.store_path, _make_artifact(
            artifact_id="continuity_artifact:a",
            timestamp="2026-03-13T10:00:00+00:00",
        ))
        append_artifact(self.store_path, _make_artifact(
            artifact_id="continuity_artifact:b",
            timestamp="2026-03-13T11:00:00+00:00",
        ))
        append_artifact(self.store_path, _make_artifact(
            artifact_id="continuity_artifact:c",
            timestamp="2026-03-13T12:00:00+00:00",
        ))

        results = list_artifacts(self.store_path)
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0]["artifact_id"], "continuity_artifact:c")
        self.assertEqual(results[2]["artifact_id"], "continuity_artifact:a")

    # ── all five artifact types ──

    def test_all_five_types_round_trip(self):
        for i, atype in enumerate(["summary", "decisions", "open_loops", "entity_map", "bridge"]):
            artifact = _make_artifact(
                artifact_id=f"continuity_artifact:type-{i}",
                artifact_type=atype,
                content=f"Content for {atype}.",
            )
            append_artifact(self.store_path, artifact)

        results = list_artifacts(self.store_path)
        self.assertEqual(len(results), 5)
        types_found = {r["artifact_type"] for r in results}
        self.assertEqual(types_found, {"summary", "decisions", "open_loops", "entity_map", "bridge"})

    # ── filtered queries ──

    def test_list_by_type_filters_correctly(self):
        append_artifact(self.store_path, _make_artifact(
            artifact_id="continuity_artifact:s1", artifact_type="summary",
        ))
        append_artifact(self.store_path, _make_artifact(
            artifact_id="continuity_artifact:d1", artifact_type="decisions",
        ))
        append_artifact(self.store_path, _make_artifact(
            artifact_id="continuity_artifact:s2", artifact_type="summary",
        ))

        summaries = list_artifacts_by_type(self.store_path, "summary")
        self.assertEqual(len(summaries), 2)
        self.assertTrue(all(r["artifact_type"] == "summary" for r in summaries))

        decisions = list_artifacts_by_type(self.store_path, "decisions")
        self.assertEqual(len(decisions), 1)

    def test_list_by_type_empty_result(self):
        append_artifact(self.store_path, _make_artifact(artifact_type="summary"))
        self.assertEqual(list_artifacts_by_type(self.store_path, "bridge"), [])

    def test_list_for_conversation_filters_correctly(self):
        append_artifact(self.store_path, _make_artifact(
            artifact_id="continuity_artifact:a1",
            source_ids=["imported_conversation:10", "imported_conversation:20"],
        ))
        append_artifact(self.store_path, _make_artifact(
            artifact_id="continuity_artifact:a2",
            source_ids=["imported_conversation:30"],
        ))

        results = list_artifacts_for_conversation(self.store_path, "imported_conversation:10")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["artifact_id"], "continuity_artifact:a1")

    def test_list_for_conversation_no_match(self):
        append_artifact(self.store_path, _make_artifact(
            source_ids=["imported_conversation:1"],
        ))
        self.assertEqual(
            list_artifacts_for_conversation(self.store_path, "imported_conversation:99"),
            [],
        )

    # ── multiple sources ──

    def test_multiple_source_conversations(self):
        sources = [
            "imported_conversation:1",
            "imported_conversation:2",
            "imported_conversation:3",
            "memory:10",
        ]
        artifact = _make_artifact(source_ids=sources)
        append_artifact(self.store_path, artifact)

        result = get_artifact(self.store_path, "continuity_artifact:test-001")
        self.assertEqual(result["source_conversation_ids"], sources)


if __name__ == "__main__":
    unittest.main()
