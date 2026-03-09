"""Read/query helpers for imported conversations stored in SQLite."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from flask import Flask
from sqlalchemy import func

from src.app.models import ImportedConversation, ImportedMessage
from src.app.models.db import db


@dataclass(frozen=True)
class ImportedConversationSummary:
    """Minimal conversation metadata for list views."""

    id: int
    source: str
    source_conversation_id: str
    title: str
    created_at_unix: float | None
    updated_at_unix: float | None


@dataclass(frozen=True)
class ImportedMessageRecord:
    """Minimal imported message shape for detail views."""

    id: int
    source_message_id: str
    role: str
    content: str
    sequence_index: int
    created_at_unix: float | None


@dataclass(frozen=True)
class ImportedConversationDetail:
    """Conversation metadata with ordered messages."""

    id: int
    source: str
    source_conversation_id: str
    title: str
    created_at_unix: float | None
    updated_at_unix: float | None
    messages: list[ImportedMessageRecord]


@dataclass(frozen=True)
class ImportedConversationSearchResult:
    """Lightweight conversation row returned by keyword search."""

    id: int
    source: str
    source_conversation_id: str
    title: str


def _sqlite_app(sqlite_path: str | Path) -> Flask:
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{Path(sqlite_path).resolve()}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    return app


def list_imported_conversations(
    sqlite_path: str | Path,
    limit: int = 50,
) -> list[ImportedConversationSummary]:
    """Return imported conversation metadata ordered by newest first."""

    app = _sqlite_app(sqlite_path)
    with app.app_context():
        try:
            rows = (
                ImportedConversation.query.order_by(ImportedConversation.id.desc())
                .limit(limit)
                .all()
            )
            return [
                ImportedConversationSummary(
                    id=row.id,
                    source=row.source,
                    source_conversation_id=row.source_conversation_id,
                    title=row.title,
                    created_at_unix=row.created_at_unix,
                    updated_at_unix=row.updated_at_unix,
                )
                for row in rows
            ]
        finally:
            db.session.remove()
            db.engine.dispose()


def get_imported_conversation(
    sqlite_path: str | Path,
    conversation_id: int,
) -> ImportedConversationDetail | None:
    """Return one imported conversation with messages ordered by sequence."""

    app = _sqlite_app(sqlite_path)
    with app.app_context():
        try:
            row = ImportedConversation.query.filter_by(id=conversation_id).first()
            if row is None:
                return None

            messages = (
                ImportedMessage.query.filter_by(conversation_id=row.id)
                .order_by(ImportedMessage.sequence_index.asc())
                .all()
            )

            return ImportedConversationDetail(
                id=row.id,
                source=row.source,
                source_conversation_id=row.source_conversation_id,
                title=row.title,
                created_at_unix=row.created_at_unix,
                updated_at_unix=row.updated_at_unix,
                messages=[
                    ImportedMessageRecord(
                        id=message.id,
                        source_message_id=message.source_message_id,
                        role=message.role,
                        content=message.content,
                        sequence_index=message.sequence_index,
                        created_at_unix=message.created_at_unix,
                    )
                    for message in messages
                ],
            )
        finally:
            db.session.remove()
            db.engine.dispose()


def search_imported_conversations(
    sqlite_path: str | Path,
    keyword: str,
    limit: int = 50,
) -> list[ImportedConversationSearchResult]:
    """Search imported conversations by title and message content.

    The search is SQLite-backed and intentionally minimal: case-insensitive
    `LIKE` matching over conversation title and imported message content.
    """

    cleaned = keyword.strip()
    if not cleaned:
        return []

    pattern = f"%{cleaned.lower()}%"
    app = _sqlite_app(sqlite_path)
    with app.app_context():
        try:
            message_match_exists = (
                ImportedMessage.query.filter(
                    ImportedMessage.conversation_id == ImportedConversation.id,
                    func.lower(ImportedMessage.content).like(pattern),
                )
                .exists()
            )

            rows = (
                ImportedConversation.query.filter(
                    (func.lower(ImportedConversation.title).like(pattern))
                    | message_match_exists
                )
                .order_by(ImportedConversation.id.desc())
                .limit(limit)
                .all()
            )

            return [
                ImportedConversationSearchResult(
                    id=row.id,
                    source=row.source,
                    source_conversation_id=row.source_conversation_id,
                    title=row.title,
                )
                for row in rows
            ]
        finally:
            db.session.remove()
            db.engine.dispose()
