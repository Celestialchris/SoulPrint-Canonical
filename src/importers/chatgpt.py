"""ChatGPT exporter adapter using the shared importer normalization contract."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .contracts import (
    PROVIDER_CHATGPT,
    ConversationImporter,
    NormalizedConversation,
    NormalizedMessage,
)


DEFAULT_TITLE = "Untitled Conversation"


class ChatGPTImporter(ConversationImporter):
    """Concrete importer adapter for ChatGPT export payloads."""

    provider_id = PROVIDER_CHATGPT

    def parse_payload(self, payload: Any) -> list[NormalizedConversation]:
        return parse_chatgpt_export(payload)


def looks_like_chatgpt_export(payload: Any) -> bool:
    """Return True when payload matches the supported ChatGPT export shape.

    Supports both the standard list format and the rescue dict format
    (``{"_meta": ..., "conversations": {...}}``).
    """

    items = _unwrap_rescue_payload(payload)
    if items is None:
        return False
    return any(isinstance(item, dict) and "mapping" in item for item in items)


def parse_chatgpt_export_file(path: str | Path) -> list[NormalizedConversation]:
    """Load a ChatGPT conversations export JSON file and normalize it."""

    with Path(path).open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    return parse_chatgpt_export(payload)


def parse_chatgpt_export(payload: Any) -> list[NormalizedConversation]:
    """Normalize the ChatGPT export payload into conversation/message records.

    Accepts both the standard list format and the rescue dict format.
    """

    items = _unwrap_rescue_payload(payload)
    if items is None:
        raise ValueError("ChatGPT export payload must be a list of conversations or a rescue dict")

    normalized: list[NormalizedConversation] = []
    for idx, raw_conversation in enumerate(items):
        if not isinstance(raw_conversation, dict):
            continue

        source_id = str(raw_conversation.get("id") or f"conversation-{idx}")
        raw_title = raw_conversation.get("title")
        title = raw_title.strip() if isinstance(raw_title, str) and raw_title.strip() else DEFAULT_TITLE

        mapping = raw_conversation.get("mapping")
        ordered_messages = _extract_ordered_messages(mapping)

        normalized.append(
            NormalizedConversation(
                source_provider=PROVIDER_CHATGPT,
                source_conversation_id=source_id,
                title=title,
                created_at=_to_float_or_none(raw_conversation.get("create_time")),
                updated_at=_to_float_or_none(raw_conversation.get("update_time")),
                messages=ordered_messages,
                source_metadata={},
            )
        )

    return normalized


def _unwrap_rescue_payload(payload: Any) -> list[Any] | None:
    """Return a list of conversation dicts from either format, or None."""

    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict) and "conversations" in payload:
        convos = payload["conversations"]
        if isinstance(convos, dict):
            return list(convos.values())
    return None


def _extract_ordered_messages(mapping: Any) -> list[NormalizedMessage]:
    if not isinstance(mapping, dict):
        return []

    root_ids = [node_id for node_id, node in mapping.items() if isinstance(node, dict) and node.get("parent") is None]
    visited: set[str] = set()
    walk_order: list[str] = []

    def visit(start_ids: list[str]) -> None:
        stack = list(reversed(start_ids))
        while stack:
            node_id = stack.pop()
            if node_id in visited:
                continue
            visited.add(node_id)
            walk_order.append(node_id)

            node = mapping.get(node_id)
            if not isinstance(node, dict):
                continue
            children = node.get("children", [])
            for child_id in reversed(children):
                if isinstance(child_id, str) and child_id not in visited:
                    stack.append(child_id)

    visit(root_ids)
    visit([nid for nid in mapping if nid not in visited])

    normalized_messages: list[NormalizedMessage] = []
    for node_id in walk_order:
        node = mapping.get(node_id)
        if not isinstance(node, dict):
            continue

        message = node.get("message")
        if not isinstance(message, dict):
            continue

        author = message.get("author")
        role = author.get("role") if isinstance(author, dict) else "unknown"
        content = _extract_content_text(message.get("content"))
        if not content:
            continue

        normalized_messages.append(
            NormalizedMessage(
                source_message_id=str(message.get("id") or node_id),
                role=str(role or "unknown"),
                content=content,
                sequence_index=len(normalized_messages),
                created_at=_to_float_or_none(message.get("create_time") or node.get("create_time")),
            )
        )

    return normalized_messages


def _extract_content_text(content: Any) -> str:
    if not isinstance(content, dict):
        return ""

    parts = content.get("parts")
    if not isinstance(parts, list):
        return ""

    cleaned_parts = [part.strip() for part in parts if isinstance(part, str) and part.strip()]
    return "\n".join(cleaned_parts)


def _to_float_or_none(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
