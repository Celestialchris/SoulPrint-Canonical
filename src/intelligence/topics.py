"""Cross-conversation topic detection for derived intelligence."""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
import uuid

from .provider import LLMProvider


@dataclass(frozen=True)
class TopicCluster:
    """A detected topic shared across multiple imported conversations."""

    topic_label: str
    conversation_stable_ids: list[str]
    conversation_titles: list[str]
    confidence: str  # "high", "medium", or "low"


@dataclass(frozen=True)
class TopicScan:
    """A complete topic scan result — derived, non-canonical."""

    scan_id: str
    generation_timestamp: str
    llm_provider_used: str
    clusters: list[dict]
    conversation_count: int
    derived_from: str
    artifact_kind: str


# Words too common to be meaningful topic signals
_STOP_WORDS = frozenset(
    "a an the and or but in on at to for of is it this that with from by "
    "be are was were been have has had do does did will would could should "
    "can may might shall not no yes so if then than too also just about up "
    "out how what when where who which why all each every some any many "
    "more most other another such only own same into over after before "
    "between through during without again further once here there these "
    "those me my he she we they its his her our their you your i".split()
)


def _keyword_fallback_topics(conversations: list) -> list[TopicCluster]:
    """Extract topic clusters from conversation titles using keyword frequency.

    Groups conversations that share significant title keywords.
    No LLM needed — purely lexical.
    """
    if not conversations:
        return []

    # Build word → conversation mapping from titles
    word_to_convs: dict[str, list[int]] = {}
    conv_map: dict[int, tuple[str, str]] = {}  # id → (stable_id, title)

    for conv in conversations:
        conv_id = conv.id
        title = conv.title or "Untitled"
        stable_id = f"imported_conversation:{conv_id}"
        conv_map[conv_id] = (stable_id, title)

        words = set(re.findall(r"[a-zA-Z]{3,}", title.lower()))
        words -= _STOP_WORDS

        for word in words:
            word_to_convs.setdefault(word, []).append(conv_id)

    # Find words shared across 2+ conversations
    shared_words = {
        word: conv_ids
        for word, conv_ids in word_to_convs.items()
        if len(set(conv_ids)) >= 2
    }

    if not shared_words:
        return []

    # Rank by frequency descending, take top clusters
    ranked = sorted(shared_words.items(), key=lambda x: len(set(x[1])), reverse=True)

    seen_groups: list[TopicCluster] = []
    used_conv_ids: set[int] = set()

    for word, conv_ids in ranked[:5]:
        unique_ids = sorted(set(conv_ids))
        # Skip if all conversations in this cluster are already covered
        if all(cid in used_conv_ids for cid in unique_ids):
            continue

        stable_ids = [conv_map[cid][0] for cid in unique_ids]
        titles = [conv_map[cid][1] for cid in unique_ids]

        seen_groups.append(
            TopicCluster(
                topic_label=word.capitalize(),
                conversation_stable_ids=stable_ids,
                conversation_titles=titles,
                confidence="low",
            )
        )
        used_conv_ids.update(unique_ids)

    return seen_groups


def _llm_extract_topics(conversations: list, provider: LLMProvider) -> list[TopicCluster]:
    """Use an LLM to detect topic clusters across conversations."""
    if not conversations:
        return []

    # Build a compact listing of conversation titles + first messages
    lines: list[str] = []
    conv_map: dict[int, tuple[str, str]] = {}

    for conv in conversations:
        conv_id = conv.id
        title = conv.title or "Untitled"
        stable_id = f"imported_conversation:{conv_id}"
        conv_map[conv_id] = (stable_id, title)

        first_msg = ""
        if conv.messages:
            sorted_msgs = sorted(conv.messages, key=lambda m: m.sequence_index)
            first_msg = (sorted_msgs[0].content or "")[:200]

        lines.append(f"[ID:{conv_id}] {title}: {first_msg}")

    prompt_text = "\n".join(lines)
    messages = [
        {
            "role": "user",
            "content": (
                "Analyze these conversation titles and first messages. "
                "Identify 2-5 recurring topic themes. For each theme, list which "
                "conversation IDs (the numbers in brackets) relate to it.\n\n"
                "Format each topic as:\n"
                "TOPIC: <label>\n"
                "IDS: <comma-separated numbers>\n"
                "CONFIDENCE: high|medium|low\n\n"
                f"{prompt_text}"
            ),
        }
    ]

    response_text = provider.summarize(messages)

    # Parse the LLM response into TopicClusters
    clusters: list[TopicCluster] = []
    current_label = None
    current_ids: list[int] = []
    current_confidence = "medium"

    for line in response_text.split("\n"):
        line = line.strip()
        if line.upper().startswith("TOPIC:"):
            # Save previous cluster if any
            if current_label and current_ids:
                valid_ids = [cid for cid in current_ids if cid in conv_map]
                if len(valid_ids) >= 2:
                    clusters.append(
                        TopicCluster(
                            topic_label=current_label,
                            conversation_stable_ids=[conv_map[cid][0] for cid in valid_ids],
                            conversation_titles=[conv_map[cid][1] for cid in valid_ids],
                            confidence=current_confidence,
                        )
                    )
            current_label = line.split(":", 1)[1].strip()
            current_ids = []
            current_confidence = "medium"
        elif line.upper().startswith("IDS:"):
            raw = line.split(":", 1)[1].strip()
            current_ids = [
                int(x.strip()) for x in raw.split(",")
                if x.strip().isdigit()
            ]
        elif line.upper().startswith("CONFIDENCE:"):
            val = line.split(":", 1)[1].strip().lower()
            if val in ("high", "medium", "low"):
                current_confidence = val

    # Save last cluster
    if current_label and current_ids:
        valid_ids = [cid for cid in current_ids if cid in conv_map]
        if len(valid_ids) >= 2:
            clusters.append(
                TopicCluster(
                    topic_label=current_label,
                    conversation_stable_ids=[conv_map[cid][0] for cid in valid_ids],
                    conversation_titles=[conv_map[cid][1] for cid in valid_ids],
                    confidence=current_confidence,
                )
            )

    # If LLM didn't produce usable output, fall back to keywords
    if not clusters:
        return _keyword_fallback_topics(conversations)

    return clusters


def extract_topics(
    conversations: list,
    provider: LLMProvider | None = None,
) -> TopicScan:
    """Detect shared topics across imported conversations.

    Uses the LLM provider when available; falls back to keyword-frequency
    extraction when provider is None.
    """
    if provider is not None:
        clusters = _llm_extract_topics(conversations, provider)
        provider_used = provider.provider_name
    else:
        clusters = _keyword_fallback_topics(conversations)
        provider_used = "keyword_fallback"

    return TopicScan(
        scan_id=f"topic_scan:{uuid.uuid4()}",
        generation_timestamp=datetime.now(tz=timezone.utc).isoformat(timespec="seconds"),
        llm_provider_used=provider_used,
        clusters=[
            {
                "topic_label": c.topic_label,
                "conversation_stable_ids": list(c.conversation_stable_ids),
                "conversation_titles": list(c.conversation_titles),
                "confidence": c.confidence,
            }
            for c in clusters
        ],
        conversation_count=len(conversations),
        derived_from="canonical_imported_conversations",
        artifact_kind="topic_scan_v1",
    )
