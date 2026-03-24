"""Multi-conversation distillation — condense N conversations into one paste-ready handoff.

This is the core SoulPrint differentiator: take a set of related conversations
(potentially 100K+ tokens across multiple providers) and produce a single,
compact markdown document that can be pasted into a new AI chat so the
LLM doesn't start from zero.

Architecture:
- Uses the same ``LLMProvider`` interface as summaries and digests.
- Output is derived, non-canonical, and traceable to canonical stable IDs.
- Stored as JSONL alongside other intelligence artifacts.
- Bounded output size (target: 2K-6K tokens ≈ 8K-24K chars).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import uuid

from .provider import LLMProvider


PROMPT_TEMPLATE_VERSION = "distill-v1"

MAX_DISTILL_CHARS = 24_000  # ~6K tokens, enough context without overwhelming


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DistillationResult:
    """Derived, non-canonical distillation of multiple conversations."""

    distillation_id: str
    source_conversation_stable_ids: list[str]
    source_conversation_titles: list[str]
    source_providers: list[str]
    generation_timestamp: str
    llm_provider_used: str
    prompt_template_version: str
    distilled_text: str
    conversation_count: int
    total_message_count: int
    derived_from: str = "canonical_imported_conversations"
    artifact_kind: str = "distillation_v1"


# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------


_SYSTEM_PROMPT = (
    "You are a continuity distillation engine. You receive transcripts from "
    "multiple AI conversations and produce a single, compact handoff document "
    "that can be pasted into a fresh AI chat to restore full context.\n"
    "\n"
    "Produce a markdown document with these sections:\n"
    "\n"
    "## Context\n"
    "A concise summary of what was discussed across all conversations. "
    "Identify the main project, goal, or thread connecting them.\n"
    "\n"
    "## Key Decisions\n"
    "Concrete decisions, conclusions, and agreements reached. Bullet list.\n"
    "\n"
    "## Current State\n"
    "Where things stand right now. What has been done, what exists.\n"
    "\n"
    "## Open Threads\n"
    "Unresolved questions, deferred items, and work in progress. Bullet list.\n"
    "\n"
    "## Key Entities\n"
    "Important people, projects, tools, concepts, and technical terms "
    "referenced across the conversations. Brief definitions where helpful.\n"
    "\n"
    "## Continue From Here\n"
    "A 2-3 sentence prompt seed that tells the receiving AI exactly "
    "where to pick up. Be specific and actionable.\n"
    "\n"
    "Rules:\n"
    "- Be factual and grounded. Do not invent information not present.\n"
    "- Prioritize recent conversations over older ones when they conflict.\n"
    "- Be concise — this document must be compact enough to paste into a "
    "chat context window without wasting tokens.\n"
    "- If a section has no entries, include the heading with 'None identified.'\n"
    "- Do NOT include preamble, commentary, or meta-notes about your process.\n"
)


def _build_multi_transcript(conversations: list) -> str:
    """Format multiple conversations into a compact multi-transcript string.

    Each ``conversation`` must expose ``.id``, ``.title``, ``.source``,
    and ``.messages`` (each with ``.role``, ``.content``, ``.sequence_index``).
    """
    parts: list[str] = []
    for conv in conversations:
        title = conv.title or "Untitled"
        source = getattr(conv, "source", "unknown")
        sorted_msgs = sorted(conv.messages, key=lambda m: m.sequence_index)
        lines = [f"[{m.role}]: {m.content}" for m in sorted_msgs]
        header = f"=== Conversation: {title} (provider: {source}) ==="
        parts.append(header + "\n" + "\n".join(lines))
    return "\n\n".join(parts)


def _truncate(text: str, max_chars: int) -> str:
    """Truncate to *max_chars*, breaking at a line boundary when possible."""
    if len(text) <= max_chars:
        return text
    suffix = "\n\n[distillation truncated]"
    budget = max_chars - len(suffix)
    cut = text[:budget]
    last_nl = cut.rfind("\n")
    if last_nl > budget * 0.5:
        cut = cut[:last_nl]
    return cut.rstrip() + suffix


# ---------------------------------------------------------------------------
# Distillation
# ---------------------------------------------------------------------------


def distill_conversations(
    conversations: list,
    provider: LLMProvider,
) -> DistillationResult:
    """Distill multiple conversations into a single paste-ready handoff.

    Parameters
    ----------
    conversations:
        ORM objects, each with ``.id``, ``.title``, ``.source``, and
        ``.messages`` (each with ``.role``, ``.content``, ``.sequence_index``).
    provider:
        An ``LLMProvider`` instance (stub, openai, or anthropic).

    Returns a ``DistillationResult`` with the condensed markdown.
    """
    if not conversations:
        return DistillationResult(
            distillation_id=f"distillation:{uuid.uuid4()}",
            source_conversation_stable_ids=[],
            source_conversation_titles=[],
            source_providers=[],
            generation_timestamp=datetime.now(tz=timezone.utc).isoformat(timespec="seconds"),
            llm_provider_used=provider.provider_name,
            prompt_template_version=PROMPT_TEMPLATE_VERSION,
            distilled_text="No conversations provided for distillation.",
            conversation_count=0,
            total_message_count=0,
        )

    stable_ids: list[str] = []
    titles: list[str] = []
    providers: list[str] = []
    total_messages = 0

    for conv in conversations:
        stable_ids.append(f"imported_conversation:{conv.id}")
        titles.append(conv.title or "Untitled")
        source = getattr(conv, "source", "unknown")
        if source not in providers:
            providers.append(source)
        total_messages += len(conv.messages)

    transcript = _build_multi_transcript(conversations)

    # Build the message payload for the provider
    messages = [
        {
            "role": "user",
            "content": (
                f"Distill the following {len(conversations)} conversations "
                f"({total_messages} total messages) into a single compact "
                f"continuation handoff document.\n\n{transcript}"
            ),
        }
    ]

    # The provider.summarize() method accepts messages and returns text.
    # We prepend the system prompt as a user-role framing message
    # since the summarize interface takes a flat message list.
    framed_messages = [
        {"role": "user", "content": _SYSTEM_PROMPT},
    ] + messages

    distilled_text = provider.summarize(framed_messages)
    distilled_text = _truncate(distilled_text, MAX_DISTILL_CHARS)

    return DistillationResult(
        distillation_id=f"distillation:{uuid.uuid4()}",
        source_conversation_stable_ids=stable_ids,
        source_conversation_titles=titles,
        source_providers=providers,
        generation_timestamp=datetime.now(tz=timezone.utc).isoformat(timespec="seconds"),
        llm_provider_used=provider.provider_name,
        prompt_template_version=PROMPT_TEMPLATE_VERSION,
        distilled_text=distilled_text,
        conversation_count=len(conversations),
        total_message_count=total_messages,
    )
