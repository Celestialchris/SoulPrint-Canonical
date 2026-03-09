"""Read/query helpers for imported conversations stored in SQLite."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from flask import Flask

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


def get_imported_conversation(
    sqlite_path: str | Path,
    conversation_id: int,
) -> ImportedConversationDetail | None:
    """Return one imported conversation with messages ordered by sequence."""

    app = _sqlite_app(sqlite_path)
    with app.app_context():
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
