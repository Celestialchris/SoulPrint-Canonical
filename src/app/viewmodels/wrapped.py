"""Wrapped summary viewmodel — 'Spotify Wrapped for AI' stats page."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import func

from ..models import ImportedConversation, ImportedMessage, MemoryEntry
from ..models.db import db


@dataclass(frozen=True)
class WrappedSummary:
    """Read-only wrapped summary rendered on the /summary route."""

    total_conversations: int
    total_messages: int
    providers: list[dict]
    dominant_provider: dict
    date_range: dict
    most_active_month: str
    longest_conversation: dict
    topic_highlights: list[str]
    average_messages_per_conversation: float
    unfinished_threads: dict
    has_data: bool


def _month_key(unix_ts: float | None) -> str | None:
    """Convert a Unix timestamp to 'YYYY-MM' string, or None."""
    if unix_ts is None:
        return None
    from datetime import datetime, timezone

    dt = datetime.fromtimestamp(unix_ts, tz=timezone.utc)
    return dt.strftime("%Y-%m")


def _resolve_conversation_title(stable_id: str) -> str | None:
    """Resolve a stable ID like 'imported_conversation:123' to its title."""
    prefix = "imported_conversation:"
    if not stable_id.startswith(prefix):
        return None
    raw_id = stable_id.removeprefix(prefix)
    if not raw_id.isdigit():
        return None
    conv = ImportedConversation.query.filter_by(id=int(raw_id)).first()
    if conv is None:
        return None
    return conv.title


def build_wrapped_summary(*, sqlite_path: str) -> WrappedSummary:
    """Build the read-only wrapped summary from canonical and derived stores.

    Parameters
    ----------
    sqlite_path:
        Raw file path to the SQLite database. Used to derive JSONL store
        paths for topics and continuity artifacts.
    """

    # ------------------------------------------------------------------
    # Core counts
    # ------------------------------------------------------------------
    imported_conversation_count = (
        db.session.query(func.count(ImportedConversation.id)).scalar() or 0
    )
    native_count = db.session.query(func.count(MemoryEntry.id)).scalar() or 0
    imported_message_count = (
        db.session.query(func.count(ImportedMessage.id)).scalar() or 0
    )

    total_conversations = imported_conversation_count + native_count
    total_messages = imported_message_count + native_count

    # ------------------------------------------------------------------
    # Providers with percentages
    # ------------------------------------------------------------------
    provider_rows = (
        db.session.query(
            ImportedConversation.source,
            func.count(ImportedConversation.id).label("count"),
        )
        .group_by(ImportedConversation.source)
        .order_by(func.count(ImportedConversation.id).desc(), ImportedConversation.source.asc())
        .all()
    )

    providers: list[dict] = []
    for source, count in provider_rows:
        percentage = round((count / total_conversations * 100) if total_conversations else 0, 1)
        providers.append({"name": source, "count": count, "percentage": percentage})

    # Native entries count as a "provider" for percentage purposes if they exist
    if native_count > 0:
        percentage = round((native_count / total_conversations * 100) if total_conversations else 0, 1)
        providers.append({"name": "native", "count": native_count, "percentage": percentage})

    dominant_provider = (
        max(providers, key=lambda p: p["count"]) if providers else {"name": "", "count": 0}
    )

    # ------------------------------------------------------------------
    # Date range
    # ------------------------------------------------------------------
    earliest_imported = db.session.query(
        func.min(ImportedConversation.created_at_unix)
    ).scalar()
    latest_imported = db.session.query(
        func.max(ImportedConversation.updated_at_unix)
    ).scalar()
    earliest_native = db.session.query(func.min(MemoryEntry.timestamp)).scalar()
    latest_native = db.session.query(func.max(MemoryEntry.timestamp)).scalar()

    # Convert native datetimes to unix for comparison
    earliest_native_unix = None
    latest_native_unix = None
    if earliest_native is not None:
        from datetime import timezone

        if earliest_native.tzinfo is None:
            earliest_native = earliest_native.replace(tzinfo=timezone.utc)
        earliest_native_unix = earliest_native.timestamp()
    if latest_native is not None:
        from datetime import timezone

        if latest_native.tzinfo is None:
            latest_native = latest_native.replace(tzinfo=timezone.utc)
        latest_native_unix = latest_native.timestamp()

    candidates_earliest = [t for t in [earliest_imported, earliest_native_unix] if t is not None]
    candidates_latest = [t for t in [latest_imported, latest_native_unix] if t is not None]

    date_range = {
        "earliest": min(candidates_earliest) if candidates_earliest else None,
        "latest": max(candidates_latest) if candidates_latest else None,
    }

    # ------------------------------------------------------------------
    # Most active month (by message creation timestamps)
    # ------------------------------------------------------------------
    month_counter: Counter[str] = Counter()

    msg_timestamps = (
        db.session.query(ImportedMessage.created_at_unix)
        .filter(ImportedMessage.created_at_unix.isnot(None))
        .all()
    )
    for (ts,) in msg_timestamps:
        month = _month_key(ts)
        if month:
            month_counter[month] += 1

    # Also count native entries by month
    native_timestamps = db.session.query(MemoryEntry.timestamp).all()
    for (ts,) in native_timestamps:
        if ts is not None:
            month = ts.strftime("%Y-%m")
            month_counter[month] += 1

    most_active_month = month_counter.most_common(1)[0][0] if month_counter else ""

    # ------------------------------------------------------------------
    # Longest conversation
    # ------------------------------------------------------------------
    longest_row = (
        db.session.query(
            ImportedConversation.title,
            func.count(ImportedMessage.id).label("msg_count"),
        )
        .join(ImportedMessage, ImportedConversation.id == ImportedMessage.conversation_id)
        .group_by(ImportedConversation.id)
        .order_by(func.count(ImportedMessage.id).desc())
        .first()
    )
    longest_conversation = (
        {"title": longest_row[0], "message_count": longest_row[1]}
        if longest_row
        else {"title": "", "message_count": 0}
    )

    # ------------------------------------------------------------------
    # Topic highlights (top 5 from latest topic scan)
    # ------------------------------------------------------------------
    from ...intelligence.store import default_topic_store_path, list_topic_scans

    topic_store = default_topic_store_path(sqlite_path)
    scans = list_topic_scans(topic_store, limit=1)
    topic_highlights: list[str] = []
    if scans:
        clusters = scans[0].get("clusters", [])
        topic_highlights = [c.get("topic_label", "") for c in clusters[:5]]

    # ------------------------------------------------------------------
    # Unfinished threads — two-tier detection
    # ------------------------------------------------------------------
    from ...intelligence.continuity.store import (
        default_continuity_store_path,
        list_artifacts_by_type,
    )

    continuity_store = default_continuity_store_path(sqlite_path)
    open_loop_artifacts = list_artifacts_by_type(continuity_store, "open_loops", limit=50)

    seen_conv_ids: set[int] = set()
    unfinished_titles: list[str] = []

    # Tier 1: from continuity open_loops artifacts
    for artifact in open_loop_artifacts:
        for stable_id in artifact.get("source_conversation_ids", []):
            prefix = "imported_conversation:"
            if stable_id.startswith(prefix):
                raw_id = stable_id.removeprefix(prefix)
                if raw_id.isdigit():
                    conv_id = int(raw_id)
                    if conv_id not in seen_conv_ids:
                        title = _resolve_conversation_title(stable_id)
                        if title:
                            seen_conv_ids.add(conv_id)
                            unfinished_titles.append(title)

    # Tier 2: fallback — conversations where last message role == "user"
    if len(unfinished_titles) < 3:
        all_convs = ImportedConversation.query.all()
        for conv in all_convs:
            if conv.id in seen_conv_ids:
                continue
            last_msg = (
                ImportedMessage.query
                .filter_by(conversation_id=conv.id)
                .order_by(ImportedMessage.sequence_index.desc())
                .first()
            )
            if last_msg and last_msg.role == "user":
                seen_conv_ids.add(conv.id)
                unfinished_titles.append(conv.title)

    # Cap at 3
    unfinished_titles = unfinished_titles[:3]

    unfinished_threads = {
        "count": len(unfinished_titles),
        "titles": unfinished_titles,
    }

    # ------------------------------------------------------------------
    # Average messages per conversation
    # ------------------------------------------------------------------
    average_messages_per_conversation = (
        round(total_messages / total_conversations, 1) if total_conversations > 0 else 0.0
    )

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------
    return WrappedSummary(
        total_conversations=total_conversations,
        total_messages=total_messages,
        providers=providers,
        dominant_provider=dominant_provider,
        date_range=date_range,
        most_active_month=most_active_month,
        longest_conversation=longest_conversation,
        topic_highlights=topic_highlights,
        average_messages_per_conversation=average_messages_per_conversation,
        unfinished_threads=unfinished_threads,
        has_data=total_conversations > 0,
    )
