"""CLI entrypoint for importing ChatGPT exports into SQLite.

This keeps Milestone 1 architecture intact by reusing the existing
normalization and persistence layers.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from flask import Flask

from src.app.models.db import db

from .chatgpt import parse_chatgpt_export_file
from .persistence import PersistResult, persist_normalized_conversations


def import_chatgpt_export_to_sqlite(export_path: str | Path, sqlite_path: str | Path) -> PersistResult:
    """Import a ChatGPT export file into a SQLite database.

    Returns:
        PersistResult: imported/skipped conversation counts and imported message count.
    """

    export_path = Path(export_path)
    sqlite_path = Path(sqlite_path).resolve()
    sqlite_path.parent.mkdir(parents=True, exist_ok=True)

    conversations = parse_chatgpt_export_file(export_path)

    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{sqlite_path}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    with app.app_context():
        db.create_all()
        result = persist_normalized_conversations(conversations)
        db.session.remove()
        db.engine.dispose()

    return result


def main() -> int:
    """Run CLI import command for one ChatGPT export file."""

    parser = argparse.ArgumentParser(description="Import a ChatGPT export into SQLite.")
    parser.add_argument("export_path", help="Path to ChatGPT export JSON file")
    parser.add_argument(
        "--db",
        default="instance/soulprint.db",
        help="Target SQLite file path (default: instance/soulprint.db)",
    )
    args = parser.parse_args()

    result = import_chatgpt_export_to_sqlite(args.export_path, args.db)
    print(
        f"Imported {result.imported_conversations} conversations "
        f"({result.skipped_conversations} skipped duplicates) and "
        f"{result.imported_messages} messages into {args.db}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
