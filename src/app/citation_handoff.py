"""Explicit Answer Trace citation handoff helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class ResolvedCitationTarget:
    """UI-safe canonical handoff target for a routed citation."""

    label: str
    href: str
    lane: str
    stable_id: str


@dataclass(frozen=True)
class AnswerTraceCitationView:
    """Template-facing citation fields for Answer Trace inspection."""

    source_lane: str
    stable_id: str
    timestamp: str | None
    target: ResolvedCitationTarget | None
    evidence_text: str | None = None


def _string_value(value: object) -> str:
    if isinstance(value, str):
        return value.strip()
    return ""


def _parse_prefixed_numeric_id(stable_id: str, *, prefix: str) -> str | None:
    if not stable_id.startswith(prefix):
        return None

    record_id = stable_id.removeprefix(prefix)
    if not record_id.isdigit():
        return None

    return record_id


def resolve_citation_target(
    citation: Mapping[str, object],
) -> ResolvedCitationTarget | None:
    """Resolve a known canonical citation into a safe route target."""

    stable_id = _string_value(citation.get("stable_id"))
    source_lane = _string_value(citation.get("source_lane"))

    if source_lane == "native_memory":
        entry_id = _parse_prefixed_numeric_id(stable_id, prefix="memory:")
        if entry_id is not None:
            return ResolvedCitationTarget(
                label=stable_id,
                href=f"/memory/{entry_id}",
                lane=source_lane,
                stable_id=stable_id,
            )

    if source_lane == "imported_conversation":
        conversation_id = _parse_prefixed_numeric_id(
            stable_id,
            prefix="imported_conversation:",
        )
        if conversation_id is not None:
            return ResolvedCitationTarget(
                label=stable_id,
                href=f"/imported/{conversation_id}/explorer",
                lane=source_lane,
                stable_id=stable_id,
            )

    return None


def build_answer_trace_citation_view(
    citation: Mapping[str, object],
) -> AnswerTraceCitationView:
    """Build a small read-only citation view model for Answer Trace templates."""

    stable_id = _string_value(citation.get("stable_id"))
    source_lane = _string_value(citation.get("source_lane"))
    timestamp = _string_value(citation.get("timestamp")) or None
    evidence_text = _string_value(citation.get("evidence_text")) or None

    return AnswerTraceCitationView(
        source_lane=source_lane,
        stable_id=stable_id,
        timestamp=timestamp,
        target=resolve_citation_target(citation),
        evidence_text=evidence_text,
    )
