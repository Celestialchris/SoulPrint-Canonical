"""Claude exporter adapter using the shared importer normalization contract."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .contracts import (
    PROVIDER_CLAUDE,
    ConversationImporter,
    NormalizedConversation,
    NormalizedMessage,
)


DEFAULT_TITLE = "Untitled Conversation"


class ClaudeImporter(ConversationImporter):
    """Concrete importer adapter for Claude export payloads."""

    provider_id = PROVIDER_CLAUDE

    def parse_payload(self, payload: Any) -> list[NormalizedConversation]:
        return parse_claude_export(payload)


def looks_like_claude_export(payload: Any) -> bool:
    """Return True when payload matches a supported Claude export shape."""

    if _looks_like_claude_conversation(payload):
        return True

    return isinstance(payload, list) and any(
        _looks_like_claude_conversation(item) for item in payload
    )


def parse_claude_export_file(path: str | Path) -> list[NormalizedConversation]:
    """Load a Claude export JSON file and normalize it."""

    with Path(path).open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    return parse_claude_export(payload)


def parse_claude_export(payload: Any) -> list[NormalizedConversation]:
    """Normalize Claude exports into canonical conversation/message records."""

    if _looks_like_claude_conversation(payload):
        raw_conversations = [payload]
    elif isinstance(payload, list):
        raw_conversations = payload
    else:
        raise ValueError(
            "Claude export payload must be one conversation object or a list of conversations"
        )

    normalized: list[NormalizedConversation] = []
    for idx, raw_conversation in enumerate(raw_conversations):
        if not isinstance(raw_conversation, dict):
            continue
        if not _looks_like_claude_conversation(raw_conversation):
            raise ValueError("Claude conversation entries must include a chat_messages list")

        source_id = str(
            raw_conversation.get("uuid")
            or raw_conversation.get("conversation_id")
            or f"claude-conversation-{idx}"
        )
        raw_title = raw_conversation.get("name")
        title = (
            raw_title.strip()
            if isinstance(raw_title, str) and raw_title.strip()
            else DEFAULT_TITLE
        )

        raw_messages = raw_conversation.get("chat_messages")
        if not isinstance(raw_messages, list):
            raise ValueError("Claude conversation chat_messages must be a list")

        normalized.append(
            NormalizedConversation(
                source_provider=PROVIDER_CLAUDE,
                source_conversation_id=source_id,
                title=title,
                created_at=_parse_timestamp_or_none(raw_conversation.get("created_at")),
                updated_at=_parse_timestamp_or_none(raw_conversation.get("updated_at")),
                messages=_extract_ordered_messages(raw_messages, source_id=source_id),
                source_metadata={},
            )
        )

    return normalized


def _looks_like_claude_conversation(payload: Any) -> bool:
    return isinstance(payload, dict) and isinstance(payload.get("chat_messages"), list)


def _extract_ordered_messages(
    raw_messages: list[Any],
    *,
    source_id: str,
) -> list[NormalizedMessage]:
    indexed_messages = list(enumerate(raw_messages))
    indexed_messages.sort(key=lambda item: (_message_index(item[1], fallback=item[0]), item[0]))

    normalized_messages: list[NormalizedMessage] = []
    for original_index, raw_message in indexed_messages:
        if not isinstance(raw_message, dict):
            continue

        content = _extract_message_text(raw_message)
        if not content:
            continue

        normalized_messages.append(
            NormalizedMessage(
                source_message_id=str(
                    raw_message.get("uuid") or f"{source_id}-message-{original_index}"
                ),
                role=_normalize_sender(raw_message.get("sender")),
                content=content,
                sequence_index=len(normalized_messages),
                created_at=_parse_timestamp_or_none(raw_message.get("created_at")),
            )
        )

    return normalized_messages


def _message_index(raw_message: Any, *, fallback: int) -> int:
    if isinstance(raw_message, dict):
        value = raw_message.get("index")
        if isinstance(value, int):
            return value
        if isinstance(value, float) and value.is_integer():
            return int(value)
    return fallback


def _normalize_sender(sender: Any) -> str:
    cleaned = str(sender or "unknown").strip().lower()
    if cleaned == "human":
        return "user"
    if cleaned == "assistant":
        return "assistant"
    if cleaned == "system":
        return "system"
    return cleaned or "unknown"


def _extract_message_text(raw_message: Any) -> str:
    if not isinstance(raw_message, dict):
        return ""

    raw_text = raw_message.get("text")
    if isinstance(raw_text, str) and raw_text.strip():
        return raw_text.strip()

    fragments = _extract_text_fragments(raw_message.get("content"))
    cleaned_fragments = [fragment.strip() for fragment in fragments if fragment.strip()]
    return "\n\n".join(cleaned_fragments)


def _extract_text_fragments(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]

    if isinstance(value, list):
        fragments: list[str] = []
        for item in value:
            fragments.extend(_extract_text_fragments(item))
        return fragments

    if not isinstance(value, dict):
        return []

    block_type = value.get("type")
    if block_type in {"text", "voice_note"}:
        text = value.get("text")
        return [text] if isinstance(text, str) else []
    if block_type == "thinking":
        thinking = value.get("thinking")
        return [thinking] if isinstance(thinking, str) else []
    if block_type == "tool_result":
        return _extract_text_fragments(value.get("content"))
    if block_type == "tool_use":
        return _extract_text_fragments(value.get("input"))

    fragments: list[str] = []
    for key in ("text", "thinking", "content"):
        fragments.extend(_extract_text_fragments(value.get(key)))
    return fragments


def _parse_timestamp_or_none(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = value.strip()
        if not cleaned:
            return None
        try:
            return float(cleaned)
        except ValueError:
            pass
        try:
            return datetime.fromisoformat(cleaned.replace("Z", "+00:00")).astimezone(
                timezone.utc
            ).timestamp()
        except ValueError:
            return None
    return None
