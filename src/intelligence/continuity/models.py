"""Typed continuity artifact models — derived, non-canonical, provenance-bound."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal
import uuid


ArtifactType = Literal[
    "summary",
    "decisions",
    "open_loops",
    "entity_map",
    "bridge",
]

VALID_ARTIFACT_TYPES: frozenset[str] = frozenset(
    ["summary", "decisions", "open_loops", "entity_map", "bridge"]
)


@dataclass(frozen=True)
class ContinuityArtifact:
    """One typed continuity artifact derived from canonical conversations.

    Continuity artifacts are derived, never canonical.  Each artifact stores
    full provenance: which conversations it was generated from, which LLM
    provider produced it, and which prompt template version was used.
    """

    artifact_id: str
    artifact_type: ArtifactType
    source_conversation_ids: list[str]
    generation_timestamp: str
    llm_provider_used: str
    prompt_template_version: str
    content_text: str
    derived_from: str = "canonical_conversations"
    artifact_kind: str = "continuity_artifact_v1"
    # Optional fields — default to None / empty
    parent_packet_ids: list[str] = field(default_factory=list)
    content_json: dict | None = None
    ambiguity_notes: str | None = None


def make_artifact_id() -> str:
    """Generate a stable artifact ID in the project convention."""
    return f"continuity_artifact:{uuid.uuid4()}"


def make_timestamp() -> str:
    """ISO 8601 UTC timestamp matching the project convention."""
    return datetime.now(tz=timezone.utc).isoformat(timespec="seconds")


def validate_artifact(artifact: ContinuityArtifact) -> list[str]:
    """Return a list of validation errors (empty means valid)."""
    errors: list[str] = []

    if not artifact.artifact_id or not artifact.artifact_id.startswith("continuity_artifact:"):
        errors.append("artifact_id must start with 'continuity_artifact:'")

    if artifact.artifact_type not in VALID_ARTIFACT_TYPES:
        errors.append(
            f"artifact_type must be one of {sorted(VALID_ARTIFACT_TYPES)}, "
            f"got '{artifact.artifact_type}'"
        )

    if not artifact.source_conversation_ids:
        errors.append("source_conversation_ids must not be empty")

    if not artifact.generation_timestamp:
        errors.append("generation_timestamp is required")

    if not artifact.llm_provider_used:
        errors.append("llm_provider_used is required")

    if not artifact.prompt_template_version:
        errors.append("prompt_template_version is required")

    if not artifact.content_text:
        errors.append("content_text is required")

    return errors
