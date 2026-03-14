"""Cross-conversation digest generation for derived intelligence."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import uuid

from .provider import LLMProvider


@dataclass(frozen=True)
class DerivedDigest:
    """Derived, non-canonical digest synthesizing multiple conversations around one topic."""

    digest_id: str
    topic_label: str
    source_conversation_stable_ids: list[str]
    source_conversation_titles: list[str]
    generation_timestamp: str
    llm_provider_used: str
    prompt_template_version: str
    digest_text: str
    derived_from: str
    artifact_kind: str


PROMPT_TEMPLATE_VERSION = "v1"


def generate_digest(
    topic_label: str,
    conversations: list,
    provider: LLMProvider,
) -> DerivedDigest:
    """Synthesize a digest across multiple conversations sharing one topic.

    ``conversations`` must each expose ``.id``, ``.title``, and ``.messages``
    (each with ``.role``, ``.content``, ``.sequence_index``).
    """
    # Build message list from all conversations
    combined_messages: list[dict] = []
    stable_ids: list[str] = []
    titles: list[str] = []

    for conv in conversations:
        stable_id = f"imported_conversation:{conv.id}"
        title = conv.title or "Untitled conversation"
        stable_ids.append(stable_id)
        titles.append(title)

        sorted_msgs = sorted(conv.messages, key=lambda m: m.sequence_index)
        combined_messages.append(
            {
                "role": "user",
                "content": (
                    f"--- Conversation: {title} ---\n"
                    + "\n".join(
                        f"[{m.role}]: {m.content}" for m in sorted_msgs
                    )
                ),
            }
        )

    # Prepend a framing message for the digest task
    framing = {
        "role": "user",
        "content": (
            f"Synthesize a digest about the topic '{topic_label}' across the "
            f"following {len(conversations)} conversations. Identify common "
            "threads, key decisions, and recurring themes. Be concise and factual."
        ),
    }
    all_messages = [framing] + combined_messages

    digest_text = provider.summarize(all_messages)

    return DerivedDigest(
        digest_id=f"derived_digest:{uuid.uuid4()}",
        topic_label=topic_label,
        source_conversation_stable_ids=stable_ids,
        source_conversation_titles=titles,
        generation_timestamp=datetime.now(tz=timezone.utc).isoformat(timespec="seconds"),
        llm_provider_used=provider.provider_name,
        prompt_template_version=PROMPT_TEMPLATE_VERSION,
        digest_text=digest_text,
        derived_from="canonical_imported_conversations",
        artifact_kind="derived_digest_v1",
    )
