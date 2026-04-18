"""Tests for continuity packet generation service."""

from __future__ import annotations

import json
import unittest
from dataclasses import dataclass

from src.intelligence.continuity.models import ContinuityArtifact
from src.intelligence.continuity.service import (
    ContinuityPacketResult,
    generate_continuity_packet,
    _build_transcript,
    _parse_provider_response,
)
from src.intelligence.continuity.store import list_artifacts, get_artifact
from tests.temp_helpers import make_test_temp_dir


# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------


@dataclass
class FakeMessage:
    role: str
    content: str
    sequence_index: int


@dataclass
class FakeConversation:
    id: int
    title: str
    messages: list


_STRUCTURED_RESPONSE = json.dumps({
    "summary": "Discussion about local-first storage using SQLite as canonical ledger.",
    "decisions": [
        "Use SQLite for canonical storage",
        "Keep derived artifacts in JSONL",
    ],
    "open_loops": [
        "Whether to add FTS5 for search",
    ],
    "entity_map": [
        "SQLite",
        "JSONL",
        "Flask",
    ],
})


class StructuredStubProvider:
    """Returns a well-formed JSON response for continuity extraction."""

    @property
    def provider_name(self) -> str:
        return "structured_stub"

    def complete(self, system: str, user: str, **_kwargs) -> str:
        return _STRUCTURED_RESPONSE


class MarkdownFencedProvider:
    """Returns JSON wrapped in markdown code fences."""

    @property
    def provider_name(self) -> str:
        return "fenced_stub"

    def complete(self, system: str, user: str, **_kwargs) -> str:
        return f"```json\n{_STRUCTURED_RESPONSE}\n```"


class EmptyFieldsProvider:
    """Returns valid JSON with some empty fields."""

    @property
    def provider_name(self) -> str:
        return "empty_fields_stub"

    def complete(self, system: str, user: str, **_kwargs) -> str:
        return json.dumps({
            "summary": "Brief discussion.",
            "decisions": [],
            "open_loops": [],
            "entity_map": [],
        })


class BrokenProvider:
    """Raises an exception on complete."""

    @property
    def provider_name(self) -> str:
        return "broken"

    def complete(self, system: str, user: str, **_kwargs) -> str:
        raise RuntimeError("Simulated provider failure")


class GarbageProvider:
    """Returns non-JSON text."""

    @property
    def provider_name(self) -> str:
        return "garbage"

    def complete(self, system: str, user: str, **_kwargs) -> str:
        return "This is not JSON at all."


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_conversation(
    conv_id: int = 42,
    title: str = "Test conversation about storage",
) -> FakeConversation:
    return FakeConversation(
        id=conv_id,
        title=title,
        messages=[
            FakeMessage(role="user", content="Should we use SQLite?", sequence_index=0),
            FakeMessage(role="assistant", content="Yes, for local-first.", sequence_index=1),
            FakeMessage(role="user", content="What about search?", sequence_index=2),
            FakeMessage(role="assistant", content="FTS5 is an option.", sequence_index=3),
        ],
    )


# ---------------------------------------------------------------------------
# Tests — transcript building
# ---------------------------------------------------------------------------


class TranscriptBuildingTest(unittest.TestCase):

    def test_transcript_orders_by_sequence_index(self):
        conv = FakeConversation(
            id=1, title="Order test",
            messages=[
                FakeMessage(role="assistant", content="Second", sequence_index=1),
                FakeMessage(role="user", content="First", sequence_index=0),
            ],
        )
        transcript = _build_transcript(conv)
        lines = transcript.split("\n")
        self.assertIn("First", lines[0])
        self.assertIn("Second", lines[1])

    def test_transcript_format(self):
        conv = _make_conversation()
        transcript = _build_transcript(conv)
        self.assertIn("[user]: Should we use SQLite?", transcript)
        self.assertIn("[assistant]: Yes, for local-first.", transcript)


# ---------------------------------------------------------------------------
# Tests — response parsing
# ---------------------------------------------------------------------------


class ResponseParsingTest(unittest.TestCase):

    def test_parse_clean_json(self):
        parsed = _parse_provider_response(_STRUCTURED_RESPONSE)
        self.assertIn("summary", parsed)
        self.assertIn("decisions", parsed)

    def test_parse_markdown_fenced_json(self):
        fenced = f"```json\n{_STRUCTURED_RESPONSE}\n```"
        parsed = _parse_provider_response(fenced)
        self.assertEqual(parsed["summary"], "Discussion about local-first storage using SQLite as canonical ledger.")

    def test_parse_plain_fenced_json(self):
        fenced = f"```\n{_STRUCTURED_RESPONSE}\n```"
        parsed = _parse_provider_response(fenced)
        self.assertIn("decisions", parsed)

    def test_parse_garbage_raises(self):
        with self.assertRaises((json.JSONDecodeError, ValueError)):
            _parse_provider_response("not json")


# ---------------------------------------------------------------------------
# Tests — successful generation
# ---------------------------------------------------------------------------


class SuccessfulGenerationTest(unittest.TestCase):

    def setUp(self):
        self.workdir = make_test_temp_dir(self, "continuity-svc")
        self.store_path = self.workdir / "continuity_artifacts.jsonl"
        self.conv = _make_conversation()
        self.provider = StructuredStubProvider()

    def test_returns_packet_result(self):
        result = generate_continuity_packet(self.conv, self.provider, self.store_path)
        self.assertIsInstance(result, ContinuityPacketResult)
        self.assertIsNone(result.error)

    def test_produces_four_artifact_types(self):
        result = generate_continuity_packet(self.conv, self.provider, self.store_path)
        types = {a.artifact_type for a in result.artifacts}
        self.assertEqual(types, {"summary", "decisions", "open_loops", "entity_map"})

    def test_all_artifacts_are_continuity_artifacts(self):
        result = generate_continuity_packet(self.conv, self.provider, self.store_path)
        for a in result.artifacts:
            self.assertIsInstance(a, ContinuityArtifact)

    def test_stable_id_matches_conversation(self):
        result = generate_continuity_packet(self.conv, self.provider, self.store_path)
        self.assertEqual(result.conversation_stable_id, "imported_conversation:42")

    def test_source_conversation_ids_on_every_artifact(self):
        result = generate_continuity_packet(self.conv, self.provider, self.store_path)
        for a in result.artifacts:
            self.assertEqual(a.source_conversation_ids, ["imported_conversation:42"])

    def test_provider_name_persisted(self):
        result = generate_continuity_packet(self.conv, self.provider, self.store_path)
        for a in result.artifacts:
            self.assertEqual(a.llm_provider_used, "structured_stub")

    def test_prompt_version_persisted(self):
        result = generate_continuity_packet(self.conv, self.provider, self.store_path)
        for a in result.artifacts:
            self.assertEqual(a.prompt_template_version, "v1")

    def test_custom_prompt_version(self):
        result = generate_continuity_packet(
            self.conv, self.provider, self.store_path, prompt_version="v2-beta"
        )
        for a in result.artifacts:
            self.assertEqual(a.prompt_template_version, "v2-beta")

    def test_generation_timestamp_present(self):
        result = generate_continuity_packet(self.conv, self.provider, self.store_path)
        for a in result.artifacts:
            self.assertIn("T", a.generation_timestamp)
            self.assertTrue(a.generation_timestamp.endswith("+00:00"))

    def test_artifact_ids_unique(self):
        result = generate_continuity_packet(self.conv, self.provider, self.store_path)
        ids = [a.artifact_id for a in result.artifacts]
        self.assertEqual(len(ids), len(set(ids)))
        for aid in ids:
            self.assertTrue(aid.startswith("continuity_artifact:"))

    def test_summary_content_text(self):
        result = generate_continuity_packet(self.conv, self.provider, self.store_path)
        summaries = [a for a in result.artifacts if a.artifact_type == "summary"]
        self.assertEqual(len(summaries), 1)
        self.assertIn("SQLite", summaries[0].content_text)

    def test_decisions_content_json(self):
        result = generate_continuity_packet(self.conv, self.provider, self.store_path)
        decisions = [a for a in result.artifacts if a.artifact_type == "decisions"]
        self.assertEqual(len(decisions), 1)
        self.assertIsNotNone(decisions[0].content_json)
        self.assertEqual(len(decisions[0].content_json["decisions"]), 2)

    def test_open_loops_content_json(self):
        result = generate_continuity_packet(self.conv, self.provider, self.store_path)
        loops = [a for a in result.artifacts if a.artifact_type == "open_loops"]
        self.assertEqual(len(loops), 1)
        self.assertIn("FTS5", loops[0].content_text)

    def test_entity_map_content_json(self):
        result = generate_continuity_packet(self.conv, self.provider, self.store_path)
        entities = [a for a in result.artifacts if a.artifact_type == "entity_map"]
        self.assertEqual(len(entities), 1)
        self.assertIn("SQLite", entities[0].content_json["entity_map"])


# ---------------------------------------------------------------------------
# Tests — persistence
# ---------------------------------------------------------------------------


class PersistenceTest(unittest.TestCase):

    def setUp(self):
        self.workdir = make_test_temp_dir(self, "continuity-persist")
        self.store_path = self.workdir / "continuity_artifacts.jsonl"

    def test_artifacts_written_to_store(self):
        conv = _make_conversation()
        result = generate_continuity_packet(conv, StructuredStubProvider(), self.store_path)

        stored = list_artifacts(self.store_path)
        self.assertEqual(len(stored), len(result.artifacts))

    def test_stored_artifacts_retrievable_by_id(self):
        conv = _make_conversation()
        result = generate_continuity_packet(conv, StructuredStubProvider(), self.store_path)

        for a in result.artifacts:
            fetched = get_artifact(self.store_path, a.artifact_id)
            self.assertIsNotNone(fetched)
            self.assertEqual(fetched["artifact_type"], a.artifact_type)
            self.assertEqual(fetched["llm_provider_used"], "structured_stub")

    def test_provider_and_prompt_version_in_store(self):
        conv = _make_conversation()
        generate_continuity_packet(
            conv, StructuredStubProvider(), self.store_path, prompt_version="v2"
        )

        stored = list_artifacts(self.store_path)
        for row in stored:
            self.assertEqual(row["llm_provider_used"], "structured_stub")
            self.assertEqual(row["prompt_template_version"], "v2")

    def test_nothing_persisted_on_error(self):
        conv = _make_conversation()
        generate_continuity_packet(conv, BrokenProvider(), self.store_path)

        stored = list_artifacts(self.store_path)
        self.assertEqual(stored, [])


# ---------------------------------------------------------------------------
# Tests — graceful failure
# ---------------------------------------------------------------------------


class GracefulFailureTest(unittest.TestCase):

    def setUp(self):
        self.workdir = make_test_temp_dir(self, "continuity-fail")
        self.store_path = self.workdir / "continuity_artifacts.jsonl"
        self.conv = _make_conversation()

    def test_no_provider_returns_error(self):
        result = generate_continuity_packet(self.conv, None, self.store_path)
        self.assertIsNotNone(result.error)
        self.assertIn("No LLM provider configured", result.error)
        self.assertEqual(result.artifacts, [])

    def test_no_provider_stable_id_still_set(self):
        result = generate_continuity_packet(self.conv, None, self.store_path)
        self.assertEqual(result.conversation_stable_id, "imported_conversation:42")

    def test_provider_exception_returns_error(self):
        result = generate_continuity_packet(self.conv, BrokenProvider(), self.store_path)
        self.assertIsNotNone(result.error)
        self.assertIn("Provider call failed", result.error)
        self.assertEqual(result.artifacts, [])

    def test_garbage_response_returns_error(self):
        result = generate_continuity_packet(self.conv, GarbageProvider(), self.store_path)
        self.assertIsNotNone(result.error)
        self.assertIn("parse", result.error.lower())
        self.assertEqual(result.artifacts, [])


# ---------------------------------------------------------------------------
# Tests — empty fields
# ---------------------------------------------------------------------------


class EmptyFieldsTest(unittest.TestCase):

    def setUp(self):
        self.workdir = make_test_temp_dir(self, "continuity-empty")
        self.store_path = self.workdir / "continuity_artifacts.jsonl"

    def test_empty_lists_produce_only_summary(self):
        conv = _make_conversation()
        result = generate_continuity_packet(conv, EmptyFieldsProvider(), self.store_path)
        self.assertIsNone(result.error)
        types = {a.artifact_type for a in result.artifacts}
        self.assertEqual(types, {"summary"})

    def test_empty_fields_do_not_create_blank_artifacts(self):
        conv = _make_conversation()
        result = generate_continuity_packet(conv, EmptyFieldsProvider(), self.store_path)
        for a in result.artifacts:
            self.assertTrue(len(a.content_text) > 0)


# ---------------------------------------------------------------------------
# Tests — markdown fence tolerance
# ---------------------------------------------------------------------------


class MarkdownFenceTest(unittest.TestCase):

    def setUp(self):
        self.workdir = make_test_temp_dir(self, "continuity-fence")
        self.store_path = self.workdir / "continuity_artifacts.jsonl"

    def test_fenced_response_produces_artifacts(self):
        conv = _make_conversation()
        result = generate_continuity_packet(conv, MarkdownFencedProvider(), self.store_path)
        self.assertIsNone(result.error)
        self.assertGreater(len(result.artifacts), 0)


# ---------------------------------------------------------------------------
# Tests — no canonical mutation
# ---------------------------------------------------------------------------


class NoCanonicalMutationTest(unittest.TestCase):
    """Verify the service never modifies the conversation object."""

    def test_conversation_unchanged_after_generation(self):
        conv = _make_conversation()
        original_id = conv.id
        original_title = conv.title
        original_msg_count = len(conv.messages)
        original_contents = [m.content for m in conv.messages]

        workdir = make_test_temp_dir(self, "continuity-immut")
        store_path = workdir / "continuity_artifacts.jsonl"
        generate_continuity_packet(conv, StructuredStubProvider(), store_path)

        self.assertEqual(conv.id, original_id)
        self.assertEqual(conv.title, original_title)
        self.assertEqual(len(conv.messages), original_msg_count)
        self.assertEqual([m.content for m in conv.messages], original_contents)


if __name__ == "__main__":
    unittest.main()
