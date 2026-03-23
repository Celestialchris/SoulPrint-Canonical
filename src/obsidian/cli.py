"""CLI entrypoint for Obsidian Bridge export and refresh."""

from __future__ import annotations

import argparse
import sys

from .exporter import export_vault, refresh_vault


def _build_export_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Export SoulPrint vault to Obsidian markdown notes."
    )
    parser.add_argument(
        "--db",
        default="instance/soulprint.db",
        help="SQLite file path (default: instance/soulprint.db)",
    )
    parser.add_argument(
        "--vault",
        required=True,
        help="Target Obsidian vault directory path",
    )
    parser.add_argument(
        "--incremental",
        action="store_true",
        help="Skip conversations that already have notes in the vault",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be created without writing files",
    )
    return parser


def _build_refresh_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Refresh AUTO blocks in existing Obsidian vault notes."
    )
    parser.add_argument(
        "--db",
        default="instance/soulprint.db",
        help="SQLite file path (default: instance/soulprint.db)",
    )
    parser.add_argument(
        "--vault",
        required=True,
        help="Existing Obsidian vault directory path",
    )
    return parser


def _run_export(argv: list[str]) -> int:
    parser = _build_export_parser()
    args = parser.parse_args(argv)

    result = export_vault(
        db_path=args.db,
        vault_path=args.vault,
        incremental=args.incremental,
        dry_run=args.dry_run,
    )

    prefix = "[dry run] " if args.dry_run else ""
    print(f"{prefix}Exported {result.chat_count} chat notes to Chats/")
    print(f"{prefix}Generated {result.theme_count} theme notes in Themes/")
    print(f"{prefix}Created {result.daily_count} daily notes in Daily/")
    print(
        f"{prefix}Created {result.provider_count} provider references in References/"
    )
    if result.skipped:
        print(f"Skipped {result.skipped} existing notes (incremental)")
    if result.errors:
        print(f"Errors: {len(result.errors)}")
        for err in result.errors:
            print(f"  - {err}")
    if not args.dry_run:
        print(f"\nDone. Open {args.vault} in Obsidian.")
    return 0


def _run_refresh(argv: list[str]) -> int:
    parser = _build_refresh_parser()
    args = parser.parse_args(argv)

    result = refresh_vault(db_path=args.db, vault_path=args.vault)

    print(f"Updated {result.updated} notes")
    if result.skipped:
        print(f"Skipped {result.skipped} notes (missing AUTO markers)")
    if result.errors:
        print(f"Errors: {len(result.errors)}")
        for err in result.errors:
            print(f"  - {err}")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] == "refresh":
        return _run_refresh(args[1:])
    if args and args[0] == "export":
        return _run_export(args[1:])
    return _run_export(args)


if __name__ == "__main__":
    raise SystemExit(main())
