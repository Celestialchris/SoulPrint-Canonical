"""CLI entrypoint for minimal Memory Passport export."""

from __future__ import annotations

import argparse

from .export import export_memory_passport


def main() -> int:
    parser = argparse.ArgumentParser(description="Export a SoulPrint Memory Passport package.")
    parser.add_argument(
        "output_dir",
        help="Directory where memory-passport-v1/ will be written",
    )
    parser.add_argument(
        "--db",
        default="instance/soulprint.db",
        help="SQLite file path (default: instance/soulprint.db)",
    )
    parser.add_argument(
        "--no-markdown",
        action="store_true",
        help="Skip derived markdown files",
    )
    args = parser.parse_args()

    result = export_memory_passport(
        sqlite_path=args.db,
        output_dir=args.output_dir,
        include_markdown=not args.no_markdown,
    )
    print(f"Exported Memory Passport: {result.package_dir}")
    print(f"Manifest: {result.manifest_path}")
    print(f"Canonical units: {result.canonical_units}")
    print(f"Derived units: {result.derived_units}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
