"""Derived lineage suggestions between imported conversations.

Proposes inspectable, non-authoritative relationship suggestions based on
lexical heuristics.  Never mutates canonical conversation records.

Relation types:
  - continues:   likely continuation of an earlier thread
  - forks_from:  shares a topic but diverges in direction
  - revisits:    returns to an earlier topic after a gap
  - supersedes:  covers the same ground but is more recent
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Literal


# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------

RelationType = Literal["continues", "forks_from", "revisits", "supersedes"]

VALID_RELATION_TYPES: frozenset[str] = frozenset(
    ["continues", "forks_from", "revisits", "supersedes"]
)


@dataclass(frozen=True)
class LineageSuggestion:
    """One derived lineage suggestion — inspectable, non-authoritative."""

    source_conversation_id: int
    target_conversation_id: int
    target_title: str
    relation_type: RelationType
    confidence: float          # 0.0 – 1.0
    signals: list[str]         # human-readable explanation of what contributed
    derived_from: str = "canonical_conversations"


# ---------------------------------------------------------------------------
# Stop words (reuses the same set as topics.py)
# ---------------------------------------------------------------------------

_STOP_WORDS = frozenset(
    "a an the and or but in on at to for of is it this that with from by "
    "be are was were been have has had do does did will would could should "
    "can may might shall not no yes so if then than too also just about up "
    "out how what when where who which why all each every some any many "
    "more most other another such only own same into over after before "
    "between through during without again further once here there these "
    "those me my he she we they its his her our their you your i "
    "new chat help use make using used get".split()
)

_CONTINUATION_PHRASES = [
    "continuing from",
    "as we discussed",
    "following up on",
    "picking up where",
    "back to our",
    "to continue",
    "last time we",
    "building on",
    "as a follow-up",
    "resuming",
]


# ---------------------------------------------------------------------------
# Tokenization
# ---------------------------------------------------------------------------


def _significant_words(text: str) -> set[str]:
    """Extract significant lowercase words (>= 3 chars, not stopwords)."""
    tokens = re.findall(r"[a-zA-Z]{3,}", text.lower())
    return {t for t in tokens if t not in _STOP_WORDS}


# ---------------------------------------------------------------------------
# Heuristic scorers — each returns (score, signal_description)
# ---------------------------------------------------------------------------


def _title_overlap_score(
    title_a: str, title_b: str,
) -> tuple[float, str | None]:
    """Jaccard similarity on significant title words."""
    words_a = _significant_words(title_a)
    words_b = _significant_words(title_b)
    if not words_a or not words_b:
        return 0.0, None

    intersection = words_a & words_b
    union = words_a | words_b
    jaccard = len(intersection) / len(union)
    if jaccard < 0.1:
        return 0.0, None
    shared = ", ".join(sorted(intersection)[:5])
    return jaccard, f"title overlap ({shared})"


def _temporal_proximity_score(
    ts_a: float | None, ts_b: float | None,
) -> tuple[float, str | None]:
    """Score based on time gap between two conversations."""
    if ts_a is None or ts_b is None:
        return 0.0, None

    gap_seconds = abs(ts_a - ts_b)
    gap_hours = gap_seconds / 3600

    if gap_hours <= 48:
        return 1.0, "within 48 hours"
    if gap_hours <= 168:   # 7 days
        return 0.5, "within 7 days"
    if gap_hours <= 720:   # 30 days
        return 0.2, "within 30 days"
    return 0.0, None


def _keyword_overlap_score(
    messages_a: list[str], messages_b: list[str],
) -> tuple[float, str | None]:
    """Overlap of significant words from message content (first few messages)."""
    text_a = " ".join(messages_a[:5])
    text_b = " ".join(messages_b[:5])
    words_a = _significant_words(text_a)
    words_b = _significant_words(text_b)
    if not words_a or not words_b:
        return 0.0, None

    intersection = words_a & words_b
    union = words_a | words_b
    jaccard = len(intersection) / len(union)
    if jaccard < 0.05:
        return 0.0, None
    count = len(intersection)
    return min(jaccard * 1.5, 1.0), f"{count} shared content keywords"


def _continuation_keyword_score(
    messages: list[str],
) -> tuple[float, str | None]:
    """Check first messages for explicit continuation phrases."""
    if not messages:
        return 0.0, None

    first_text = " ".join(messages[:2]).lower()
    for phrase in _CONTINUATION_PHRASES:
        if phrase in first_text:
            return 1.0, f'continuation phrase: "{phrase}"'
    return 0.0, None


# ---------------------------------------------------------------------------
# Relation type inference
# ---------------------------------------------------------------------------


def _infer_relation_type(
    title_score: float,
    temporal_score: float,
    keyword_score: float,
    continuation_score: float,
    source_ts: float | None,
    target_ts: float | None,
) -> RelationType:
    """Infer the most likely relation type from heuristic scores."""
    if continuation_score > 0 or (temporal_score >= 1.0 and title_score >= 0.2):
        return "continues"

    if title_score >= 0.5 and target_ts and source_ts and target_ts > source_ts:
        return "supersedes"

    if title_score >= 0.2 and temporal_score <= 0.2:
        return "revisits"

    return "forks_from"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


@dataclass
class ConversationSummary:
    """Lightweight conversation descriptor for lineage scoring.

    This avoids coupling to SQLAlchemy models — callers build these
    from whatever data source they have.
    """
    id: int
    title: str
    created_at_unix: float | None = None
    message_previews: list[str] = field(default_factory=list)


def suggest_lineage(
    source: ConversationSummary,
    candidates: list[ConversationSummary],
    limit: int = 3,
    min_confidence: float = 0.15,
) -> list[LineageSuggestion]:
    """Score candidates and return top lineage suggestions for *source*.

    Heuristic priority (per spec):
      1. Title overlap  (weight 0.40)
      2. Temporal proximity  (weight 0.20)
      3. Keyword overlap from content  (weight 0.30)
      4. Continuation keywords  (weight 0.10)

    Returns at most *limit* suggestions above *min_confidence*, sorted by
    confidence descending.
    """
    W_TITLE = 0.40
    W_TEMPORAL = 0.20
    W_KEYWORD = 0.30
    W_CONTINUATION = 0.10

    suggestions: list[LineageSuggestion] = []

    for candidate in candidates:
        if candidate.id == source.id:
            continue

        signals: list[str] = []

        title_score, title_sig = _title_overlap_score(source.title, candidate.title)
        temporal_score, temporal_sig = _temporal_proximity_score(
            source.created_at_unix, candidate.created_at_unix,
        )
        keyword_score, keyword_sig = _keyword_overlap_score(
            source.message_previews, candidate.message_previews,
        )
        continuation_score, continuation_sig = _continuation_keyword_score(
            source.message_previews,
        )

        if title_sig:
            signals.append(title_sig)
        if temporal_sig:
            signals.append(temporal_sig)
        if keyword_sig:
            signals.append(keyword_sig)
        if continuation_sig:
            signals.append(continuation_sig)

        confidence = (
            title_score * W_TITLE
            + temporal_score * W_TEMPORAL
            + keyword_score * W_KEYWORD
            + continuation_score * W_CONTINUATION
        )

        if confidence < min_confidence:
            continue

        relation = _infer_relation_type(
            title_score, temporal_score, keyword_score, continuation_score,
            source.created_at_unix, candidate.created_at_unix,
        )

        suggestions.append(LineageSuggestion(
            source_conversation_id=source.id,
            target_conversation_id=candidate.id,
            target_title=candidate.title,
            relation_type=relation,
            confidence=round(confidence, 3),
            signals=signals,
        ))

    suggestions.sort(key=lambda s: s.confidence, reverse=True)
    return suggestions[:limit]
