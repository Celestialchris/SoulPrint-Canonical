"""Read-only validation for Memory Passport v1 artifacts."""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .export import PASSPORT_VERSION

STATUS_VALID = "valid"
STATUS_VALID_WITH_WARNINGS = "valid_with_warnings"
STATUS_INVALID = "invalid"

_CANONICAL_COUNT_KEYS = (
    "imported_conversations",
    "imported_messages",
    "native_memory_entries",
    "provenance_units",
)


@dataclass(frozen=True)
class PassportValidationDiagnostic:
    """One readable validator diagnostic."""

    code: str
    message: str
    path: str | None = None
    stable_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "path": self.path,
            "stable_id": self.stable_id,
        }


@dataclass(frozen=True)
class PassportValidationResult:
    """Structured, machine-readable result for one passport validation run."""

    status: str
    errors: list[PassportValidationDiagnostic] = field(default_factory=list)
    warnings: list[PassportValidationDiagnostic] = field(default_factory=list)
    checked_counts: dict[str, int] = field(default_factory=dict)
    provider_summary: dict[str, dict[str, int]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "errors": [diagnostic.to_dict() for diagnostic in self.errors],
            "warnings": [diagnostic.to_dict() for diagnostic in self.warnings],
            "checked_counts": dict(self.checked_counts),
            "provider_summary": {
                provider_id: dict(counts)
                for provider_id, counts in self.provider_summary.items()
            },
        }


def validate_memory_passport(passport_path: str | Path) -> PassportValidationResult:
    """Validate one exported Memory Passport package without mutating it."""

    validator = _PassportValidator(_resolve_package_dir(passport_path))
    return validator.validate()


def _resolve_package_dir(passport_path: str | Path) -> Path:
    path = Path(passport_path)
    if path.is_file() and path.name == "manifest.json":
        return path.parent
    if path.is_dir() and (path / "manifest.json").exists():
        return path
    nested = path / "memory-passport-v1"
    if nested.is_dir() and (nested / "manifest.json").exists():
        return nested
    return path


class _PassportValidator:
    def __init__(self, package_dir: Path):
        self.package_dir = package_dir
        self.errors: list[PassportValidationDiagnostic] = []
        self.warnings: list[PassportValidationDiagnostic] = []
        self.checked_counts = {
            "imported_conversations": 0,
            "imported_messages": 0,
            "native_memory_entries": 0,
            "provenance_units": 0,
            "derived_units": 0,
        }
        self.provider_summary: dict[str, dict[str, int]] = defaultdict(
            lambda: {
                "imported_conversations": 0,
                "imported_messages": 0,
                "native_memory_entries": 0,
            }
        )
        self.actual_source_lanes: set[str] = set()
        self.actual_source_providers: set[str] = set()
        self.actual_timestamps: list[float] = []
        self.canonical_records: dict[str, dict[str, Any]] = {}
        self.canonical_paths: dict[str, str] = {}
        self.imported_conversations: dict[str, dict[str, Any]] = {}
        self.message_sequences: dict[str, list[int]] = defaultdict(list)
        self.provenance_records: dict[str, dict[str, Any]] = {}
        self._conversation_source_identities: dict[tuple[str, str], str] = {}
        self._message_source_identities: dict[tuple[str, str, str], str] = {}

    def validate(self) -> PassportValidationResult:
        manifest = self._load_manifest()
        if manifest is None:
            return self._build_result()

        self._load_imported_conversations()
        self._load_imported_messages()
        self._validate_message_sequences()
        self._load_native_memory_entries()
        self._validate_provenance(manifest)
        self._validate_manifest_consistency(manifest)
        return self._build_result()

    def _build_result(self) -> PassportValidationResult:
        if self.errors:
            status = STATUS_INVALID
        elif self.warnings:
            status = STATUS_VALID_WITH_WARNINGS
        else:
            status = STATUS_VALID

        return PassportValidationResult(
            status=status,
            errors=self.errors,
            warnings=self.warnings,
            checked_counts=dict(self.checked_counts),
            provider_summary={
                provider_id: dict(counts)
                for provider_id, counts in sorted(self.provider_summary.items())
            },
        )

    def _load_manifest(self) -> dict[str, Any] | None:
        manifest_path = self.package_dir / "manifest.json"
        if not manifest_path.exists():
            self._add_error(
                "manifest_missing",
                "Memory Passport is missing required manifest.json.",
                path="manifest.json",
            )
            return None

        manifest = self._read_json_file(manifest_path)
        if manifest is None:
            return None
        if not isinstance(manifest, dict):
            self._add_error(
                "manifest_invalid_type",
                "manifest.json must contain a top-level JSON object.",
                path="manifest.json",
            )
            return None

        required_fields: dict[str, tuple[type[Any], ...]] = {
            "passport_version": (str,),
            "created_at": (str,),
            "soulprint_export_version": (str,),
            "source_lanes": (list,),
            "counts": (dict,),
            "source_providers": (list,),
            "provenance": (dict,),
            "integrity_notes": (str, list),
        }
        for field_name, expected_types in required_fields.items():
            value = manifest.get(field_name)
            if value is None:
                self._add_error(
                    "manifest_missing_field",
                    f"manifest.json is missing required field '{field_name}'.",
                    path="manifest.json",
                )
                continue
            if not isinstance(value, expected_types):
                type_names = ", ".join(expected_type.__name__ for expected_type in expected_types)
                self._add_error(
                    "manifest_invalid_field_type",
                    f"manifest.json field '{field_name}' must be one of: {type_names}.",
                    path="manifest.json",
                )

        integrity_notes = manifest.get("integrity_notes")
        if isinstance(integrity_notes, list):
            if any(not isinstance(value, str) or not value.strip() for value in integrity_notes):
                self._add_error(
                    "manifest_invalid_integrity_notes",
                    "manifest.json field 'integrity_notes' must contain only non-empty strings when provided as an array.",
                    path="manifest.json",
                )

        version = manifest.get("passport_version")
        if isinstance(version, str) and version != PASSPORT_VERSION:
            self._add_error(
                "unsupported_passport_version",
                f"Passport version '{version}' is not supported by this validator.",
                path="manifest.json",
            )

        for field_name in ("source_lanes", "source_providers"):
            values = manifest.get(field_name)
            if isinstance(values, list):
                if any(not isinstance(value, str) or not value.strip() for value in values):
                    self._add_error(
                        "manifest_invalid_list_value",
                        f"manifest.json field '{field_name}' must contain only non-empty strings.",
                        path="manifest.json",
                    )

        counts = manifest.get("counts")
        if isinstance(counts, dict):
            for key in _CANONICAL_COUNT_KEYS:
                value = counts.get(key)
                if value is None:
                    self._add_error(
                        "manifest_missing_count",
                        f"manifest.json counts are missing required key '{key}'.",
                        path="manifest.json",
                    )
                    continue
                if not isinstance(value, int) or value < 0:
                    self._add_error(
                        "manifest_invalid_count",
                        f"manifest.json count '{key}' must be a non-negative integer.",
                        path="manifest.json",
                    )

        provenance = manifest.get("provenance")
        if isinstance(provenance, dict):
            index_file = provenance.get("index_file")
            if not isinstance(index_file, str) or not index_file.strip():
                self._add_error(
                    "manifest_missing_provenance_index",
                    "manifest.json provenance.index_file must be a non-empty string.",
                    path="manifest.json",
                )

        markdown_included = manifest.get("markdown_included")
        if markdown_included is not None and not isinstance(markdown_included, bool):
            self._add_error(
                "manifest_invalid_markdown_flag",
                "manifest.json field 'markdown_included' must be a boolean when present.",
                path="manifest.json",
            )

        time_range = manifest.get("time_range")
        if time_range is not None and not isinstance(time_range, dict):
            self._add_error(
                "manifest_invalid_time_range",
                "manifest.json field 'time_range' must be an object when present.",
                path="manifest.json",
            )

        return manifest

    def _load_imported_conversations(self) -> None:
        imported_root = self.package_dir / "conversations" / "imported"
        if not imported_root.exists():
            return

        for conversation_path in sorted(imported_root.glob("*/conversations.jsonl")):
            provider_id = conversation_path.parent.name
            records = self._read_jsonl_file(conversation_path)
            for line_number, record in records:
                record_path = f"{self._relpath(conversation_path)}:{line_number}"
                stable_id = self._require_non_empty_string(record, "stable_id", path=record_path)
                if stable_id is None:
                    continue

                source_lane = self._require_non_empty_string(
                    record,
                    "source_lane",
                    path=record_path,
                    stable_id=stable_id,
                )
                source_provider = self._require_non_empty_string(
                    record,
                    "source_provider",
                    path=record_path,
                    stable_id=stable_id,
                )
                source_record_id = self._require_non_empty_string(
                    record,
                    "source_record_id",
                    path=record_path,
                    stable_id=stable_id,
                )
                if None in (source_lane, source_provider, source_record_id):
                    continue

                if not stable_id.startswith("imported_conversation:"):
                    self._add_error(
                        "conversation_stable_id_invalid",
                        f"Imported conversation '{stable_id}' must start with 'imported_conversation:'.",
                        path=record_path,
                        stable_id=stable_id,
                    )
                if source_lane != "imported_conversation":
                    self._add_error(
                        "conversation_lane_invalid",
                        f"Imported conversation '{stable_id}' must declare source_lane 'imported_conversation'.",
                        path=record_path,
                        stable_id=stable_id,
                    )
                if source_provider != provider_id:
                    self._add_error(
                        "conversation_provider_path_mismatch",
                        f"Imported conversation '{stable_id}' is stored under provider '{provider_id}' but declares '{source_provider}'.",
                        path=record_path,
                        stable_id=stable_id,
                    )

                self._register_canonical_record(
                    stable_id,
                    record,
                    self._relpath(conversation_path),
                )
                previous_stable_id = self._conversation_source_identities.get(
                    (source_provider, source_record_id)
                )
                if previous_stable_id is not None and previous_stable_id != stable_id:
                    self._add_error(
                        "conversation_source_identity_conflict",
                        (
                            f"Imported conversation source identity '{source_provider}:{source_record_id}' "
                            f"maps to both '{previous_stable_id}' and '{stable_id}'."
                        ),
                        path=record_path,
                        stable_id=stable_id,
                    )
                else:
                    self._conversation_source_identities[(source_provider, source_record_id)] = stable_id

                source_metadata = record.get("source_metadata")
                if not isinstance(source_metadata, dict):
                    self._add_warning(
                        "conversation_source_metadata_missing",
                        f"Imported conversation '{stable_id}' is missing source_metadata details.",
                        path=record_path,
                        stable_id=stable_id,
                    )
                else:
                    metadata_source = source_metadata.get("source")
                    if metadata_source is None:
                        self._add_warning(
                            "conversation_source_missing",
                            f"Imported conversation '{stable_id}' is missing source_metadata.source.",
                            path=record_path,
                            stable_id=stable_id,
                        )
                    elif metadata_source != source_provider:
                        self._add_error(
                            "conversation_source_metadata_mismatch",
                            f"Imported conversation '{stable_id}' has a source_metadata.source value that does not match source_provider.",
                            path=record_path,
                            stable_id=stable_id,
                        )
                    metadata_source_id = source_metadata.get("source_conversation_id")
                    if metadata_source_id is None:
                        self._add_warning(
                            "conversation_source_id_missing",
                            f"Imported conversation '{stable_id}' is missing source_metadata.source_conversation_id.",
                            path=record_path,
                            stable_id=stable_id,
                        )
                    elif metadata_source_id != source_record_id:
                        self._add_error(
                            "conversation_source_id_mismatch",
                            f"Imported conversation '{stable_id}' has a source_metadata.source_conversation_id value that does not match source_record_id.",
                            path=record_path,
                            stable_id=stable_id,
                        )

                if not self._has_any_value(record, "created_at_unix", "created_at_iso"):
                    self._add_warning(
                        "conversation_timestamp_missing",
                        f"Imported conversation '{stable_id}' is missing created_at timestamp metadata.",
                        path=record_path,
                        stable_id=stable_id,
                    )
                if not self._has_any_value(record, "updated_at_unix", "updated_at_iso"):
                    self._add_warning(
                        "conversation_updated_timestamp_missing",
                        f"Imported conversation '{stable_id}' is missing updated_at timestamp metadata.",
                        path=record_path,
                        stable_id=stable_id,
                    )

                title = record.get("title")
                if not isinstance(title, str) or not title.strip():
                    self._add_warning(
                        "conversation_title_missing",
                        f"Imported conversation '{stable_id}' is missing a readable title.",
                        path=record_path,
                        stable_id=stable_id,
                    )

                self.checked_counts["imported_conversations"] += 1
                self.provider_summary[source_provider]["imported_conversations"] += 1
                self.actual_source_lanes.add("imported_conversation")
                self.actual_source_providers.add(source_provider)
                self.imported_conversations[stable_id] = record
                self._track_timestamp(record.get("updated_at_unix") or record.get("created_at_unix"))

    def _load_imported_messages(self) -> None:
        imported_root = self.package_dir / "conversations" / "imported"
        if not imported_root.exists():
            return

        for message_path in sorted(imported_root.glob("*/messages.jsonl")):
            provider_id = message_path.parent.name
            records = self._read_jsonl_file(message_path)
            for line_number, record in records:
                record_path = f"{self._relpath(message_path)}:{line_number}"
                stable_id = self._require_non_empty_string(record, "stable_id", path=record_path)
                conversation_stable_id = self._require_non_empty_string(
                    record,
                    "conversation_stable_id",
                    path=record_path,
                    stable_id=stable_id,
                )
                source_lane = self._require_non_empty_string(
                    record,
                    "source_lane",
                    path=record_path,
                    stable_id=stable_id,
                )
                source_provider = self._require_non_empty_string(
                    record,
                    "source_provider",
                    path=record_path,
                    stable_id=stable_id,
                )
                source_record_id = self._require_non_empty_string(
                    record,
                    "source_record_id",
                    path=record_path,
                    stable_id=stable_id,
                )
                role = self._require_non_empty_string(
                    record,
                    "role",
                    path=record_path,
                    stable_id=stable_id,
                )
                content = self._require_non_empty_string(
                    record,
                    "content",
                    path=record_path,
                    stable_id=stable_id,
                )
                sequence_index = self._require_non_negative_integer(
                    record,
                    "sequence_index",
                    path=record_path,
                    stable_id=stable_id,
                )

                if None in (
                    stable_id,
                    conversation_stable_id,
                    source_lane,
                    source_provider,
                    source_record_id,
                    role,
                    content,
                    sequence_index,
                ):
                    continue

                if not stable_id.startswith("imported_message:"):
                    self._add_error(
                        "message_stable_id_invalid",
                        f"Imported message '{stable_id}' must start with 'imported_message:'.",
                        path=record_path,
                        stable_id=stable_id,
                    )
                if source_lane != "imported_conversation":
                    self._add_error(
                        "message_lane_invalid",
                        f"Imported message '{stable_id}' must declare source_lane 'imported_conversation'.",
                        path=record_path,
                        stable_id=stable_id,
                    )
                if source_provider != provider_id:
                    self._add_error(
                        "message_provider_path_mismatch",
                        f"Imported message '{stable_id}' is stored under provider '{provider_id}' but declares '{source_provider}'.",
                        path=record_path,
                        stable_id=stable_id,
                    )
                if conversation_stable_id not in self.imported_conversations:
                    self._add_error(
                        "message_conversation_reference_missing",
                        (
                            f"Imported message '{stable_id}' references missing conversation "
                            f"'{conversation_stable_id}'."
                        ),
                        path=record_path,
                        stable_id=stable_id,
                    )
                    continue

                parent_conversation = self.imported_conversations[conversation_stable_id]
                if parent_conversation.get("source_provider") != source_provider:
                    self._add_error(
                        "message_provider_mismatch",
                        f"Imported message '{stable_id}' does not match its parent conversation provider identity.",
                        path=record_path,
                        stable_id=stable_id,
                    )

                self._register_canonical_record(
                    stable_id,
                    record,
                    self._relpath(message_path),
                )
                previous_stable_id = self._message_source_identities.get(
                    (source_provider, conversation_stable_id, source_record_id)
                )
                if previous_stable_id is not None and previous_stable_id != stable_id:
                    self._add_error(
                        "message_source_identity_conflict",
                        (
                            f"Imported message source identity '{source_provider}:{source_record_id}' "
                            f"appears more than once for conversation '{conversation_stable_id}'."
                        ),
                        path=record_path,
                        stable_id=stable_id,
                    )
                else:
                    self._message_source_identities[
                        (source_provider, conversation_stable_id, source_record_id)
                    ] = stable_id

                source_metadata = record.get("source_metadata")
                if not isinstance(source_metadata, dict):
                    self._add_warning(
                        "message_source_metadata_missing",
                        f"Imported message '{stable_id}' is missing source_metadata details.",
                        path=record_path,
                        stable_id=stable_id,
                    )
                else:
                    source_message_id = source_metadata.get("source_message_id")
                    if source_message_id is None:
                        self._add_warning(
                            "message_source_id_missing",
                            f"Imported message '{stable_id}' is missing source_metadata.source_message_id.",
                            path=record_path,
                            stable_id=stable_id,
                        )
                    elif source_message_id != source_record_id:
                        self._add_error(
                            "message_source_id_mismatch",
                            f"Imported message '{stable_id}' has a source_metadata.source_message_id value that does not match source_record_id.",
                            path=record_path,
                            stable_id=stable_id,
                        )
                    conversation_source_id = source_metadata.get("conversation_source_id")
                    if conversation_source_id is None:
                        self._add_warning(
                            "message_conversation_source_id_missing",
                            f"Imported message '{stable_id}' is missing source_metadata.conversation_source_id.",
                            path=record_path,
                            stable_id=stable_id,
                        )
                    elif conversation_source_id != parent_conversation.get("source_record_id"):
                        self._add_error(
                            "message_conversation_source_id_mismatch",
                            (
                                f"Imported message '{stable_id}' points to conversation source id "
                                f"'{conversation_source_id}' but its parent conversation uses "
                                f"'{parent_conversation.get('source_record_id')}'."
                            ),
                            path=record_path,
                            stable_id=stable_id,
                        )

                if not self._has_any_value(record, "created_at_unix", "created_at_iso"):
                    self._add_warning(
                        "message_timestamp_missing",
                        f"Imported message '{stable_id}' is missing created_at timestamp metadata.",
                        path=record_path,
                        stable_id=stable_id,
                    )

                self.checked_counts["imported_messages"] += 1
                self.provider_summary[source_provider]["imported_messages"] += 1
                self.actual_source_lanes.add("imported_conversation")
                self.actual_source_providers.add(source_provider)
                self.message_sequences[conversation_stable_id].append(sequence_index)

    def _validate_message_sequences(self) -> None:
        for conversation_stable_id, sequence_values in self.message_sequences.items():
            if not sequence_values:
                continue
            ordered = sorted(sequence_values)
            expected = list(range(len(sequence_values)))
            if ordered != expected:
                self._add_error(
                    "message_sequence_invalid",
                    (
                        f"Imported conversation '{conversation_stable_id}' has message sequence indices "
                        f"{ordered}, expected {expected}."
                    ),
                    stable_id=conversation_stable_id,
                )

        for conversation_stable_id in self.imported_conversations:
            if conversation_stable_id not in self.message_sequences:
                self._add_warning(
                    "conversation_has_no_messages",
                    f"Imported conversation '{conversation_stable_id}' has no message records.",
                    stable_id=conversation_stable_id,
                )

    def _load_native_memory_entries(self) -> None:
        native_path = self.package_dir / "native" / "memory_entries.jsonl"
        if not native_path.exists():
            return

        records = self._read_jsonl_file(native_path)
        for line_number, record in records:
            record_path = f"{self._relpath(native_path)}:{line_number}"
            stable_id = self._require_non_empty_string(record, "stable_id", path=record_path)
            source_lane = self._require_non_empty_string(
                record,
                "source_lane",
                path=record_path,
                stable_id=stable_id,
            )
            source_provider = self._require_non_empty_string(
                record,
                "source_provider",
                path=record_path,
                stable_id=stable_id,
            )
            source_record_id = self._require_non_empty_string(
                record,
                "source_record_id",
                path=record_path,
                stable_id=stable_id,
            )
            role = self._require_non_empty_string(
                record,
                "role",
                path=record_path,
                stable_id=stable_id,
            )
            content = self._require_non_empty_string(
                record,
                "content",
                path=record_path,
                stable_id=stable_id,
            )

            if None in (stable_id, source_lane, source_provider, source_record_id, role, content):
                continue

            if not stable_id.startswith("memory:"):
                self._add_error(
                    "native_stable_id_invalid",
                    f"Native memory record '{stable_id}' must start with 'memory:'.",
                    path=record_path,
                    stable_id=stable_id,
                )
            if source_lane != "native_memory":
                self._add_error(
                    "native_lane_invalid",
                    f"Native memory record '{stable_id}' must declare source_lane 'native_memory'.",
                    path=record_path,
                    stable_id=stable_id,
                )
            stable_suffix = stable_id.split(":", maxsplit=1)[1] if ":" in stable_id else ""
            if stable_suffix and source_record_id != stable_suffix:
                self._add_error(
                    "native_source_id_mismatch",
                    f"Native memory record '{stable_id}' has source_record_id '{source_record_id}', expected '{stable_suffix}'.",
                    path=record_path,
                    stable_id=stable_id,
                )

            self._register_canonical_record(
                stable_id,
                record,
                self._relpath(native_path),
            )
            source_metadata = record.get("source_metadata")
            if not isinstance(source_metadata, dict):
                self._add_warning(
                    "native_source_metadata_missing",
                    f"Native memory record '{stable_id}' is missing source_metadata details.",
                    path=record_path,
                    stable_id=stable_id,
                )
            else:
                metadata_role = source_metadata.get("role")
                if metadata_role is None:
                    self._add_warning(
                        "native_role_missing",
                        f"Native memory record '{stable_id}' is missing source_metadata.role.",
                        path=record_path,
                        stable_id=stable_id,
                    )
                elif metadata_role != role:
                    self._add_error(
                        "native_role_mismatch",
                        f"Native memory record '{stable_id}' has a source_metadata.role value that does not match role.",
                        path=record_path,
                        stable_id=stable_id,
                    )
                if "tags" not in source_metadata:
                    self._add_warning(
                        "native_tags_missing",
                        f"Native memory record '{stable_id}' is missing source_metadata.tags.",
                        path=record_path,
                        stable_id=stable_id,
                    )

            if not self._has_any_value(record, "timestamp_unix", "timestamp_iso"):
                self._add_warning(
                    "native_timestamp_missing",
                    f"Native memory record '{stable_id}' is missing timestamp metadata.",
                    path=record_path,
                    stable_id=stable_id,
                )

            self.checked_counts["native_memory_entries"] += 1
            self.provider_summary[source_provider]["native_memory_entries"] += 1
            self.actual_source_lanes.add("native_memory")
            self.actual_source_providers.add(source_provider)
            self._track_timestamp(record.get("timestamp_unix"))

    def _validate_provenance(self, manifest: dict[str, Any]) -> None:
        provenance = manifest.get("provenance")
        if not isinstance(provenance, dict):
            return

        index_file = provenance.get("index_file")
        if not isinstance(index_file, str) or not index_file.strip():
            return

        provenance_path = self.package_dir / Path(index_file)
        if not provenance_path.exists():
            self._add_error(
                "provenance_index_missing",
                f"Memory Passport is missing provenance index '{index_file}'.",
                path=index_file,
            )
            return

        for line_number, record in self._read_jsonl_file(provenance_path):
            record_path = f"{self._relpath(provenance_path)}:{line_number}"
            stable_id = self._require_non_empty_string(record, "stable_id", path=record_path)
            unit_type = self._require_non_empty_string(
                record,
                "unit_type",
                path=record_path,
                stable_id=stable_id,
            )
            source_lane = self._require_non_empty_string(
                record,
                "source_lane",
                path=record_path,
                stable_id=stable_id,
            )
            source_provider = self._require_non_empty_string(
                record,
                "source_provider",
                path=record_path,
                stable_id=stable_id,
            )
            source_record_id = self._require_non_empty_string(
                record,
                "source_record_id",
                path=record_path,
                stable_id=stable_id,
            )
            path_value = self._require_non_empty_string(
                record,
                "path",
                path=record_path,
                stable_id=stable_id,
            )
            if None in (stable_id, unit_type, source_lane, source_provider, source_record_id, path_value):
                continue

            if stable_id in self.provenance_records:
                self._add_error(
                    "provenance_stable_id_duplicate",
                    f"Provenance index contains duplicate stable_id '{stable_id}'.",
                    path=record_path,
                    stable_id=stable_id,
                )
                continue
            self.provenance_records[stable_id] = record

            relative_path = Path(path_value)
            if not (self.package_dir / relative_path).exists():
                self._add_error(
                    "provenance_path_missing",
                    f"Provenance record '{stable_id}' points to missing path '{path_value}'.",
                    path=record_path,
                    stable_id=stable_id,
                )

            source_metadata = record.get("source_metadata")
            if not isinstance(source_metadata, dict):
                self._add_warning(
                    "provenance_source_metadata_missing",
                    f"Provenance record '{stable_id}' is missing source_metadata details.",
                    path=record_path,
                    stable_id=stable_id,
                )
                source_metadata = {}

            if unit_type == "canonical":
                canonical_record = self.canonical_records.get(stable_id)
                if canonical_record is None:
                    self._add_error(
                        "provenance_canonical_reference_missing",
                        f"Canonical provenance record '{stable_id}' does not match any exported canonical record.",
                        path=record_path,
                        stable_id=stable_id,
                    )
                    continue
                expected_path = self.canonical_paths.get(stable_id)
                if expected_path is not None and expected_path != path_value:
                    self._add_error(
                        "provenance_canonical_path_mismatch",
                        f"Canonical provenance record '{stable_id}' points to '{path_value}', expected '{expected_path}'.",
                        path=record_path,
                        stable_id=stable_id,
                    )
                self._validate_identity_match(
                    stable_id=stable_id,
                    record_path=record_path,
                    canonical_record=canonical_record,
                    provenance_record=record,
                )
            elif unit_type == "derived":
                canonical_stable_id = None
                if isinstance(source_metadata, dict):
                    canonical_stable_id = source_metadata.get("canonical_stable_id")
                if not isinstance(canonical_stable_id, str) or not canonical_stable_id.strip():
                    self._add_error(
                        "provenance_derived_reference_missing",
                        f"Derived provenance record '{stable_id}' is missing source_metadata.canonical_stable_id.",
                        path=record_path,
                        stable_id=stable_id,
                    )
                    continue
                canonical_record = self.canonical_records.get(canonical_stable_id)
                if canonical_record is None:
                    self._add_error(
                        "provenance_derived_reference_invalid",
                        (
                            f"Derived provenance record '{stable_id}' references missing canonical "
                            f"stable_id '{canonical_stable_id}'."
                        ),
                        path=record_path,
                        stable_id=stable_id,
                    )
                    continue
                self._validate_identity_match(
                    stable_id=stable_id,
                    record_path=record_path,
                    canonical_record=canonical_record,
                    provenance_record=record,
                )
            else:
                self._add_error(
                    "provenance_unit_type_invalid",
                    f"Provenance record '{stable_id}' has unsupported unit_type '{unit_type}'.",
                    path=record_path,
                    stable_id=stable_id,
                )

        self.checked_counts["provenance_units"] = len(self.provenance_records)
        self.checked_counts["derived_units"] = sum(
            1
            for record in self.provenance_records.values()
            if record.get("unit_type") == "derived"
        )

    def _validate_manifest_consistency(self, manifest: dict[str, Any]) -> None:
        counts = manifest.get("counts")
        if isinstance(counts, dict):
            for key in _CANONICAL_COUNT_KEYS:
                expected_value = counts.get(key)
                if isinstance(expected_value, int) and self.checked_counts.get(key) != expected_value:
                    self._add_error(
                        "manifest_count_mismatch",
                        (
                            f"manifest.json count '{key}' is {expected_value}, but the package "
                            f"contains {self.checked_counts.get(key, 0)}."
                        ),
                        path="manifest.json",
                    )

        source_lanes = manifest.get("source_lanes")
        if isinstance(source_lanes, list):
            manifest_lanes = {value for value in source_lanes if isinstance(value, str) and value.strip()}
            if manifest_lanes != self.actual_source_lanes:
                self._add_error(
                    "manifest_source_lanes_mismatch",
                    (
                        f"manifest.json source_lanes {sorted(manifest_lanes)} do not match "
                        f"the exported lanes {sorted(self.actual_source_lanes)}."
                    ),
                    path="manifest.json",
                )

        source_providers = manifest.get("source_providers")
        if isinstance(source_providers, list):
            manifest_providers = {
                value for value in source_providers if isinstance(value, str) and value.strip()
            }
            if manifest_providers != self.actual_source_providers:
                self._add_error(
                    "manifest_source_providers_mismatch",
                    (
                        f"manifest.json source_providers {sorted(manifest_providers)} do not match "
                        f"the exported providers {sorted(self.actual_source_providers)}."
                    ),
                    path="manifest.json",
                )

        time_range = manifest.get("time_range")
        if self.actual_timestamps:
            if time_range is None:
                self._add_warning(
                    "manifest_time_range_missing",
                    "manifest.json is missing optional time_range even though timestamped records are present.",
                    path="manifest.json",
                )
            elif isinstance(time_range, dict):
                min_timestamp = min(self.actual_timestamps)
                max_timestamp = max(self.actual_timestamps)
                if time_range.get("min_timestamp_unix") != min_timestamp:
                    self._add_error(
                        "manifest_min_time_range_mismatch",
                        (
                            "manifest.json time_range.min_timestamp_unix does not match the "
                            "minimum timestamp found in canonical records."
                        ),
                        path="manifest.json",
                    )
                if time_range.get("max_timestamp_unix") != max_timestamp:
                    self._add_error(
                        "manifest_max_time_range_mismatch",
                        (
                            "manifest.json time_range.max_timestamp_unix does not match the "
                            "maximum timestamp found in canonical records."
                        ),
                        path="manifest.json",
                    )

    def _validate_identity_match(
        self,
        *,
        stable_id: str,
        record_path: str,
        canonical_record: dict[str, Any],
        provenance_record: dict[str, Any],
    ) -> None:
        for field_name in ("source_lane", "source_provider", "source_record_id"):
            if provenance_record.get(field_name) != canonical_record.get(field_name):
                self._add_error(
                    "provenance_identity_mismatch",
                    (
                        f"Provenance record '{stable_id}' field '{field_name}' does not match "
                        "the canonical record it points to."
                    ),
                    path=record_path,
                    stable_id=stable_id,
                )

    def _register_canonical_record(
        self,
        stable_id: str,
        record: dict[str, Any],
        relative_path: str,
    ) -> None:
        existing_record = self.canonical_records.get(stable_id)
        if existing_record is not None:
            self._add_error(
                "canonical_stable_id_duplicate",
                f"Canonical export contains duplicate stable_id '{stable_id}'.",
                path=relative_path,
                stable_id=stable_id,
            )
            return
        self.canonical_records[stable_id] = record
        self.canonical_paths[stable_id] = relative_path

    def _read_json_file(self, path: Path) -> Any | None:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            self._add_error(
                "json_parse_error",
                f"Could not parse JSON file '{self._relpath(path)}': {exc.msg}.",
                path=self._relpath(path),
            )
        except OSError as exc:
            self._add_error(
                "file_read_error",
                f"Could not read file '{self._relpath(path)}': {exc.strerror or str(exc)}.",
                path=self._relpath(path),
            )
        return None

    def _read_jsonl_file(self, path: Path) -> list[tuple[int, dict[str, Any]]]:
        try:
            content = path.read_text(encoding="utf-8")
        except OSError as exc:
            self._add_error(
                "file_read_error",
                f"Could not read file '{self._relpath(path)}': {exc.strerror or str(exc)}.",
                path=self._relpath(path),
            )
            return []

        records: list[tuple[int, dict[str, Any]]] = []
        for line_number, line in enumerate(content.splitlines(), start=1):
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError as exc:
                self._add_error(
                    "jsonl_parse_error",
                    f"Could not parse JSONL record at {self._relpath(path)}:{line_number}: {exc.msg}.",
                    path=f"{self._relpath(path)}:{line_number}",
                )
                continue
            if not isinstance(payload, dict):
                self._add_error(
                    "jsonl_record_invalid_type",
                    f"JSONL record at {self._relpath(path)}:{line_number} must be a JSON object.",
                    path=f"{self._relpath(path)}:{line_number}",
                )
                continue
            records.append((line_number, payload))
        return records

    def _require_non_empty_string(
        self,
        record: dict[str, Any],
        field_name: str,
        *,
        path: str,
        stable_id: str | None = None,
    ) -> str | None:
        value = record.get(field_name)
        if not isinstance(value, str) or not value.strip():
            self._add_error(
                "field_missing_or_blank",
                f"Record is missing required non-empty field '{field_name}'.",
                path=path,
                stable_id=stable_id,
            )
            return None
        return value

    def _require_non_negative_integer(
        self,
        record: dict[str, Any],
        field_name: str,
        *,
        path: str,
        stable_id: str | None = None,
    ) -> int | None:
        value = record.get(field_name)
        if not isinstance(value, int) or value < 0:
            self._add_error(
                "field_invalid_integer",
                f"Record field '{field_name}' must be a non-negative integer.",
                path=path,
                stable_id=stable_id,
            )
            return None
        return value

    def _has_any_value(self, record: dict[str, Any], *field_names: str) -> bool:
        return any(record.get(field_name) is not None for field_name in field_names)

    def _track_timestamp(self, value: Any) -> None:
        if isinstance(value, (int, float)):
            self.actual_timestamps.append(float(value))

    def _relpath(self, path: Path) -> str:
        try:
            return path.relative_to(self.package_dir).as_posix()
        except ValueError:
            return path.as_posix()

    def _add_error(
        self,
        code: str,
        message: str,
        *,
        path: str | None = None,
        stable_id: str | None = None,
    ) -> None:
        self.errors.append(
            PassportValidationDiagnostic(
                code=code,
                message=message,
                path=path,
                stable_id=stable_id,
            )
        )

    def _add_warning(
        self,
        code: str,
        message: str,
        *,
        path: str | None = None,
        stable_id: str | None = None,
    ) -> None:
        self.warnings.append(
            PassportValidationDiagnostic(
                code=code,
                message=message,
                path=path,
                stable_id=stable_id,
            )
        )
