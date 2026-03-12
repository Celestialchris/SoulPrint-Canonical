"""Workspace viewmodel helpers for the canonical `/` route."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import func

from ..models import ImportedConversation, ImportedMessage, MemoryEntry
from ..models.db import db


@dataclass(frozen=True)
class WorkspaceSummary:
    """Read-only workspace summary rendered on the home route."""

    native_count: int
    imported_conversation_count: int
    imported_message_count: int
    trace_count: int
    providers: list[dict[str, int | str]]
    recent_imported: list[dict[str, object]]
    recent_native: list[dict[str, object]]
    recent_traces: list[dict[str, object]]
    has_any_data: bool
    continuity_sentence: str


def _trim_text(value: str, limit: int = 120) -> str:
    cleaned = " ".join((value or "").split())
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 1].rstrip() + "…"


def build_workspace_summary(*, trace_store_path: str | Path) -> WorkspaceSummary:
    """Build the read-only workspace model from canonical and derived stores."""

    native_count = db.session.query(func.count(MemoryEntry.id)).scalar() or 0
    imported_conversation_count = (
        db.session.query(func.count(ImportedConversation.id)).scalar() or 0
    )
    imported_message_count = db.session.query(func.count(ImportedMessage.id)).scalar() or 0

    provider_rows = (
        db.session.query(
            ImportedConversation.source,
            func.count(ImportedConversation.id).label("conversation_count"),
        )
        .group_by(ImportedConversation.source)
        .order_by(func.count(ImportedConversation.id).desc(), ImportedConversation.source.asc())
        .all()
    )
    providers = [
        {"name": source, "conversation_count": conversation_count}
        for source, conversation_count in provider_rows
    ]

    recent_imported_rows = (
        ImportedConversation.query.order_by(ImportedConversation.id.desc()).limit(5).all()
    )
    recent_imported = [
        {
            "id": row.id,
            "title": row.title,
            "source": row.source,
            "updated_at_unix": row.updated_at_unix,
            "created_at_unix": row.created_at_unix,
        }
        for row in recent_imported_rows
    ]

    recent_native_rows = MemoryEntry.query.order_by(MemoryEntry.id.desc()).limit(5).all()
    recent_native = [
        {
            "id": row.id,
            "role": row.role,
            "timestamp": row.timestamp,
            "preview": _trim_text(row.content),
        }
        for row in recent_native_rows
    ]

    from ...answering.trace import list_answer_traces

    traces = list_answer_traces(trace_store_path, limit=50)
    trace_count = len(traces)
    recent_traces = [
        {
            "trace_id": trace.get("trace_id", ""),
            "question": _trim_text(str(trace.get("question", ""))),
            "created_at": str(trace.get("created_at", "")),
            "status": str(trace.get("status", "")),
        }
        for trace in traces[:5]
    ]

    has_any_data = any(
        [
            native_count,
            imported_conversation_count,
            imported_message_count,
            trace_count,
        ]
    )

    continuity_sentence = (
        "You have "
        f"{imported_conversation_count} imported conversations across {len(providers)} providers "
        f"and {native_count} native memory entries."
    )

    return WorkspaceSummary(
        native_count=native_count,
        imported_conversation_count=imported_conversation_count,
        imported_message_count=imported_message_count,
        trace_count=trace_count,
        providers=providers,
        recent_imported=recent_imported,
        recent_native=recent_native,
        recent_traces=recent_traces,
        has_any_data=has_any_data,
        continuity_sentence=continuity_sentence,
    )
