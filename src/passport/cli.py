"""CLI entrypoint for minimal Memory Passport export."""

from __future__ import annotations

import argparse
import json
import sys

from .export import export_memory_passport
from .validator import validate_memory_passport


def _build_export_parser() -> argparse.ArgumentParser:
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
    return parser


def _build_validate_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate a SoulPrint Memory Passport package.")
    parser.add_argument(
        "passport_path",
        help="Path to memory-passport-v1/ or its manifest.json",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON diagnostics",
    )
    return parser


def _run_export(argv: list[str]) -> int:
    parser = _build_export_parser()
    args = parser.parse_args(argv)

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


def _run_validate(argv: list[str]) -> int:
    parser = _build_validate_parser()
    args = parser.parse_args(argv)

    result = validate_memory_passport(args.passport_path)
    if args.json:
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    else:
        print(f"Status: {result.status}")
        checked_counts = ", ".join(
            f"{key}={value}" for key, value in sorted(result.checked_counts.items())
        )
        print(f"Checked counts: {checked_counts}")
        for provider_id, counts in result.provider_summary.items():
            provider_counts = ", ".join(
                f"{key}={value}" for key, value in sorted(counts.items()) if value
            )
            print(f"Provider {provider_id}: {provider_counts or 'no canonical units'}")
        for warning in result.warnings:
            print(f"Warning: {warning.message}")
        for error in result.errors:
            print(f"Error: {error.message}")

    return 0 if result.status != "invalid" else 1


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] == "validate":
        return _run_validate(args[1:])
    if args and args[0] == "export":
        return _run_export(args[1:])
    return _run_export(args)


if __name__ == "__main__":
    raise SystemExit(main())
