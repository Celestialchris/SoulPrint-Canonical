"""Tests for continuity bridge assembly."""

from __future__ import annotations

import unittest

from src.intelligence.continuity.bridge import (
    MAX_BRIDGE_CHARS,
    BridgeResult,
    assemble_bridge,
    assemble_bridge_text,
)
from src.intelligence.continuity.store import get_artifact, list_artifacts
from tests.temp_helpers import make_test_temp_dir


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------


def _make_artifacts(
    conv_id: str = "imported_conversation:42",
    summary_text: str = "Discussion about local-first storage using SQLite.",
    decisions: list[str] | None = None,
    open_loops: list[str] | None = None,
    entities: list[str] | None = None,
) -> list[dict]:
    """Build a minimal set of continuity artifacts as dicts (newest-first)."""
    decisions = decisions or ["Use SQLite for canonical storage", "Keep derived artifacts in JSONL"]
    open_loops = open_loops or ["Whether to add FTS5 for search"]
    entities = entities or ["SQLite", "JSONL", "Flask"]

    return [
        {
            "artifact_id": "continuity_artifact:summary-1",
            "artifact_type": "summary",
            "source_conversation_ids": [conv_id],
            "generation_timestamp": "2026-03-13T12:00:00+00:00",
            "llm_provider_used": "stub",
            "prompt_template_version": "v1",
            "content_text": summary_text,
            "content_json": None,
        },
        {
            "artifact_id": "continuity_artifact:decisions-1",
            "artifact_type": "decisions",
            "source_conversation_ids": [conv_id],
            "generation_timestamp": "2026-03-13T12:00:00+00:00",
            "llm_provider_used": "stub",
            "prompt_template_version": "v1",
            "content_text": "\n".join(f"- {d}" for d in decisions),
            "content_json": {"decisions": decisions},
        },
        {
            "artifact_id": "continuity_artifact:loops-1",
            "artifact_type": "open_loops",
            "source_conversation_ids": [conv_id],
            "generation_timestamp": "2026-03-13T12:00:00+00:00",
            "llm_provider_used": "stub",
            "prompt_template_version": "v1",
            "content_text": "\n".join(f"- {o}" for o in open_loops),
            "content_json": {"open_loops": open_loops},
        },
        {
            "artifact_id": "continuity_artifact:entities-1",
            "artifact_type": "entity_map",
            "source_conversation_ids": [conv_id],
            "generation_timestamp": "2026-03-13T12:00:00+00:00",
            "llm_provider_used": "stub",
            "prompt_template_version": "v1",
            "content_text": ", ".join(entities),
            "content_json": {"entity_map": entities},
        },
    ]


def _make_parent_artifacts(
    conv_id: str = "imported_conversation:10",
) -> list[dict]:
    """Build parent artifacts for multi-packet bridge tests."""
    return [
        {
            "artifact_id": "continuity_artifact:parent-summary-1",
            "artifact_type": "summary",
            "source_conversation_ids": [conv_id],
            "generation_timestamp": "2026-03-12T10:00:00+00:00",
            "llm_provider_used": "stub",
            "prompt_template_version": "v1",
            "content_text": "Earlier discussion about project architecture choices.",
            "content_json": None,
        },
        {
            "artifact_id": "continuity_artifact:parent-decisions-1",
            "artifact_type": "decisions",
            "source_conversation_ids": [conv_id],
            "generation_timestamp": "2026-03-12T10:00:00+00:00",
            "llm_provider_used": "stub",
            "prompt_template_version": "v1",
            "content_text": "- Use Flask for web layer\n- Local-first architecture",
            "content_json": {"decisions": ["Use Flask for web layer", "Local-first architecture"]},
        },
    ]


# ---------------------------------------------------------------------------
# Tests — single-packet bridge assembly
# ---------------------------------------------------------------------------


class SinglePacketBridgeTest(unittest.TestCase):

    def test_bridge_text_contains_summary_as_objective(self):
        text = assemble_bridge_text(_make_artifacts())
        self.assertIn("Prior Objective", text)
        self.assertIn("local-first storage", text)

    def test_bridge_text_contains_decisions(self):
        text = assemble_bridge_text(_make_artifacts())
        self.assertIn("Key Decisions", text)
        self.assertIn("SQLite for canonical storage", text)

    def test_bridge_text_contains_open_loops(self):
        text = assemble_bridge_text(_make_artifacts())
        self.assertIn("Open Loops", text)
        self.assertIn("FTS5", text)

    def test_bridge_text_contains_entities(self):
        text = assemble_bridge_text(_make_artifacts())
        self.assertIn("Key Entities", text)
        self.assertIn("Flask", text)

    def test_bridge_text_contains_next_step_seed(self):
        text = assemble_bridge_text(_make_artifacts())
        self.assertIn("Suggested Next Step", text)
        self.assertIn("FTS5", text)

    def test_bridge_text_contains_derived_label(self):
        text = assemble_bridge_text(_make_artifacts())
        self.assertIn("not canonical", text)

    def test_bridge_text_contains_title_when_provided(self):
        text = assemble_bridge_text(_make_artifacts(), conversation_title="Storage Chat")
        self.assertIn("Storage Chat", text)

    def test_bridge_text_header_present(self):
        text = assemble_bridge_text(_make_artifacts())
        self.assertIn("# Continuity Bridge", text)


# ---------------------------------------------------------------------------
# Tests — bridge with parent artifacts
# ---------------------------------------------------------------------------


class ParentPacketBridgeTest(unittest.TestCase):

    def test_parent_context_section_present(self):
        text = assemble_bridge_text(
            _make_artifacts(),
            parent_artifacts=_make_parent_artifacts(),
        )
        self.assertIn("Prior Context (from parent)", text)
        self.assertIn("project architecture", text)

    def test_parent_decisions_included(self):
        text = assemble_bridge_text(
            _make_artifacts(),
            parent_artifacts=_make_parent_artifacts(),
        )
        self.assertIn("Flask for web layer", text)

    def test_main_and_parent_sections_both_present(self):
        text = assemble_bridge_text(
            _make_artifacts(),
            parent_artifacts=_make_parent_artifacts(),
        )
        # Main artifact sections
        self.assertIn("Prior Objective", text)
        self.assertIn("Key Decisions", text)
        # Parent section
        self.assertIn("Prior Context (from parent)", text)


# ---------------------------------------------------------------------------
# Tests — assemble_bridge result type and provenance
# ---------------------------------------------------------------------------


class BridgeResultTest(unittest.TestCase):

    def test_returns_bridge_result(self):
        result = assemble_bridge("imported_conversation:42", _make_artifacts())
        self.assertIsInstance(result, BridgeResult)
        self.assertIsNone(result.error)

    def test_artifact_type_is_bridge(self):
        result = assemble_bridge("imported_conversation:42", _make_artifacts())
        self.assertEqual(result.artifact.artifact_type, "bridge")

    def test_artifact_id_prefix(self):
        result = assemble_bridge("imported_conversation:42", _make_artifacts())
        self.assertTrue(result.artifact.artifact_id.startswith("continuity_artifact:"))

    def test_source_conversation_ids_include_primary(self):
        result = assemble_bridge("imported_conversation:42", _make_artifacts())
        self.assertIn("imported_conversation:42", result.source_conversation_ids)

    def test_source_conversation_ids_include_parents(self):
        result = assemble_bridge(
            "imported_conversation:42",
            _make_artifacts(),
            parent_artifacts=_make_parent_artifacts(),
        )
        self.assertIn("imported_conversation:42", result.source_conversation_ids)
        self.assertIn("imported_conversation:10", result.source_conversation_ids)

    def test_parent_packet_ids_tracked(self):
        parents = _make_parent_artifacts()
        result = assemble_bridge(
            "imported_conversation:42",
            _make_artifacts(),
            parent_artifacts=parents,
        )
        expected_ids = [a["artifact_id"] for a in parents]
        self.assertEqual(result.parent_packet_ids, expected_ids)

    def test_no_parents_empty_parent_ids(self):
        result = assemble_bridge("imported_conversation:42", _make_artifacts())
        self.assertEqual(result.parent_packet_ids, [])

    def test_provider_is_bridge_assembler(self):
        result = assemble_bridge("imported_conversation:42", _make_artifacts())
        self.assertEqual(result.artifact.llm_provider_used, "bridge_assembler")

    def test_prompt_version_set(self):
        result = assemble_bridge("imported_conversation:42", _make_artifacts())
        self.assertEqual(result.artifact.prompt_template_version, "bridge-v1")

    def test_generation_timestamp_present(self):
        result = assemble_bridge("imported_conversation:42", _make_artifacts())
        self.assertIn("T", result.artifact.generation_timestamp)
        self.assertTrue(result.artifact.generation_timestamp.endswith("+00:00"))


# ---------------------------------------------------------------------------
# Tests — token/length guardrails
# ---------------------------------------------------------------------------


class LengthGuardrailTest(unittest.TestCase):

    def test_normal_bridge_under_max(self):
        text = assemble_bridge_text(_make_artifacts())
        self.assertLessEqual(len(text), MAX_BRIDGE_CHARS)

    def test_very_long_summary_gets_truncated(self):
        long_summary = "x " * 8000  # ~16k chars
        artifacts = _make_artifacts(summary_text=long_summary)
        text = assemble_bridge_text(artifacts)
        self.assertLessEqual(len(text), MAX_BRIDGE_CHARS)
        self.assertIn("[truncated]", text)

    def test_many_decisions_stay_bounded(self):
        many_decisions = [f"Decision number {i} about topic {i}" for i in range(200)]
        artifacts = _make_artifacts(decisions=many_decisions)
        text = assemble_bridge_text(artifacts)
        self.assertLessEqual(len(text), MAX_BRIDGE_CHARS)

    def test_combined_large_artifacts_stay_bounded(self):
        artifacts = _make_artifacts(
            summary_text="S " * 2000,
            decisions=[f"Decision {i}" for i in range(100)],
            open_loops=[f"Loop {i}" for i in range(100)],
            entities=[f"Entity{i}" for i in range(100)],
        )
        text = assemble_bridge_text(artifacts)
        self.assertLessEqual(len(text), MAX_BRIDGE_CHARS)

    def test_bridge_text_non_empty_for_normal_input(self):
        text = assemble_bridge_text(_make_artifacts())
        self.assertGreater(len(text), 100)


# ---------------------------------------------------------------------------
# Tests — graceful behavior with missing data
# ---------------------------------------------------------------------------


class GracefulMissingDataTest(unittest.TestCase):

    def test_empty_artifacts_returns_error(self):
        result = assemble_bridge("imported_conversation:42", [])
        self.assertIsNotNone(result.error)
        self.assertIn("No continuity artifacts", result.error)
        self.assertIsNone(result.artifact)
        self.assertEqual(result.bridge_text, "")

    def test_summary_only_produces_bridge(self):
        artifacts = [_make_artifacts()[0]]  # summary only
        text = assemble_bridge_text(artifacts)
        self.assertIn("Prior Objective", text)
        self.assertNotIn("Key Decisions", text)
        self.assertNotIn("Open Loops", text)

    def test_no_parents_still_works(self):
        text = assemble_bridge_text(_make_artifacts(), parent_artifacts=None)
        self.assertIn("Prior Objective", text)
        self.assertNotIn("Prior Context (from parent)", text)

    def test_empty_parents_list_still_works(self):
        text = assemble_bridge_text(_make_artifacts(), parent_artifacts=[])
        self.assertNotIn("Prior Context (from parent)", text)

    def test_parent_without_summary_uses_decisions(self):
        parents = [_make_parent_artifacts()[1]]  # decisions only
        text = assemble_bridge_text(_make_artifacts(), parent_artifacts=parents)
        self.assertIn("Prior Context (from parent)", text)
        self.assertIn("Flask for web layer", text)

    def test_parent_with_no_matching_types_skips_section(self):
        parents = [{
            "artifact_id": "continuity_artifact:parent-entities",
            "artifact_type": "entity_map",
            "source_conversation_ids": ["imported_conversation:10"],
            "content_text": "SomeEntity",
        }]
        text = assemble_bridge_text(_make_artifacts(), parent_artifacts=parents)
        self.assertNotIn("Prior Context (from parent)", text)

    def test_open_loops_without_json_uses_content_text(self):
        artifacts = _make_artifacts()
        # Remove content_json from open_loops
        for a in artifacts:
            if a["artifact_type"] == "open_loops":
                a["content_json"] = None
        text = assemble_bridge_text(artifacts)
        self.assertIn("Suggested Next Step", text)
        self.assertIn("FTS5", text)

    def test_stable_id_always_in_source_ids(self):
        result = assemble_bridge("imported_conversation:99", _make_artifacts())
        self.assertIn("imported_conversation:99", result.source_conversation_ids)


# ---------------------------------------------------------------------------
# Tests — persistence
# ---------------------------------------------------------------------------


class BridgePersistenceTest(unittest.TestCase):

    def setUp(self):
        self.workdir = make_test_temp_dir(self, "bridge-persist")
        self.store_path = self.workdir / "continuity_artifacts.jsonl"

    def test_bridge_persisted_when_store_path_given(self):
        result = assemble_bridge(
            "imported_conversation:42",
            _make_artifacts(),
            store_path=self.store_path,
        )
        stored = list_artifacts(self.store_path)
        self.assertEqual(len(stored), 1)
        self.assertEqual(stored[0]["artifact_type"], "bridge")
        self.assertEqual(stored[0]["artifact_id"], result.artifact.artifact_id)

    def test_bridge_not_persisted_without_store_path(self):
        assemble_bridge("imported_conversation:42", _make_artifacts())
        self.assertFalse(self.store_path.exists())

    def test_persisted_bridge_retrievable_by_id(self):
        result = assemble_bridge(
            "imported_conversation:42",
            _make_artifacts(),
            store_path=self.store_path,
        )
        fetched = get_artifact(self.store_path, result.artifact.artifact_id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched["artifact_type"], "bridge")
        self.assertEqual(fetched["llm_provider_used"], "bridge_assembler")

    def test_persisted_bridge_has_parent_ids(self):
        parents = _make_parent_artifacts()
        result = assemble_bridge(
            "imported_conversation:42",
            _make_artifacts(),
            parent_artifacts=parents,
            store_path=self.store_path,
        )
        fetched = get_artifact(self.store_path, result.artifact.artifact_id)
        self.assertEqual(
            fetched["parent_packet_ids"],
            [a["artifact_id"] for a in parents],
        )

    def test_error_result_not_persisted(self):
        assemble_bridge(
            "imported_conversation:42",
            [],
            store_path=self.store_path,
        )
        self.assertFalse(self.store_path.exists())


if __name__ == "__main__":
    unittest.main()
