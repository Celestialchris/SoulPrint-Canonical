"""Helpers for rendering imported conversation transcript explorer."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from src.app.models import ImportedMessage


@dataclass(frozen=True)
class TocEntry:
    """Prompt-level anchor derived from a user turn."""

    message_id: int
    sequence_index: int
    label: str


def format_timestamp(timestamp_unix: float | None) -> str:
    """Format a unix timestamp for UI display."""

    if timestamp_unix is None:
        return "N/A"

    return (
        datetime.fromtimestamp(timestamp_unix, tz=timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )


def anchor_for_message(message_id: int) -> str:
    """Build a stable DOM anchor for one transcript message."""

    return f"message-{message_id}"


def _normalize_toc_label(content: str, max_chars: int = 56) -> str:
    compact = " ".join(content.split())
    if not compact:
        return "(empty prompt)"
    if len(compact) <= max_chars:
        return compact
    return f"{compact[: max_chars - 1].rstrip()}…"


def build_prompt_toc(messages: list[ImportedMessage]) -> list[TocEntry]:
    """Create prompt-level table-of-contents entries from user turns."""

    entries: list[TocEntry] = []
    for message in messages:
        if message.role != "user":
            continue
        entries.append(
            TocEntry(
                message_id=message.id,
                sequence_index=message.sequence_index,
                label=_normalize_toc_label(message.content),
            )
        )
    return entries
