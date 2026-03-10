"""CLI entrypoint for importing supported conversation exports into SQLite.

This keeps Milestone 1 architecture intact by reusing the existing
normalization and persistence layers.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from pathlib import Path

from flask import Flask

from src.app.models.db import db

from .contracts import PROVIDER_CHATGPT
from .errors import (
    ImportProviderDetectionError,
    MalformedImportFileError,
    UnsupportedImportFormatError,
)
from .persistence import PersistResult, persist_normalized_conversations
from .registry import available_import_providers, parse_import_file


@dataclass(frozen=True)
class ImportExecutionResult:
    """Provider-aware result for one import run."""

    provider_id: str
    persist_result: PersistResult
    warnings: list[str] = field(default_factory=list)

    @property
    def imported_conversations(self) -> int:
        return self.persist_result.imported_conversations

    @property
    def imported_messages(self) -> int:
        return self.persist_result.imported_messages

    @property
    def skipped_conversations(self) -> int:
        return self.persist_result.skipped_conversations


def import_conversation_export_to_sqlite(
    export_path: str | Path,
    sqlite_path: str | Path,
    *,
    provider: str | None = None,
) -> ImportExecutionResult:
    """Import one supported provider export into SQLite."""

    export_path = Path(export_path)
    sqlite_path = Path(sqlite_path).resolve()
    sqlite_path.parent.mkdir(parents=True, exist_ok=True)

    parsed = parse_import_file(export_path, provider_hint=provider)

    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{sqlite_path}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    with app.app_context():
        db.create_all()
        persist_result = persist_normalized_conversations(parsed.conversations)
        db.session.remove()
        db.engine.dispose()

    return ImportExecutionResult(
        provider_id=parsed.provider_id,
        persist_result=persist_result,
        warnings=parsed.warnings,
    )


def import_chatgpt_export_to_sqlite(export_path: str | Path, sqlite_path: str | Path) -> PersistResult:
    """Import a ChatGPT export file into a SQLite database.

    Returns:
        PersistResult: imported/skipped conversation counts and imported message count.
    """

    return import_conversation_export_to_sqlite(
        export_path,
        sqlite_path,
        provider=PROVIDER_CHATGPT,
    ).persist_result


def main() -> int:
    """Run CLI import command for one supported conversation export file."""

    parser = argparse.ArgumentParser(description="Import a supported conversation export into SQLite.")
    parser.add_argument("export_path", help="Path to provider export JSON file")
    parser.add_argument(
        "--db",
        default="instance/soulprint.db",
        help="Target SQLite file path (default: instance/soulprint.db)",
    )
    parser.add_argument(
        "--provider",
        default="auto",
        choices=("auto", *available_import_providers()),
        help="Force provider id instead of auto-detecting from payload (default: auto)",
    )
    args = parser.parse_args()

    try:
        result = import_conversation_export_to_sqlite(
            args.export_path,
            args.db,
            provider=args.provider,
        )
    except (ImportProviderDetectionError, MalformedImportFileError, UnsupportedImportFormatError) as exc:
        print(str(exc))
        return 1

    print(f"Provider: {result.provider_id}")
    print(
        f"Imported {result.imported_conversations} conversations "
        f"({result.skipped_conversations} skipped duplicates) and "
        f"{result.imported_messages} messages into {args.db}"
    )
    for warning in result.warnings:
        print(f"Warning: {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
