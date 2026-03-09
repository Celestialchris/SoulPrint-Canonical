"""CLI entrypoint for inspecting imported conversations in SQLite."""

from __future__ import annotations

import argparse

from .query import get_imported_conversation, list_imported_conversations


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect imported ChatGPT conversations in SQLite.")
    parser.add_argument(
        "--db",
        default="instance/soulprint.db",
        help="SQLite file path (default: instance/soulprint.db)",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="List imported conversations")
    list_parser.add_argument("--limit", type=int, default=20, help="Maximum rows to print")

    show_parser = subparsers.add_parser("show", help="Show one conversation and its messages")
    show_parser.add_argument("conversation_id", type=int, help="Imported conversation numeric id")

    args = parser.parse_args()

    if args.command == "list":
        rows = list_imported_conversations(args.db, limit=args.limit)
        for row in rows:
            print(f"{row.id}\t{row.source}\t{row.title}\t{row.source_conversation_id}")
        return 0

    detail = get_imported_conversation(args.db, args.conversation_id)
    if detail is None:
        print(f"No conversation found for id={args.conversation_id}")
        return 1

    print(f"id: {detail.id}")
    print(f"source: {detail.source}")
    print(f"source_conversation_id: {detail.source_conversation_id}")
    print(f"title: {detail.title}")
    print("messages:")
    for message in detail.messages:
        print(f"  [{message.sequence_index}] {message.role}: {message.content}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
