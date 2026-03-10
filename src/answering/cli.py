"""CLI entrypoint for minimal local grounded answering."""

from __future__ import annotations

import argparse
import json

from src.retrieval import federated_search

from .local import answer_from_federated_hits, retrieval_keyword_from_question
from .trace import (
    append_answer_trace,
    create_answer_trace,
    default_trace_store_path,
    get_answer_trace,
    list_answer_traces,
)


def _print_trace(trace: dict[str, object]) -> None:
    print(json.dumps(trace, ensure_ascii=False, sort_keys=True, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Ask a minimal grounded question over federated SoulPrint retrieval."
    )
    parser.add_argument(
        "--db",
        default="instance/soulprint.db",
        help="SQLite file path (default: instance/soulprint.db)",
    )
    parser.add_argument("question", nargs="?", help="Question text to ground against canonical records")
    parser.add_argument(
        "--limit-per-lane",
        type=int,
        default=10,
        help="Maximum rows fetched from each lane before merge (default: 10)",
    )
    parser.add_argument(
        "--emit-trace",
        action="store_true",
        help="Append a derived Answer Trace JSONL entry after generating an answer.",
    )
    parser.add_argument(
        "--trace-store",
        default="",
        help="Optional explicit Answer Trace JSONL path (defaults to sibling of --db).",
    )
    parser.add_argument(
        "--list-traces",
        type=int,
        default=0,
        help="List newest derived answer traces (count).",
    )
    parser.add_argument(
        "--show-trace",
        default="",
        help="Show one derived answer trace by trace_id.",
    )

    args = parser.parse_args()
    trace_store = args.trace_store or str(default_trace_store_path(args.db))

    if args.list_traces > 0:
        for trace in list_answer_traces(trace_store, limit=args.list_traces):
            _print_trace(trace)
        return 0

    if args.show_trace:
        trace = get_answer_trace(trace_store, args.show_trace)
        if trace is None:
            print(f"trace not found: {args.show_trace}")
            return 1

        _print_trace(trace)
        return 0

    if not args.question:
        parser.error("question is required unless --list-traces or --show-trace is used")

    retrieval_keyword = retrieval_keyword_from_question(args.question)
    hits = federated_search(args.db, keyword=retrieval_keyword, limit_per_lane=args.limit_per_lane)
    result = answer_from_federated_hits(args.question, hits)

    print(f"status: {result.status}")
    print(f"answer: {result.answer_text}")
    print("citations:")
    if result.citations:
        for citation in result.citations:
            print(
                json.dumps(
                    {
                        "source_lane": citation.source_lane,
                        "stable_id": citation.stable_id,
                        "timestamp": citation.timestamp,
                        "source_metadata": citation.source_metadata,
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                )
            )
    else:
        print("[]")

    if result.notes:
        print("notes:")
        for note in result.notes:
            print(f"- {note}")

    if args.emit_trace:
        trace = create_answer_trace(
            question=args.question,
            retrieval_terms=retrieval_keyword,
            answer=result,
        )
        append_answer_trace(trace_store, trace)
        print(f"trace_id: {trace.trace_id}")
        print(f"trace_store: {trace_store}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
