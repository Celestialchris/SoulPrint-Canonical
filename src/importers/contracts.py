"""Provider-agnostic importer normalization contract.

This module defines the smallest contract needed for importer adapters to feed
canonical persistence without changing canonical storage semantics.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


# Canonical provider identifiers currently supported by importer runtime.
PROVIDER_CHATGPT = "chatgpt"
PROVIDER_CLAUDE = "claude"
PROVIDER_GEMINI = "gemini"
PROVIDER_GROK = "grok"
SUPPORTED_IMPORT_PROVIDERS = frozenset(
    {
        PROVIDER_CHATGPT,
        PROVIDER_CLAUDE,
        PROVIDER_GEMINI,
        PROVIDER_GROK,
    }
)


@dataclass(slots=True, frozen=True)
class NormalizedMessage:
    """Normalized message row for a single conversation turn."""

    source_message_id: str
    role: str
    content: str
    sequence_index: int
    created_at: float | None


@dataclass(slots=True, frozen=True)
class NormalizedConversation:
    """Normalized conversation with explicit source provider and provenance IDs."""

    source_provider: str
    source_conversation_id: str
    title: str
    created_at: float | None
    updated_at: float | None
    messages: list[NormalizedMessage]
    source_metadata: dict[str, Any] = field(default_factory=dict)


class ConversationImporter(Protocol):
    """Importer adapter contract for one provider export shape."""

    provider_id: str

    def parse_payload(self, payload: Any) -> list[NormalizedConversation]:
        """Normalize provider payload into canonical conversation units."""


def validate_provider_id(provider_id: str) -> str:
    """Validate and normalize importer provider identity.

    Raises:
        ValueError: If provider_id is blank or unsupported.
    """

    normalized = provider_id.strip().lower()
    if not normalized:
        raise ValueError("Provider id must be a non-empty string")
    if normalized not in SUPPORTED_IMPORT_PROVIDERS:
        raise ValueError(f"Unsupported importer provider: {provider_id}")
    return normalized
