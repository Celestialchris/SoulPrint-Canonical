"""Orchestrates one conversation summarization as a derived artifact."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import uuid

from .provider import LLMProvider


@dataclass(frozen=True)
class DerivedSummary:
    """Derived, non-canonical summary of one imported conversation."""

    summary_id: str
    source_conversation_stable_id: str
    source_conversation_title: str
    generation_timestamp: str
    llm_provider_used: str
    prompt_template_version: str
    summary_text: str
    derived_from: str
    artifact_kind: str


PROMPT_TEMPLATE_VERSION = "v1"


def summarize_conversation(conversation, provider: LLMProvider) -> DerivedSummary:
    """Run one summarization against a provider and return a provenance-bound artifact.

    ``conversation`` must expose ``.id``, ``.title``, and ``.messages`` (each with
    ``.role``, ``.content``, ``.sequence_index``).
    """
    sorted_messages = sorted(conversation.messages, key=lambda m: m.sequence_index)
    message_dicts = [
        {"role": m.role, "content": m.content} for m in sorted_messages
    ]

    summary_text = provider.summarize(message_dicts)

    return DerivedSummary(
        summary_id=f"derived_summary:{uuid.uuid4()}",
        source_conversation_stable_id=f"imported_conversation:{conversation.id}",
        source_conversation_title=conversation.title or "Untitled conversation",
        generation_timestamp=datetime.now(tz=timezone.utc).isoformat(timespec="seconds"),
        llm_provider_used=provider.provider_name,
        prompt_template_version=PROMPT_TEMPLATE_VERSION,
        summary_text=summary_text,
        derived_from="canonical_imported_conversation",
        artifact_kind="derived_summary_v1",
    )
