"""Tests for continuity artifact models and validation."""

from __future__ import annotations

import unittest

from src.intelligence.continuity.models import (
    VALID_ARTIFACT_TYPES,
    ContinuityArtifact,
    make_artifact_id,
    make_timestamp,
    validate_artifact,
)


def _make_artifact(**overrides) -> ContinuityArtifact:
    defaults = dict(
        artifact_id="continuity_artifact:test-001",
        artifact_type="summary",
        source_conversation_ids=["imported_conversation:1", "imported_conversation:2"],
        generation_timestamp="2026-03-13T12:00:00+00:00",
        llm_provider_used="stub",
        prompt_template_version="v1",
        content_text="A concise summary of the conversation themes.",
    )
    defaults.update(overrides)
    return ContinuityArtifact(**defaults)


class ArtifactModelTest(unittest.TestCase):

    def test_all_five_artifact_types_recognized(self):
        expected = {"summary", "decisions", "open_loops", "entity_map", "bridge"}
        self.assertEqual(VALID_ARTIFACT_TYPES, expected)

    def test_default_field_values(self):
        a = _make_artifact()
        self.assertEqual(a.derived_from, "canonical_conversations")
        self.assertEqual(a.artifact_kind, "continuity_artifact_v1")
        self.assertEqual(a.parent_packet_ids, [])
        self.assertIsNone(a.content_json)
        self.assertIsNone(a.ambiguity_notes)

    def test_optional_fields_persist(self):
        a = _make_artifact(
            parent_packet_ids=["continuity_artifact:parent-1"],
            content_json={"key_decisions": ["use SQLite", "keep local"]},
            ambiguity_notes="Source conversations disagree on timeline.",
        )
        self.assertEqual(a.parent_packet_ids, ["continuity_artifact:parent-1"])
        self.assertEqual(a.content_json["key_decisions"][0], "use SQLite")
        self.assertEqual(a.ambiguity_notes, "Source conversations disagree on timeline.")

    def test_frozen_immutability(self):
        a = _make_artifact()
        with self.assertRaises(AttributeError):
            a.content_text = "mutated"  # type: ignore[misc]

    def test_each_artifact_type_validates(self):
        for atype in VALID_ARTIFACT_TYPES:
            a = _make_artifact(artifact_type=atype)
            errors = validate_artifact(a)
            self.assertEqual(errors, [], f"Unexpected errors for type {atype}: {errors}")

    def test_make_artifact_id_format(self):
        aid = make_artifact_id()
        self.assertTrue(aid.startswith("continuity_artifact:"))
        self.assertGreater(len(aid), len("continuity_artifact:"))

    def test_make_artifact_id_uniqueness(self):
        ids = {make_artifact_id() for _ in range(100)}
        self.assertEqual(len(ids), 100)

    def test_make_timestamp_iso_format(self):
        ts = make_timestamp()
        self.assertIn("T", ts)
        self.assertTrue(ts.endswith("+00:00"))


class ArtifactValidationTest(unittest.TestCase):

    def test_valid_artifact_no_errors(self):
        a = _make_artifact()
        self.assertEqual(validate_artifact(a), [])

    def test_bad_artifact_id_prefix(self):
        a = _make_artifact(artifact_id="wrong_prefix:123")
        errors = validate_artifact(a)
        self.assertTrue(any("artifact_id" in e for e in errors))

    def test_empty_artifact_id(self):
        a = _make_artifact(artifact_id="")
        errors = validate_artifact(a)
        self.assertTrue(any("artifact_id" in e for e in errors))

    def test_invalid_artifact_type(self):
        a = _make_artifact(artifact_type="nonexistent")  # type: ignore[arg-type]
        errors = validate_artifact(a)
        self.assertTrue(any("artifact_type" in e for e in errors))

    def test_empty_source_conversation_ids(self):
        a = _make_artifact(source_conversation_ids=[])
        errors = validate_artifact(a)
        self.assertTrue(any("source_conversation_ids" in e for e in errors))

    def test_missing_llm_provider(self):
        a = _make_artifact(llm_provider_used="")
        errors = validate_artifact(a)
        self.assertTrue(any("llm_provider_used" in e for e in errors))

    def test_missing_prompt_template_version(self):
        a = _make_artifact(prompt_template_version="")
        errors = validate_artifact(a)
        self.assertTrue(any("prompt_template_version" in e for e in errors))

    def test_missing_content_text(self):
        a = _make_artifact(content_text="")
        errors = validate_artifact(a)
        self.assertTrue(any("content_text" in e for e in errors))

    def test_missing_timestamp(self):
        a = _make_artifact(generation_timestamp="")
        errors = validate_artifact(a)
        self.assertTrue(any("generation_timestamp" in e for e in errors))

    def test_multiple_errors_reported(self):
        a = _make_artifact(
            artifact_id="",
            artifact_type="bogus",  # type: ignore[arg-type]
            source_conversation_ids=[],
            llm_provider_used="",
            content_text="",
        )
        errors = validate_artifact(a)
        self.assertGreaterEqual(len(errors), 4)


if __name__ == "__main__":
    unittest.main()
