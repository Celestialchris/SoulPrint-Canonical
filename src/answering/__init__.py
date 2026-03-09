"""Minimal local answering APIs built on top of federated retrieval."""

from .local import (
    AnswerCitation,
    AnswerContext,
    GroundedAnswer,
    answer_from_federated_hits,
    build_answer_context,
    format_grounded_answer,
)

__all__ = [
    "AnswerCitation",
    "AnswerContext",
    "GroundedAnswer",
    "build_answer_context",
    "answer_from_federated_hits",
    "format_grounded_answer",
]
