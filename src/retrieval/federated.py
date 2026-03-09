"""Minimal federated read surface across native and imported lanes.

This module intentionally composes existing lane storage without changing schema.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timezone
from pathlib import Path

from flask import Flask
from sqlalchemy import func

from src.app.models import ImportedConversation, ImportedMessage, MemoryEntry
from src.app.models.db import db

from .mem0_adapter import ingest_federated_items, mem0_write_mode


@dataclass(frozen=True)
class FederatedReadResult:
    """Lightweight read result with explicit lane/source provenance."""

    source_lane: str
    stable_id: str
    title: str
    timestamp_unix: float | None
    source_metadata: dict[str, str]


def _sqlite_app(sqlite_path: str | Path) -> Flask:
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{Path(sqlite_path).resolve()}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    return app


def _memory_timestamp_to_unix(entry: MemoryEntry) -> float | None:
    if entry.timestamp is None:
        return None

    timestamp = entry.timestamp
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    return timestamp.timestamp()


def federated_search(
    sqlite_path: str | Path,
    keyword: str = "",
    limit_per_lane: int = 25,
) -> list[FederatedReadResult]:
    """Return mixed read-only results from native and imported lanes.

    Results are sorted by descending timestamp when available, preserving explicit
    lane/source metadata for traceability.
    """

    cleaned = keyword.strip()
    pattern = f"%{cleaned.lower()}%" if cleaned else None

    app = _sqlite_app(sqlite_path)
    with app.app_context():
        try:
            memory_query = MemoryEntry.query
            if pattern is not None:
                memory_query = memory_query.filter(
                    func.lower(MemoryEntry.content).like(pattern)
                )

            memory_rows = (
                memory_query.order_by(MemoryEntry.timestamp.desc())
                .limit(limit_per_lane)
                .all()
            )

            imported_query = ImportedConversation.query
            if pattern is not None:
                message_match_exists = (
                    ImportedMessage.query.filter(
                        ImportedMessage.conversation_id == ImportedConversation.id,
                        func.lower(ImportedMessage.content).like(pattern),
                    )
                    .exists()
                )
                imported_query = imported_query.filter(
                    (func.lower(ImportedConversation.title).like(pattern))
                    | message_match_exists
                )

            imported_rows = (
                imported_query.order_by(ImportedConversation.id.desc())
                .limit(limit_per_lane)
                .all()
            )

            results: list[FederatedReadResult] = [
                FederatedReadResult(
                    source_lane="native_memory",
                    stable_id=f"memory:{row.id}",
                    title=row.content,
                    timestamp_unix=_memory_timestamp_to_unix(row),
                    source_metadata={
                        "role": row.role,
                        "tags": row.tags or "",
                    },
                )
                for row in memory_rows
            ]

            results.extend(
                FederatedReadResult(
                    source_lane="imported_conversation",
                    stable_id=f"imported_conversation:{row.id}",
                    title=row.title,
                    timestamp_unix=row.updated_at_unix or row.created_at_unix,
                    source_metadata={
                        "source": row.source,
                        "source_conversation_id": row.source_conversation_id,
                    },
                )
                for row in imported_rows
            )

            merged = sorted(
                results,
                key=lambda item: (
                    item.timestamp_unix is not None,
                    item.timestamp_unix if item.timestamp_unix is not None else float("-inf"),
                ),
                reverse=True,
            )

            if mem0_write_mode() == "best_effort":
                ingest_federated_items(merged)

            return merged
        finally:
            db.session.remove()
            db.engine.dispose()
