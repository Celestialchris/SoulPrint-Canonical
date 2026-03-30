"""Gemini exporter adapter using the shared importer normalization contract.

Supports three real export shapes:

1. Google Takeout MyActivity.json (with responses) — flat activity log entries
   with ``header``, ``title`` prefixed by ``"Prompted "``, ``time``, and model
   responses in ``safeHtmlItem``.  Entries are grouped into synthetic
   conversations using time-proximity clustering.

2. Google Takeout MyActivity.json (prompts only) — same structure as (1) but
   without ``"Prompted "`` prefix or ``safeHtmlItem``.  Each entry is mapped to
   a single-message conversation (legacy behavior).

3. Conversational JSON — per-conversation objects with ``messages`` arrays
   containing ``role``/``content`` pairs.  This shape is produced by third-party
   Chrome extensions (AI Chat Exporter, gemini-chat-exporter, etc.) and
   preserves full user+model turns.

All shapes can appear as a JSON array of entries/conversations or as a single
object (conversational shape only).
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .contracts import (
    PROVIDER_GEMINI,
    ConversationImporter,
    NormalizedConversation,
    NormalizedMessage,
)


DEFAULT_TITLE = "Untitled Conversation"

# Google Takeout activity entries use this header for Gemini interactions.
_TAKEOUT_HEADER = "Gemini Apps"

# Real Google Takeout MyActivity entries prefix the prompt with this string.
_PROMPTED_PREFIX = "Prompted "

# Default gap threshold for time-proximity grouping (seconds).
DEFAULT_ACTIVITY_GAP_SECONDS = 30 * 60  # 30 minutes


class GeminiImporter(ConversationImporter):
    """Concrete importer adapter for Gemini export payloads."""

    provider_id = PROVIDER_GEMINI

    def parse_payload(self, payload: Any) -> list[NormalizedConversation]:
        return parse_gemini_export(payload)


# ---------------------------------------------------------------------------
# Auto-detection helpers
# ---------------------------------------------------------------------------


def looks_like_gemini_myactivity(payload: Any) -> bool:
    """Return True when payload matches real Google Takeout MyActivity format.

    This is the format produced by takeout.google.com with JSON selected for
    "My Activity > Gemini Apps".  Entries have ``title`` prefixed with
    ``"Prompted "`` and model responses in ``safeHtmlItem``.
    """

    if not isinstance(payload, list):
        return False

    return any(
        isinstance(item, dict)
        and item.get("header") == _TAKEOUT_HEADER
        and isinstance(item.get("title"), str)
        and item["title"].startswith(_PROMPTED_PREFIX)
        for item in payload
    )


def looks_like_gemini_takeout(payload: Any) -> bool:
    """Return True when payload matches the Google Takeout MyActivity shape."""

    if not isinstance(payload, list):
        return False

    return any(
        isinstance(item, dict)
        and isinstance(item.get("header"), str)
        and _TAKEOUT_HEADER.lower() in item["header"].lower()
        and isinstance(item.get("title"), str)
        for item in payload
    )


def looks_like_gemini_conversations(payload: Any) -> bool:
    """Return True when payload matches a conversational Gemini export."""

    if _looks_like_gemini_conversation(payload):
        return True

    return isinstance(payload, list) and any(
        _looks_like_gemini_conversation(item) for item in payload
    )


def looks_like_gemini_export(payload: Any) -> bool:
    """Return True when payload matches any supported Gemini export shape."""

    return (
        looks_like_gemini_myactivity(payload)
        or looks_like_gemini_takeout(payload)
        or looks_like_gemini_conversations(payload)
    )


# ---------------------------------------------------------------------------
# File-level convenience
# ---------------------------------------------------------------------------


def parse_gemini_export_file(path: str | Path) -> list[NormalizedConversation]:
    """Load a Gemini export JSON file and normalize it."""

    with Path(path).open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    return parse_gemini_export(payload)


# ---------------------------------------------------------------------------
# Core parser
# ---------------------------------------------------------------------------


def parse_gemini_export(
    payload: Any,
    *,
    activity_gap_seconds: int = DEFAULT_ACTIVITY_GAP_SECONDS,
) -> list[NormalizedConversation]:
    """Normalize Gemini exports into canonical conversation/message records.

    Dispatches to the appropriate parser based on detected payload shape.
    """

    if looks_like_gemini_myactivity(payload):
        return _parse_myactivity(payload, gap_seconds=activity_gap_seconds)

    if looks_like_gemini_takeout(payload):
        return _parse_takeout_activity(payload)

    if _looks_like_gemini_conversation(payload):
        return _parse_conversations([payload])

    if isinstance(payload, list):
        conversation_items = [
            item for item in payload if _looks_like_gemini_conversation(item)
        ]
        if conversation_items:
            return _parse_conversations(conversation_items)

    raise ValueError(
        "Gemini export payload must be either a Google Takeout MyActivity array "
        "or a conversation object/array with a messages list"
    )


# ---------------------------------------------------------------------------
# Shape A — Google Takeout MyActivity.json
# ---------------------------------------------------------------------------


def _parse_takeout_activity(payload: list[Any]) -> list[NormalizedConversation]:
    """Parse Google Takeout flat activity entries into conversations.

    Each activity entry becomes a single-message conversation because the
    Takeout format does not group entries into conversations or include model
    responses.
    """

    normalized: list[NormalizedConversation] = []
    for idx, entry in enumerate(payload):
        if not isinstance(entry, dict):
            continue

        header = entry.get("header")
        if not isinstance(header, str) or _TAKEOUT_HEADER.lower() not in header.lower():
            continue

        raw_title = entry.get("title")
        if not isinstance(raw_title, str) or not raw_title.strip():
            continue

        prompt_text = raw_title.strip()
        created_at = _parse_iso_timestamp(entry.get("time"))

        # Derive a stable source id from prompt text + timestamp so re-imports
        # are idempotent even though Takeout entries have no explicit id.
        source_id = _derive_takeout_source_id(prompt_text, created_at, idx)

        # Use a truncated version of the prompt as the conversation title.
        title = prompt_text[:120] + ("\u2026" if len(prompt_text) > 120 else "")

        messages = [
            NormalizedMessage(
                source_message_id=f"{source_id}-prompt",
                role="user",
                content=prompt_text,
                sequence_index=0,
                created_at=created_at,
            )
        ]

        normalized.append(
            NormalizedConversation(
                source_provider=PROVIDER_GEMINI,
                source_conversation_id=source_id,
                title=title,
                created_at=created_at,
                updated_at=created_at,
                messages=messages,
                source_metadata={"gemini_export_shape": "takeout"},
            )
        )

    return normalized


def _derive_takeout_source_id(
    prompt_text: str,
    created_at: float | None,
    fallback_index: int,
) -> str:
    """Build a stable identifier for a Takeout activity entry."""

    identity = f"{prompt_text}|{created_at or fallback_index}"
    digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:16]
    return f"gemini-takeout-{digest}"


# ---------------------------------------------------------------------------
# Shape A2 — Google Takeout MyActivity.json (with responses + grouping)
# ---------------------------------------------------------------------------


def _parse_myactivity(
    payload: list[Any],
    *,
    gap_seconds: int = DEFAULT_ACTIVITY_GAP_SECONDS,
) -> list[NormalizedConversation]:
    """Parse real Google Takeout MyActivity entries into grouped conversations.

    Entries with ``"Prompted "`` title prefix are extracted, sorted by time,
    grouped by time proximity, and each group becomes one conversation with
    user/assistant message pairs.
    """

    entries = _extract_activity_entries(payload)
    if not entries:
        return []

    entries.sort(key=lambda e: e["timestamp"])
    groups = _group_entries_by_time_proximity(entries, gap_seconds=gap_seconds)

    normalized: list[NormalizedConversation] = []
    for group in groups:
        conv_id = _derive_myactivity_group_id(group)
        first_entry = group[0]
        title = first_entry["prompt"][:80] + ("\u2026" if len(first_entry["prompt"]) > 80 else "")

        messages: list[NormalizedMessage] = []
        for entry in group:
            seq = len(messages)
            messages.append(
                NormalizedMessage(
                    source_message_id=f"{conv_id}-msg-{seq}",
                    role="user",
                    content=entry["prompt"],
                    sequence_index=seq,
                    created_at=entry["timestamp"],
                )
            )
            if entry["response"]:
                seq = len(messages)
                messages.append(
                    NormalizedMessage(
                        source_message_id=f"{conv_id}-msg-{seq}",
                        role="assistant",
                        content=entry["response"],
                        sequence_index=seq,
                        created_at=entry["timestamp"],
                    )
                )

        normalized.append(
            NormalizedConversation(
                source_provider=PROVIDER_GEMINI,
                source_conversation_id=conv_id,
                title=title,
                created_at=first_entry["timestamp"],
                updated_at=group[-1]["timestamp"],
                messages=messages,
                source_metadata={"gemini_export_shape": "myactivity"},
            )
        )

    return normalized


def _extract_activity_entries(payload: list[Any]) -> list[dict[str, Any]]:
    """Extract prompt/response/timestamp dicts from MyActivity entries."""

    entries: list[dict[str, Any]] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        if item.get("header") != _TAKEOUT_HEADER:
            continue
        raw_title = item.get("title")
        if not isinstance(raw_title, str) or not raw_title.startswith(_PROMPTED_PREFIX):
            continue

        prompt = raw_title[len(_PROMPTED_PREFIX):].strip()
        if not prompt:
            continue

        timestamp = _parse_iso_timestamp(item.get("time"))
        response = _extract_safe_html_response(item)

        entries.append({
            "prompt": prompt,
            "response": response,
            "timestamp": timestamp,
        })

    return entries


def _extract_safe_html_response(entry: dict[str, Any]) -> str:
    """Extract plain text from safeHtmlItem, returning empty string if absent."""

    safe_items = entry.get("safeHtmlItem")
    if not isinstance(safe_items, list) or not safe_items:
        return ""

    first = safe_items[0]
    if not isinstance(first, dict):
        return ""

    html = first.get("html")
    if not isinstance(html, str) or not html.strip():
        return ""

    return _html_to_text(html)


def _html_to_text(html: str) -> str:
    """Convert HTML to plain text.

    Uses BeautifulSoup if available, falls back to regex tag stripping.
    """

    try:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "lxml")
        return soup.get_text(separator="\n").strip()
    except ImportError:
        # Fallback: strip tags with regex.
        text = re.sub(r"<[^>]+>", "\n", html)
        # Collapse multiple newlines and strip.
        text = re.sub(r"\n{2,}", "\n", text)
        return text.strip()


def _group_entries_by_time_proximity(
    entries: list[dict[str, Any]],
    *,
    gap_seconds: int = DEFAULT_ACTIVITY_GAP_SECONDS,
) -> list[list[dict[str, Any]]]:
    """Group sorted entries into conversations by time proximity.

    Walks through entries in order. When the gap between consecutive entries
    exceeds ``gap_seconds``, a new group starts.  Entries without timestamps
    are attached to the current group.
    """

    if not entries:
        return []

    groups: list[list[dict[str, Any]]] = [[entries[0]]]
    for entry in entries[1:]:
        prev_ts = groups[-1][-1]["timestamp"]
        curr_ts = entry["timestamp"]

        if prev_ts is not None and curr_ts is not None:
            if curr_ts - prev_ts > gap_seconds:
                groups.append([])

        groups[-1].append(entry)

    return groups


def _derive_myactivity_group_id(group: list[dict[str, Any]]) -> str:
    """Build a deterministic conversation ID from a group of activity entries.

    Uses the first entry's timestamp plus all prompt texts so re-imports
    produce identical IDs.
    """

    first_ts = group[0]["timestamp"]
    prompts = "|".join(entry["prompt"] for entry in group)
    identity = f"{first_ts}|{prompts}"
    digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:16]
    return f"gemini_activity_{digest}"


# ---------------------------------------------------------------------------
# Shape B — Conversational JSON (Chrome extensions / manual exports)
# ---------------------------------------------------------------------------


def _parse_conversations(raw_conversations: list[Any]) -> list[NormalizedConversation]:
    """Parse conversational Gemini export objects."""

    normalized: list[NormalizedConversation] = []
    for idx, raw_conversation in enumerate(raw_conversations):
        if not isinstance(raw_conversation, dict):
            continue

        source_id = _extract_conversation_id(raw_conversation, idx)
        raw_title = raw_conversation.get("title")
        title = (
            raw_title.strip()
            if isinstance(raw_title, str) and raw_title.strip()
            else DEFAULT_TITLE
        )

        raw_messages = raw_conversation.get("messages")
        if not isinstance(raw_messages, list):
            raise ValueError("Gemini conversation messages must be a list")

        exported_at = _parse_iso_timestamp(raw_conversation.get("exportedAt"))

        normalized.append(
            NormalizedConversation(
                source_provider=PROVIDER_GEMINI,
                source_conversation_id=source_id,
                title=title,
                created_at=_first_message_timestamp(raw_messages) or exported_at,
                updated_at=exported_at,
                messages=_extract_ordered_messages(raw_messages, source_id=source_id),
                source_metadata={"gemini_export_shape": "conversations"},
            )
        )

    return normalized


def _looks_like_gemini_conversation(payload: Any) -> bool:
    """Return True if payload is a single conversational Gemini export object."""

    if not isinstance(payload, dict):
        return False

    messages = payload.get("messages")
    if not isinstance(messages, list) or not messages:
        return False

    # Distinguish from Claude exports (which use chat_messages) and ChatGPT
    # exports (which use mapping).  Gemini conversational exports use
    # "messages" with role values like "user" and "model".
    if "chat_messages" in payload or "mapping" in payload:
        return False

    return any(
        isinstance(msg, dict) and msg.get("role") in ("user", "model")
        for msg in messages
    )


def _extract_conversation_id(raw_conversation: dict[str, Any], fallback_index: int) -> str:
    """Extract or derive a conversation source id."""

    # Check explicit id fields.
    for key in ("id", "conversationId", "conversation_id"):
        value = raw_conversation.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    # Derive from URL if present (e.g. gemini.google.com/app/<id>).
    url = raw_conversation.get("url")
    if isinstance(url, str) and "/app/" in url:
        slug = url.rsplit("/app/", maxsplit=1)[-1].strip().rstrip("/")
        if slug:
            return f"gemini-{slug}"

    return f"gemini-conversation-{fallback_index}"


def _extract_ordered_messages(
    raw_messages: list[Any],
    *,
    source_id: str,
) -> list[NormalizedMessage]:
    """Extract and order messages from a conversational Gemini export."""

    normalized_messages: list[NormalizedMessage] = []
    for original_index, raw_message in enumerate(raw_messages):
        if not isinstance(raw_message, dict):
            continue

        content = _extract_message_text(raw_message)
        if not content:
            continue

        normalized_messages.append(
            NormalizedMessage(
                source_message_id=str(
                    raw_message.get("id")
                    or raw_message.get("messageId")
                    or f"{source_id}-message-{original_index}"
                ),
                role=_normalize_role(raw_message.get("role")),
                content=content,
                sequence_index=len(normalized_messages),
                created_at=_parse_iso_timestamp(raw_message.get("timestamp")),
            )
        )

    return normalized_messages


def _extract_message_text(raw_message: Any) -> str:
    """Extract text content from a Gemini message object."""

    if not isinstance(raw_message, dict):
        return ""

    # Direct content string.
    content = raw_message.get("content")
    if isinstance(content, str) and content.strip():
        return content.strip()

    # Text field fallback.
    text = raw_message.get("text")
    if isinstance(text, str) and text.strip():
        return text.strip()

    # Parts array (some exporters use this pattern).
    parts = raw_message.get("parts")
    if isinstance(parts, list):
        fragments = [
            part.strip() if isinstance(part, str) else
            (part.get("text", "").strip() if isinstance(part, dict) else "")
            for part in parts
        ]
        cleaned = [f for f in fragments if f]
        if cleaned:
            return "\n".join(cleaned)

    return ""


def _normalize_role(role: Any) -> str:
    """Normalize Gemini role values to the canonical user/assistant set."""

    cleaned = str(role or "unknown").strip().lower()
    if cleaned in ("user", "human"):
        return "user"
    if cleaned in ("model", "assistant"):
        return "assistant"
    if cleaned == "system":
        return "system"
    return cleaned or "unknown"


def _first_message_timestamp(raw_messages: list[Any]) -> float | None:
    """Return the earliest message timestamp in a raw messages list."""

    for msg in raw_messages:
        if isinstance(msg, dict):
            ts = _parse_iso_timestamp(msg.get("timestamp"))
            if ts is not None:
                return ts
    return None


def _parse_iso_timestamp(value: Any) -> float | None:
    """Parse an ISO 8601 timestamp string into a Unix float."""

    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if not isinstance(value, str):
        return None

    cleaned = value.strip()
    if not cleaned:
        return None

    try:
        return float(cleaned)
    except ValueError:
        pass

    try:
        return (
            datetime.fromisoformat(cleaned.replace("Z", "+00:00"))
            .astimezone(timezone.utc)
            .timestamp()
        )
    except ValueError:
        return None
