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


_STOPWORDS = {
    "the",
    "and",
    "for",
    "with",
    "what",
    "when",
    "where",
    "which",
    "about",
    "have",
    "from",
    "that",
    "this",
    "your",
    "into",
    "note",
    "notes",
    "did",
}


def _to_iso_utc(timestamp_unix: float | None) -> str | None:
    if timestamp_unix is None:
        return None
    return datetime.fromtimestamp(timestamp_unix, tz=timezone.utc).isoformat(timespec="seconds")


def extract_query_terms(question: str) -> list[str]:
    """Extract compact lexical terms for retrieval and grounding checks."""

    tokens = re.findall(r"[a-z0-9]+", question.lower())
    terms: list[str] = []
    for token in tokens:
        if len(token) < 4:
            continue
        if token in _STOPWORDS:
            continue
        if token not in terms:
            terms.append(token)
    return terms


def retrieval_keyword_from_question(question: str) -> str:
    """Build compact retrieval keyword text from natural-language question."""

    return " ".join(extract_query_terms(question))


def _hit_overlap_count(hit: FederatedReadResult, terms: list[str]) -> int:
    haystack = hit.title.lower()
    return sum(1 for term in terms if term in haystack)


def build_answer_context(question: str, federated_hits: list[FederatedReadResult]) -> AnswerContext:
    """Build answering input context from federated retrieval output."""

    return AnswerContext(
        question=question.strip(),
        retrieved_at=datetime.now(tz=timezone.utc).isoformat(timespec="seconds"),
        hits=federated_hits,
    )


def format_grounded_answer(
    question: str,
    citations: list[AnswerCitation],
    status: str,
    evidence_titles: list[str] | None = None,
) -> str:
    """Render a concise grounded answer with visible evidence and citation markers."""

    evidence_titles = evidence_titles or []
    if status == "insufficient_evidence":
        if citations:
            details = "; ".join(
                f"[{idx + 1}] {citation.stable_id} ({citation.source_lane})"
                for idx, citation in enumerate(citations)
            )
            evidence = " | ".join(evidence_titles) if evidence_titles else "no clear lexical match"
            return (
                f"I found limited evidence for '{question}'. Evidence snippets: {evidence}. "
                f"Most relevant records: {details}. Please refine the question for a stronger grounded answer."
            )
        return (
            f"I could not find grounded evidence for '{question}' in canonical records. "
            "Try different keywords."
        )

    evidence = " | ".join(evidence_titles)
    citations_text = "; ".join(
        f"[{idx + 1}] {citation.stable_id} ({citation.source_lane})"
        for idx, citation in enumerate(citations)
    )
    return (
        f"Grounded evidence for '{question}': {evidence}. "
        f"Sources: {citations_text}."
    )


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

    terms = extract_query_terms(context.question)
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
    evidence_titles = [hit.title for hit in top_hits]

    if not terms:
        return GroundedAnswer(
            answer_text=format_grounded_answer(
                context.question,
                citations,
                "insufficient_evidence",
                evidence_titles=evidence_titles,
            ),
            status="insufficient_evidence",
            citations=citations,
            notes=["Question terms were too short or ambiguous for lexical grounding."],
        )

    strongest_overlap = _hit_overlap_count(top_hits[0], terms)
    if strongest_overlap == 0:
        return GroundedAnswer(
            answer_text=format_grounded_answer(
                context.question,
                citations,
                "insufficient_evidence",
                evidence_titles=evidence_titles,
            ),
            status="insufficient_evidence",
            citations=citations,
            notes=["Retrieved items did not lexically match the question terms."],
        )

    return GroundedAnswer(
        answer_text=format_grounded_answer(
            context.question,
            citations,
            "grounded",
            evidence_titles=evidence_titles,
        ),
        status="grounded",
        citations=citations,
        notes=[],
    )
