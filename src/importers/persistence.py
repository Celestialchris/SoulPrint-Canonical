"""Persistence helpers for normalized importer records."""

from __future__ import annotations

from typing import Iterable

from src.app.models import ImportedConversation, ImportedMessage
from src.app.models.db import db

from .chatgpt import NormalizedConversation


def persist_normalized_conversations(
    conversations: Iterable[NormalizedConversation],
) -> list[ImportedConversation]:
    """Persist normalized conversations and messages in one transaction."""

    persisted: list[ImportedConversation] = []

    for conversation in conversations:
        db_conversation = ImportedConversation(
            source="chatgpt",
            source_conversation_id=conversation.source_conversation_id,
            title=conversation.title,
            created_at_unix=conversation.created_at,
            updated_at_unix=conversation.updated_at,
        )
        db.session.add(db_conversation)
        db.session.flush()

        for message in conversation.messages:
            db.session.add(
                ImportedMessage(
                    conversation_id=db_conversation.id,
                    source_message_id=message.source_message_id,
                    role=message.role,
                    content=message.content,
                    sequence_index=message.sequence_index,
                    created_at_unix=message.created_at,
                )
            )

        persisted.append(db_conversation)

    db.session.commit()
    return persisted
