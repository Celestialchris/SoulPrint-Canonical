"""Claude Code session JSONL adapter using the shared importer normalization contract."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .contracts import (
    PROVIDER_CLAUDE_CODE,
    ConversationImporter,
    NormalizedConversation,
    NormalizedMessage,
)


TRUNCATE_AT = 4000
DEFAULT_TITLE = "Claude Code session"

_KNOWN_RECORD_TYPES = {
    "user",
    "assistant",
    "permission-mode",
    "attachment",
    "file-history-snapshot",
    "last-prompt",
    "custom-title",
    "agent-name",
    "system",
}

_TOOL_NAMES_WITH_COMMAND = {"Bash"}
_TOOL_NAMES_WITH_FILE_PATH = {"Write", "Edit", "str_replace_based_edit_tool"}


class ClaudeCodeImporter(ConversationImporter):
    """Concrete importer adapter for Claude Code session JSONL files."""

    provider_id = PROVIDER_CLAUDE_CODE

    def parse_payload(self, payload: Any) -> list[NormalizedConversation]:
        if not isinstance(payload, (bytes, bytearray)):
            payload = str(payload).encode("utf-8")
        return _parse_claude_code_session(payload)


def looks_like_claude_code_export(payload: Any) -> bool:
    """Return True when payload is a Claude Code session JSONL file.

    Scans lines until a recognizable record is found, skipping malformed lines.
    Returns False on a line that parses successfully but doesn't match the shape.
    """
    if not isinstance(payload, (bytes, bytearray)):
        return False
    try:
        text = payload.decode("utf-8", errors="replace")
    except Exception:
        return False
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue  # malformed line — keep scanning
        if not isinstance(record, dict):
            return False
        t = record.get("type")
        if t in _KNOWN_RECORD_TYPES and "sessionId" in record:
            return True
        return False
    return False


def _parse_timestamp(ts: str | int | float | None) -> float | None:
    if ts is None:
        return None
    if isinstance(ts, (int, float)):
        return float(ts)
    if isinstance(ts, str):
        cleaned = ts.strip()
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


def _render_tool_use(block: dict) -> str:
    name = block.get("name", "")
    inp = block.get("input") or {}
    if name == "Bash":
        cmd = inp.get("command", "")
        return f"[Tool: Bash] {cmd}".rstrip() if cmd else "[Tool: Bash]"
    if name == "Write":
        path = inp.get("file_path", "")
        return f"[Tool: Write] {path}".rstrip() if path else "[Tool: Write]"
    if name in ("Edit", "str_replace_based_edit_tool"):
        path = inp.get("file_path", "")
        return f"[Tool: Edit] {path}".rstrip() if path else "[Tool: Edit]"
    return f"[Tool: {name}]" if name else "[Tool]"


def _render_tool_result(block: dict, truncate_at: int) -> str:
    prefix = "[Error] " if block.get("is_error") else ""
    content = block.get("content", "")

    if isinstance(content, str):
        body = content
    elif isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if not isinstance(item, dict):
                continue
            item_type = item.get("type")
            if item_type == "text":
                text = item.get("text", "")
                if text:
                    parts.append(text)
            elif item_type == "tool_reference":
                tool_name = item.get("tool_name", "")
                parts.append(f"[Reference: {tool_name}]")
        body = "\n".join(parts)
    else:
        return prefix.rstrip()

    if len(body) > truncate_at:
        body = body[:truncate_at] + "... [truncated]"
    return (prefix + body).strip()


def _extract_text(content: str | list) -> str:
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""
    parts: list[str] = []
    for block in content:
        if not isinstance(block, dict):
            continue
        block_type = block.get("type")
        if block_type == "text":
            text = block.get("text", "")
            if text:
                parts.append(text)
        elif block_type == "tool_use":
            rendered = _render_tool_use(block)
            if rendered:
                parts.append(rendered)
        elif block_type == "tool_result":
            rendered = _render_tool_result(block, TRUNCATE_AT)
            if rendered:
                parts.append(rendered)
        elif block_type == "thinking":
            pass  # drop thinking blocks — model-internal, not part of user transcript
        # unknown block types: skip silently
    return "\n\n".join(parts)


def _parse_claude_code_session(payload: bytes) -> list[NormalizedConversation]:
    try:
        text = payload.decode("utf-8")
    except (UnicodeDecodeError, AttributeError):
        return []

    messages: list[NormalizedMessage] = []
    session_id: str | None = None
    first_ts: float | None = None
    last_ts: float | None = None

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue

        if not isinstance(record, dict):
            continue
        if record.get("type") not in {"user", "assistant"}:
            continue
        msg_dict = record.get("message")
        if not isinstance(msg_dict, dict):
            continue

        ts = _parse_timestamp(record.get("timestamp"))
        if ts is None:
            continue

        role = msg_dict.get("role") or record.get("type", "unknown")
        content_raw = msg_dict.get("content", "")
        text_content = _extract_text(content_raw)
        if not text_content.strip():
            continue

        sid = record.get("sessionId", "unknown")
        if session_id is None:
            session_id = sid

        seq = len(messages)
        record_uuid = record.get("uuid")
        source_message_id = record_uuid if record_uuid else f"{sid}:{seq}"
        messages.append(
            NormalizedMessage(
                source_message_id=source_message_id,
                role=role,
                content=text_content,
                sequence_index=seq,
                created_at=ts,
            )
        )

        if first_ts is None:
            first_ts = ts
        last_ts = ts

    if not messages:
        return []

    effective_session_id = session_id or "unknown"
    return [
        NormalizedConversation(
            source_provider=PROVIDER_CLAUDE_CODE,
            source_conversation_id=effective_session_id,
            title=f"Claude Code session {effective_session_id[:8]}",
            created_at=first_ts,
            updated_at=last_ts,
            messages=messages,
            source_metadata={"session_id": effective_session_id},
        )
    ]
