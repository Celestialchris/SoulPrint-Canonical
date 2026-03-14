"""CLI entrypoint for federated read-only retrieval across storage lanes."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone

from .federated import federated_search


def _format_timestamp(timestamp_unix: float | None) -> str:
    if timestamp_unix is None:
        return "-"
    value = datetime.fromtimestamp(timestamp_unix, tz=timezone.utc)
    return value.isoformat(timespec="seconds")


def _render_metadata(source_metadata: dict[str, str]) -> str:
    return json.dumps(source_metadata, sort_keys=True, ensure_ascii=False)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Query mixed-lane federated retrieval results from SQLite."
    )
    parser.add_argument(
        "--db",
        default="instance/soulprint.db",
        help="SQLite file path (default: instance/soulprint.db)",
    )
    parser.add_argument(
        "query",
        nargs="?",
        default="",
        help="Optional keyword search across native and imported lanes",
    )
    parser.add_argument(
        "--limit-per-lane",
        type=int,
        default=10,
        help="Maximum rows fetched from each lane before merge (default: 10)",
    )
    args = parser.parse_args()

    rows = federated_search(args.db, keyword=args.query, limit_per_lane=args.limit_per_lane)
    if not rows:
        print("No federated results found.")
        return 0

    for row in rows:
        print(f"source_lane: {row.source_lane}")
        print(f"stable_id: {row.stable_id}")
        print(f"title: {row.title}")
        print(f"timestamp: {_format_timestamp(row.timestamp_unix)}")
        print(f"source_metadata: {_render_metadata(row.source_metadata)}")
        print("---")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
