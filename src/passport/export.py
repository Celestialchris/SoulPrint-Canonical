"""Minimal Memory Passport v1 exporter.

This module writes a local, inspectable package from canonical SQLite lanes
without changing storage semantics.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from flask import Flask

from src.app.models import ImportedConversation, ImportedMessage, MemoryEntry
from src.app.models.db import db
from src.importers.query import (
    ImportedConversationDetail,
    ImportedMessageRecord,
    render_imported_conversation_markdown,
)

PASSPORT_VERSION = "1.0"
SOULPRINT_EXPORT_VERSION = "m1-minimal"


@dataclass(frozen=True)
class PassportExportResult:
    """Result metadata for one export run."""

    package_dir: Path
    manifest_path: Path
    canonical_units: int
    derived_units: int


def _sqlite_app(sqlite_path: str | Path) -> Flask:
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{Path(sqlite_path).resolve()}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    return app


def _iso_utc_from_unix(timestamp_unix: float | None) -> str | None:
    if timestamp_unix is None:
        return None
    return (
        datetime.fromtimestamp(timestamp_unix, tz=UTC)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )


def _iso_utc_from_datetime(timestamp: datetime | None) -> str | None:
    if timestamp is None:
        return None
    value = timestamp
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.isoformat(timespec="seconds").replace("+00:00", "Z")


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(record, sort_keys=True, ensure_ascii=False) for record in records]
    content = "\n".join(lines)
    if lines:
        content += "\n"
    path.write_text(content, encoding="utf-8")


def _render_native_markdown(entry: MemoryEntry) -> str:
    timestamp_iso = _iso_utc_from_datetime(entry.timestamp)
    lines = [
        f"# Native Memory Entry {entry.id}",
        "",
        "## Metadata",
        f"- Stable ID: memory:{entry.id}",
        "- Source Lane: native_memory",
        "- Source Provider: soulprint",
        f"- Timestamp: {timestamp_iso or 'N/A'}",
        f"- Role: {entry.role}",
        f"- Tags: {entry.tags or ''}",
        "",
        "## Content",
        entry.content,
        "",
    ]
    return "\n".join(lines)


def _as_imported_detail(row: ImportedConversation) -> ImportedConversationDetail:
    ordered_messages = sorted(row.messages, key=lambda message: message.sequence_index)
    return ImportedConversationDetail(
        id=row.id,
        source=row.source,
        source_conversation_id=row.source_conversation_id,
        title=row.title,
        created_at_unix=row.created_at_unix,
        updated_at_unix=row.updated_at_unix,
        messages=[
            ImportedMessageRecord(
                id=message.id,
                source_message_id=message.source_message_id,
                role=message.role,
                content=message.content,
                sequence_index=message.sequence_index,
                created_at_unix=message.created_at_unix,
            )
            for message in ordered_messages
        ],
    )


def export_memory_passport(
    sqlite_path: str | Path,
    output_dir: str | Path,
    *,
    include_markdown: bool = True,
    created_at: datetime | None = None,
    export_id: str | None = None,
) -> PassportExportResult:
    """Export canonical and derived data into a minimal Memory Passport package."""

    package_dir = Path(output_dir) / "memory-passport-v1"
    package_dir.mkdir(parents=True, exist_ok=True)

    created_at_value = created_at or datetime.now(tz=UTC)
    created_at_iso = created_at_value.isoformat(timespec="seconds").replace("+00:00", "Z")
    export_identifier = export_id or str(uuid4())

    provenance_records: list[dict] = []

    imported_conversation_records: list[dict] = []
    imported_message_records: list[dict] = []
    native_memory_records: list[dict] = []

    source_lanes: list[str] = []
    source_providers: set[str] = set()

    app = _sqlite_app(sqlite_path)
    with app.app_context():
        try:
            imported_rows = ImportedConversation.query.order_by(ImportedConversation.id.asc()).all()
            if imported_rows:
                source_lanes.append("imported_conversation")

            for conversation in imported_rows:
                stable_id = f"imported_conversation:{conversation.id}"
                record = {
                    "stable_id": stable_id,
                    "source_lane": "imported_conversation",
                    "source_provider": conversation.source,
                    "source_record_id": conversation.source_conversation_id,
                    "title": conversation.title,
                    "created_at_unix": conversation.created_at_unix,
                    "updated_at_unix": conversation.updated_at_unix,
                    "created_at_iso": _iso_utc_from_unix(conversation.created_at_unix),
                    "updated_at_iso": _iso_utc_from_unix(conversation.updated_at_unix),
                    "source_metadata": {
                        "source": conversation.source,
                        "source_conversation_id": conversation.source_conversation_id,
                    },
                }
                imported_conversation_records.append(record)
                source_providers.add(conversation.source)

                provenance_records.append(
                    {
                        "unit_type": "canonical",
                        "stable_id": stable_id,
                        "source_lane": "imported_conversation",
                        "source_provider": conversation.source,
                        "source_record_id": conversation.source_conversation_id,
                        "timestamp_unix": conversation.updated_at_unix or conversation.created_at_unix,
                        "source_metadata": record["source_metadata"],
                        "path": "conversations/imported/chatgpt/conversations.jsonl",
                    }
                )

                for message in sorted(conversation.messages, key=lambda item: item.sequence_index):
                    message_stable_id = f"imported_message:{message.id}"
                    message_record = {
                        "stable_id": message_stable_id,
                        "conversation_stable_id": stable_id,
                        "source_lane": "imported_conversation",
                        "source_provider": conversation.source,
                        "source_record_id": message.source_message_id,
                        "role": message.role,
                        "content": message.content,
                        "sequence_index": message.sequence_index,
                        "created_at_unix": message.created_at_unix,
                        "created_at_iso": _iso_utc_from_unix(message.created_at_unix),
                        "source_metadata": {
                            "conversation_source_id": conversation.source_conversation_id,
                            "source_message_id": message.source_message_id,
                        },
                    }
                    imported_message_records.append(message_record)
                    provenance_records.append(
                        {
                            "unit_type": "canonical",
                            "stable_id": message_stable_id,
                            "source_lane": "imported_conversation",
                            "source_provider": conversation.source,
                            "source_record_id": message.source_message_id,
                            "timestamp_unix": message.created_at_unix,
                            "source_metadata": message_record["source_metadata"],
                            "path": "conversations/imported/chatgpt/messages.jsonl",
                        }
                    )

                if include_markdown:
                    markdown_rel_path = f"markdown/conversations/{stable_id}.md"
                    markdown_path = package_dir / markdown_rel_path
                    markdown_path.parent.mkdir(parents=True, exist_ok=True)
                    markdown_path.write_text(
                        render_imported_conversation_markdown(_as_imported_detail(conversation)),
                        encoding="utf-8",
                    )
                    provenance_records.append(
                        {
                            "unit_type": "derived",
                            "stable_id": f"derived:markdown:{stable_id}",
                            "source_lane": "imported_conversation",
                            "source_provider": conversation.source,
                            "source_record_id": conversation.source_conversation_id,
                            "timestamp_unix": conversation.updated_at_unix or conversation.created_at_unix,
                            "source_metadata": {
                                "canonical_stable_id": stable_id,
                                "derived_kind": "markdown",
                            },
                            "path": markdown_rel_path,
                        }
                    )

            native_rows = MemoryEntry.query.order_by(MemoryEntry.id.asc()).all()
            if native_rows:
                source_lanes.append("native_memory")

            for entry in native_rows:
                stable_id = f"memory:{entry.id}"
                timestamp_iso = _iso_utc_from_datetime(entry.timestamp)
                timestamp_unix = None
                if entry.timestamp is not None:
                    timestamp_unix = (
                        entry.timestamp.replace(tzinfo=UTC).timestamp()
                        if entry.timestamp.tzinfo is None
                        else entry.timestamp.timestamp()
                    )

                native_record = {
                    "stable_id": stable_id,
                    "source_lane": "native_memory",
                    "source_provider": "soulprint",
                    "source_record_id": str(entry.id),
                    "timestamp_unix": timestamp_unix,
                    "timestamp_iso": timestamp_iso,
                    "role": entry.role,
                    "content": entry.content,
                    "tags": entry.tags,
                    "source_metadata": {
                        "role": entry.role,
                        "tags": entry.tags or "",
                    },
                }
                native_memory_records.append(native_record)
                source_providers.add("soulprint")

                provenance_records.append(
                    {
                        "unit_type": "canonical",
                        "stable_id": stable_id,
                        "source_lane": "native_memory",
                        "source_provider": "soulprint",
                        "source_record_id": str(entry.id),
                        "timestamp_unix": timestamp_unix,
                        "source_metadata": native_record["source_metadata"],
                        "path": "native/memory_entries.jsonl",
                    }
                )

                if include_markdown:
                    markdown_rel_path = f"markdown/native/{stable_id}.md"
                    markdown_path = package_dir / markdown_rel_path
                    markdown_path.parent.mkdir(parents=True, exist_ok=True)
                    markdown_path.write_text(_render_native_markdown(entry), encoding="utf-8")
                    provenance_records.append(
                        {
                            "unit_type": "derived",
                            "stable_id": f"derived:markdown:{stable_id}",
                            "source_lane": "native_memory",
                            "source_provider": "soulprint",
                            "source_record_id": str(entry.id),
                            "timestamp_unix": timestamp_unix,
                            "source_metadata": {
                                "canonical_stable_id": stable_id,
                                "derived_kind": "markdown",
                            },
                            "path": markdown_rel_path,
                        }
                    )

            if imported_conversation_records:
                _write_jsonl(
                    package_dir / "conversations" / "imported" / "chatgpt" / "conversations.jsonl",
                    imported_conversation_records,
                )
            if imported_message_records:
                _write_jsonl(
                    package_dir / "conversations" / "imported" / "chatgpt" / "messages.jsonl",
                    imported_message_records,
                )
            if native_memory_records:
                _write_jsonl(package_dir / "native" / "memory_entries.jsonl", native_memory_records)

            _write_jsonl(package_dir / "provenance" / "index.jsonl", provenance_records)

            all_timestamps = [
                value
                for value in (
                    [record.get("updated_at_unix") or record.get("created_at_unix") for record in imported_conversation_records]
                    + [record.get("timestamp_unix") for record in native_memory_records]
                )
                if value is not None
            ]

            counts = {
                "imported_conversations": len(imported_conversation_records),
                "imported_messages": len(imported_message_records),
                "native_memory_entries": len(native_memory_records),
                "provenance_units": len(provenance_records),
            }

            manifest = {
                "passport_version": PASSPORT_VERSION,
                "created_at": created_at_iso,
                "soulprint_export_version": SOULPRINT_EXPORT_VERSION,
                "source_lanes": sorted(source_lanes),
                "counts": counts,
                "source_providers": sorted(source_providers),
                "provenance": {
                    "index_file": "provenance/index.jsonl",
                    "canonical_vs_derived_boundary": "canonical lane files authoritative; markdown derived",
                },
                "integrity_notes": "v1 non-cryptographic export; deterministic JSON/JSONL ordering",
                "export_id": export_identifier,
                "markdown_included": include_markdown,
            }
            if all_timestamps:
                manifest["time_range"] = {
                    "min_timestamp_unix": min(all_timestamps),
                    "max_timestamp_unix": max(all_timestamps),
                }

            manifest_path = package_dir / "manifest.json"
            _write_json(manifest_path, manifest)

            canonical_units = len(imported_conversation_records) + len(imported_message_records) + len(
                native_memory_records
            )
            derived_units = len(provenance_records) - canonical_units
            return PassportExportResult(
                package_dir=package_dir,
                manifest_path=manifest_path,
                canonical_units=canonical_units,
                derived_units=max(0, derived_units),
            )
        finally:
            db.session.remove()
            db.engine.dispose()
