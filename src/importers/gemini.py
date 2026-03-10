"""Gemini importer boundary.

Gemini is recognized as a provider slot, but parser support remains fenced until
the repo carries a real fixture-backed export shape.
"""

from __future__ import annotations

from typing import Any

from .contracts import PROVIDER_GEMINI, ConversationImporter, NormalizedConversation
from .errors import UnsupportedImportFormatError


class GeminiImporter(ConversationImporter):
    """Placeholder importer for a recognized-but-unsupported Gemini slot."""

    provider_id = PROVIDER_GEMINI

    def parse_payload(self, payload: Any) -> list[NormalizedConversation]:
        raise UnsupportedImportFormatError(
            "Gemini provider is recognized, but no fixture-backed export parser is implemented yet."
        )
