"""Minimal local answering boundary on top of federated retrieval."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import re

from src.retrieval import FederatedReadResult


@dataclass(frozen=True)
class AnswerCitation:
    """Provenance pointer for one cited canonical record."""

    source_lane: str
    stable_id: str
    timestamp: str | None
    source_metadata: dict[str, str]


@dataclass(frozen=True)
class AnswerContext:
    """Small context packet that answering consumes from federated retrieval."""

    question: str
    retrieved_at: str
    hits: list[FederatedReadResult]


@dataclass(frozen=True)
class GroundedAnswer:
    """Structured grounded answer result for CLI/UI consumption."""

    answer_text: str
    status: str
    citations: list[AnswerCitation]
    notes: list[str]


def _to_iso_utc(timestamp_unix: float | None) -> str | None:
    if timestamp_unix is None:
        return None
    return datetime.fromtimestamp(timestamp_unix, tz=timezone.utc).isoformat(timespec="seconds")


def _question_terms(question: str) -> set[str]:
    tokens = re.findall(r"[a-z0-9]+", question.lower())
    return {token for token in tokens if len(token) >= 3}


def _hit_overlap_count(hit: FederatedReadResult, terms: set[str]) -> int:
    haystack = hit.title.lower()
    return sum(1 for term in terms if term in haystack)


def build_answer_context(question: str, federated_hits: list[FederatedReadResult]) -> AnswerContext:
    """Build answering input context from federated retrieval output."""

    return AnswerContext(
        question=question.strip(),
        retrieved_at=datetime.now(tz=timezone.utc).isoformat(timespec="seconds"),
        hits=federated_hits,
    )


def format_grounded_answer(question: str, citations: list[AnswerCitation], status: str) -> str:
    """Render a concise grounded answer with visible citation markers."""

    if status == "insufficient_evidence":
        if citations:
            details = "; ".join(
                f"[{idx + 1}] {citation.stable_id} ({citation.source_lane})"
                for idx, citation in enumerate(citations)
            )
            return (
                f"I found limited evidence for '{question}'. Most relevant records: {details}. "
                "Please refine the question for a stronger grounded answer."
            )
        return (
            f"I could not find grounded evidence for '{question}' in canonical records. "
            "Try different keywords."
        )

    snippets = [
        f"[{idx + 1}] {citation.stable_id} ({citation.source_lane})"
        for idx, citation in enumerate(citations)
    ]
    joined = "; ".join(snippets)
    return f"Grounded answer for '{question}' based on: {joined}."


def answer_from_federated_hits(question: str, federated_hits: list[FederatedReadResult]) -> GroundedAnswer:
    """Generate a minimal grounded answer from federated retrieval hits."""

    context = build_answer_context(question, federated_hits)
    if not context.hits:
        return GroundedAnswer(
            answer_text=format_grounded_answer(context.question, [], "insufficient_evidence"),
            status="insufficient_evidence",
            citations=[],
            notes=["No federated retrieval hits were found."],
        )

    terms = _question_terms(context.question)
    ranked_hits = sorted(
        context.hits,
        key=lambda hit: _hit_overlap_count(hit, terms),
        reverse=True,
    )

    top_hits = ranked_hits[:3]
    citations = [
        AnswerCitation(
            source_lane=hit.source_lane,
            stable_id=hit.stable_id,
            timestamp=_to_iso_utc(hit.timestamp_unix),
            source_metadata=hit.source_metadata,
        )
        for hit in top_hits
    ]

    strongest_overlap = _hit_overlap_count(top_hits[0], terms) if terms else 0
    weak_evidence = bool(terms) and strongest_overlap == 0

    if weak_evidence:
        return GroundedAnswer(
            answer_text=format_grounded_answer(context.question, citations, "insufficient_evidence"),
            status="insufficient_evidence",
            citations=citations,
            notes=["Retrieved items did not lexically match the question terms."],
        )

    return GroundedAnswer(
        answer_text=format_grounded_answer(context.question, citations, "grounded"),
        status="grounded",
        citations=citations,
        notes=[],
    )
