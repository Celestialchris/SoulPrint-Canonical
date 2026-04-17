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
MAX_INPUT_CHARS = 180_000   # safe for 65k-context local models (~45k tokens)


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
    input_truncated: bool = False


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


def _build_multi_transcript(
    conversations: list, max_chars: int
) -> tuple[str, bool]:
    """Format conversations into a multi-transcript string, capped at *max_chars*.

    Conversations are sorted most-recent-first by ``created_at_unix`` so the
    newest context survives when budget is exhausted.

    Returns ``(transcript, truncated)`` where *truncated* is True when one or
    more conversations were dropped due to the budget.
    """
    sorted_convs = sorted(
        conversations,
        key=lambda c: getattr(c, "created_at_unix", 0) or 0,
        reverse=True,
    )
    parts: list[str] = []
    used = 0
    truncated = False
    for conv in sorted_convs:
        title = conv.title or "Untitled"
        source = getattr(conv, "source", "unknown")
        sorted_msgs = sorted(conv.messages, key=lambda m: m.sequence_index)
        lines = [f"[{m.role}]: {m.content}" for m in sorted_msgs]
        header = f"=== Conversation: {title} (provider: {source}) ==="
        block = header + "\n" + "\n".join(lines)
        separator_cost = 2 if parts else 0  # "\n\n" only between blocks
        if used + separator_cost + len(block) > max_chars:
            truncated = True
            break
        parts.append(block)
        used += separator_cost + len(block)
    return "\n\n".join(parts), truncated


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

    transcript, truncated = _build_multi_transcript(conversations, MAX_INPUT_CHARS)

    user_message = (
        f"Distill the following {len(conversations)} conversations "
        f"({total_messages} total messages) into a single compact "
        f"continuation handoff document.\n\n{transcript}"
    )

    distilled_text = provider.complete(_SYSTEM_PROMPT, user_message)
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
        input_truncated=truncated,
    )
