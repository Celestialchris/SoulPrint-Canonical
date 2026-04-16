"""Grok (xAI) exporter adapter using the shared importer normalization contract."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .contracts import (
    PROVIDER_GROK,
    ConversationImporter,
    NormalizedConversation,
    NormalizedMessage,
)


DEFAULT_TITLE = "Untitled Conversation"


class GrokImporter(ConversationImporter):
    """Concrete importer adapter for Grok (xAI) export payloads."""

    provider_id = PROVIDER_GROK

    def parse_payload(self, payload: Any) -> list[NormalizedConversation]:
        return parse_grok_export(payload)


def looks_like_grok_export(payload: Any) -> bool:
    """Return True when payload matches the supported Grok export shape.

    Grok exports use ``{"conversations": [...]}`` where each item has both
    a ``"conversation"`` key and a ``"responses"`` key.  This is distinct from
    the ChatGPT rescue-dict format (items use ``"mapping"``) and Claude format
    (items use ``"chat_messages"``).
    """

    if not isinstance(payload, dict):
        return False
    conversations = payload.get("conversations")
    if not isinstance(conversations, list):
        return False
    return any(
        isinstance(item, dict) and "conversation" in item and "responses" in item
        for item in conversations
    )


def parse_grok_export_file(path: str | Path) -> list[NormalizedConversation]:
    """Load a Grok conversations export JSON file and normalize it."""

    with Path(path).open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    return parse_grok_export(payload)


def parse_grok_export(payload: Any) -> list[NormalizedConversation]:
    """Normalize the Grok export payload into conversation/message records."""

    if not isinstance(payload, dict) or "conversations" not in payload:
        raise ValueError("Grok export payload must be a dict with a 'conversations' key")
    if not isinstance(payload["conversations"], list):
        raise ValueError("Grok export 'conversations' must be a list, got: " + type(payload["conversations"]).__name__)
    return _parse_wrapped_conversations(payload)


def _extract_timestamp(ts: Any) -> float | None:
    """Extract a Unix timestamp (seconds) from all Grok timestamp formats.

    Handles four formats:
    1. MongoDB BSON: {"$date": {"$numberLong": "1737381600000"}}
    2. ISO in $date: {"$date": "2025-01-20T14:00:00.000Z"}
    3. ISO 8601 string: "2025-01-20T14:00:00.000Z"
    4. Raw numeric: int or float (ms if > 1e12, else seconds)
    """

    if ts is None:
        return None

    # MongoDB BSON / $date wrapper
    if isinstance(ts, dict):
        date_val = ts.get("$date")
        if date_val is None:
            return None
        # Nested $numberLong: {"$date": {"$numberLong": "ms"}}
        if isinstance(date_val, dict):
            number_long = date_val.get("$numberLong")
            if number_long is None:
                return None
            try:
                ms = int(number_long)
                return ms / 1000.0
            except (TypeError, ValueError):
                return None
        # ISO string inside $date: {"$date": "2025-01-20T14:00:00.000Z"}
        if isinstance(date_val, str):
            try:
                dt = datetime.fromisoformat(date_val.replace("Z", "+00:00"))
                return dt.timestamp()
            except ValueError:
                return None
        # Raw numeric inside $date
        if isinstance(date_val, (int, float)):
            return float(date_val) / 1000.0 if date_val > 1e12 else float(date_val)
        return None

    # ISO 8601 string
    if isinstance(ts, str):
        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            return dt.timestamp()
        except ValueError:
            return None

    # Raw numeric
    if isinstance(ts, (int, float)):
        return float(ts) / 1000.0 if ts > 1e12 else float(ts)

    return None


def _normalize_role(sender: str) -> str:
    """Map Grok sender values to canonical role strings."""

    lowered = str(sender).lower()
    if lowered == "human":
        return "user"
    return lowered


def _parse_wrapped_conversations(payload: dict) -> list[NormalizedConversation]:
    """Parse the ``{"conversations": [...]}`` wrapper into normalized records."""

    items = payload.get("conversations", [])
    result: list[NormalizedConversation] = []

    for idx, item in enumerate(items):
        if not isinstance(item, dict):
            continue

        conv = item.get("conversation")
        responses = item.get("responses")
        if not isinstance(conv, dict) or not isinstance(responses, list) or not responses:
            continue

        conv_id = str(conv.get("id") or f"grok-conv-{idx}")
        raw_title = conv.get("title")
        title = (
            raw_title.strip()
            if isinstance(raw_title, str) and raw_title.strip()
            else DEFAULT_TITLE
        )

        created_at = _extract_timestamp(conv.get("create_time"))
        updated_at = _extract_timestamp(conv.get("modify_time"))

        messages: list[NormalizedMessage] = []
        first_model: str | None = None

        for idx, resp_wrapper in enumerate(responses):
            if not isinstance(resp_wrapper, dict):
                continue
            resp = resp_wrapper.get("response")
            if not isinstance(resp, dict):
                continue

            msg_id = resp.get("_id")
            if not msg_id:
                msg_id = f"{conv_id}-msg-{idx}"

            raw_message = resp.get("message")
            if raw_message is None:
                continue
            content = str(raw_message).strip() if not isinstance(raw_message, str) else raw_message.strip()
            if not content:
                continue

            role = _normalize_role(str(resp.get("sender", "unknown")))
            msg_ts = _extract_timestamp(resp.get("create_time"))

            model = resp.get("model")
            if model and first_model is None:
                first_model = str(model)

            messages.append(
                NormalizedMessage(
                    source_message_id=str(msg_id),
                    role=role,
                    content=content,
                    sequence_index=len(messages),
                    created_at=msg_ts,
                )
            )

        result.append(
            NormalizedConversation(
                source_provider=PROVIDER_GROK,
                source_conversation_id=conv_id,
                title=title,
                created_at=created_at,
                updated_at=updated_at,
                messages=messages,
                source_metadata={"grok_model": first_model} if first_model else {},
            )
        )

    return result
