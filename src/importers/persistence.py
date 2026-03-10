"""Persistence helpers for normalized importer records.

Duplicate import policy (minimal, source-aware):
- identity key: (source, source_conversation_id)
- if a row already exists for that key, the incoming conversation is skipped
- skipped conversations do not create additional messages

This keeps importer behavior idempotent for repeat imports of the same export,
without changing the current schema or query shape.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from src.app.models import ImportedConversation, ImportedMessage
from src.app.models.db import db

from .contracts import NormalizedConversation, validate_provider_id


@dataclass(frozen=True)
class PersistResult:
    """Counts from one persistence pass."""

    imported_conversations: int
    imported_messages: int
    skipped_conversations: int


def persist_normalized_conversations(
    conversations: Iterable[NormalizedConversation],
) -> PersistResult:
    """Persist normalized conversations and messages in one transaction."""

    conversations_list = list(conversations)
    provider_id = ""
    if conversations_list:
        provider_ids = {validate_provider_id(conversation.source_provider) for conversation in conversations_list}
        if len(provider_ids) != 1:
            raise ValueError("persist_normalized_conversations expects a single provider per batch")
        provider_id = next(iter(provider_ids))

    incoming_ids = {conversation.source_conversation_id for conversation in conversations_list}
    existing_ids = {
        row.source_conversation_id
        for row in ImportedConversation.query.with_entities(ImportedConversation.source_conversation_id)
        .filter(
            ImportedConversation.source == provider_id,
            ImportedConversation.source_conversation_id.in_(incoming_ids),
        )
        .all()
    }

    imported_conversations = 0
    imported_messages = 0
    skipped_conversations = 0

    for conversation in conversations_list:
        if conversation.source_conversation_id in existing_ids:
            skipped_conversations += 1
            continue

        db_conversation = ImportedConversation(
            source=provider_id,
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
            imported_messages += 1

        imported_conversations += 1

    db.session.commit()
    return PersistResult(
        imported_conversations=imported_conversations,
        imported_messages=imported_messages,
        skipped_conversations=skipped_conversations,
    )
