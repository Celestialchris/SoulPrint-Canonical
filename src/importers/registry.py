"""Provider registry and import-file detection/runtime helpers."""

from __future__ import annotations

import json
from dataclasses import dataclass
from json import JSONDecodeError
from pathlib import Path
from typing import Any, Callable

from .chatgpt import ChatGPTImporter, DEFAULT_TITLE as CHATGPT_DEFAULT_TITLE, looks_like_chatgpt_export
from .claude import ClaudeImporter, DEFAULT_TITLE as CLAUDE_DEFAULT_TITLE, looks_like_claude_export
from .contracts import (
    PROVIDER_CHATGPT,
    PROVIDER_CLAUDE,
    PROVIDER_GEMINI,
    ConversationImporter,
    NormalizedConversation,
    validate_provider_id,
)
from .errors import (
    ImportProviderDetectionError,
    MalformedImportFileError,
    UnsupportedImportFormatError,
)
from .gemini import GeminiImporter, DEFAULT_TITLE as GEMINI_DEFAULT_TITLE, looks_like_gemini_export


_DEFAULT_TITLES = frozenset({CHATGPT_DEFAULT_TITLE, CLAUDE_DEFAULT_TITLE, GEMINI_DEFAULT_TITLE})


@dataclass(frozen=True)
class ImportProviderSpec:
    """One provider adapter plus optional auto-detection rule."""

    provider_id: str
    importer: ConversationImporter
    detector: Callable[[Any], bool] | None = None


@dataclass(frozen=True)
class ImportParseResult:
    """Parsed provider batch with non-fatal diagnostics."""

    provider_id: str
    conversations: list[NormalizedConversation]
    warnings: list[str]


_PROVIDER_SPECS: dict[str, ImportProviderSpec] = {
    PROVIDER_CHATGPT: ImportProviderSpec(
        provider_id=PROVIDER_CHATGPT,
        importer=ChatGPTImporter(),
        detector=looks_like_chatgpt_export,
    ),
    PROVIDER_CLAUDE: ImportProviderSpec(
        provider_id=PROVIDER_CLAUDE,
        importer=ClaudeImporter(),
        detector=looks_like_claude_export,
    ),
    PROVIDER_GEMINI: ImportProviderSpec(
        provider_id=PROVIDER_GEMINI,
        importer=GeminiImporter(),
        detector=looks_like_gemini_export,
    ),
}


def available_import_providers() -> tuple[str, ...]:
    """Return supported provider ids for CLI choices and validation."""

    return tuple(_PROVIDER_SPECS)


def parse_import_file(
    path: str | Path,
    *,
    provider_hint: str | None = None,
) -> ImportParseResult:
    """Load, detect, and parse one provider export file."""

    payload = _load_json_payload(path)
    spec = _resolve_provider_spec(payload, provider_hint=provider_hint)

    try:
        conversations = spec.importer.parse_payload(payload)
    except UnsupportedImportFormatError:
        raise
    except ValueError as exc:
        raise MalformedImportFileError(
            f"{spec.provider_id} import payload is malformed or unsupported: {exc}"
        ) from exc

    return ImportParseResult(
        provider_id=spec.provider_id,
        conversations=conversations,
        warnings=_collect_import_warnings(spec.provider_id, conversations),
    )


def _load_json_payload(path: str | Path) -> Any:
    try:
        with Path(path).open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except JSONDecodeError as exc:
        raise MalformedImportFileError(f"Import file is not valid JSON: {exc}") from exc


def _resolve_provider_spec(
    payload: Any,
    *,
    provider_hint: str | None,
) -> ImportProviderSpec:
    if provider_hint and provider_hint != "auto":
        normalized_hint = validate_provider_id(provider_hint)
        return _PROVIDER_SPECS[normalized_hint]

    matches = [
        provider_id
        for provider_id, spec in _PROVIDER_SPECS.items()
        if spec.detector is not None and spec.detector(payload)
    ]
    if len(matches) == 1:
        return _PROVIDER_SPECS[matches[0]]
    if len(matches) > 1:
        raise ImportProviderDetectionError(
            "Import provider detection matched multiple providers; rerun with --provider."
        )
    raise ImportProviderDetectionError(
        "Could not detect import provider from JSON. Supported auto-detect formats: chatgpt, claude, and gemini. "
        "Use --provider to force a recognized provider."
    )


def _collect_import_warnings(
    provider_id: str,
    conversations: list[NormalizedConversation],
) -> list[str]:
    warnings: list[str] = []

    missing_titles = sum(1 for conversation in conversations if conversation.title in _DEFAULT_TITLES)
    if missing_titles:
        warnings.append(
            f"{provider_id}: {missing_titles} conversation(s) used a fallback title because the provider export did not include one."
        )

    missing_conversation_timestamps = sum(
        1
        for conversation in conversations
        if conversation.created_at is None or conversation.updated_at is None
    )
    if missing_conversation_timestamps:
        warnings.append(
            f"{provider_id}: {missing_conversation_timestamps} conversation(s) are missing create/update timestamps."
        )

    missing_message_timestamps = sum(
        1
        for conversation in conversations
        for message in conversation.messages
        if message.created_at is None
    )
    if missing_message_timestamps:
        warnings.append(
            f"{provider_id}: {missing_message_timestamps} message(s) are missing created_at timestamps."
        )

    return warnings
