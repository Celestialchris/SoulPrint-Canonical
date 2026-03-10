"""Minimal local answering APIs built on top of federated retrieval."""

from .local import (
    AnswerCitation,
    AnswerContext,
    GroundedAnswer,
    answer_from_federated_hits,
    build_answer_context,
    extract_query_terms,
    format_grounded_answer,
    retrieval_keyword_from_question,
)

__all__ = [
    "AnswerCitation",
    "AnswerContext",
    "GroundedAnswer",
    "build_answer_context",
    "answer_from_federated_hits",
    "format_grounded_answer",
    "extract_query_terms",
    "retrieval_keyword_from_question",
]

from .trace import (
    AnswerTrace,
    append_answer_trace,
    create_answer_trace,
    default_trace_store_path,
    get_answer_trace,
    list_answer_traces,
)

__all__.extend([
    "AnswerTrace",
    "create_answer_trace",
    "append_answer_trace",
    "list_answer_traces",
    "get_answer_trace",
    "default_trace_store_path",
])
