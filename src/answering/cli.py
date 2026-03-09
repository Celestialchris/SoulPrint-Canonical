"""CLI entrypoint for minimal local grounded answering."""

from __future__ import annotations

import argparse
import json

from src.retrieval import federated_search

from .local import answer_from_federated_hits


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Ask a minimal grounded question over federated SoulPrint retrieval."
    )
    parser.add_argument(
        "--db",
        default="instance/soulprint.db",
        help="SQLite file path (default: instance/soulprint.db)",
    )
    parser.add_argument("question", help="Question text to ground against canonical records")
    parser.add_argument(
        "--limit-per-lane",
        type=int,
        default=10,
        help="Maximum rows fetched from each lane before merge (default: 10)",
    )

    args = parser.parse_args()
    hits = federated_search(args.db, keyword=args.question, limit_per_lane=args.limit_per_lane)
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

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
