"""Continuity packet generation service — derives typed artifacts from canonical conversations."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path

from ..provider import LLMProvider
from .models import ContinuityArtifact, make_artifact_id, make_timestamp
from .store import append_artifact


logger = logging.getLogger(__name__)

# Transcript budget: cap the rendered transcript so the system prompt,
# transcript, and response budget fit inside the provider's context window.
#
# Observed Gemma/Ollama tokenizer density on real conversation content is
# roughly 2 chars/token, denser than the 4 chars/token English-prose
# estimate the original budget assumed. At 2 chars/token, 80,000 chars
# renders to ~40K input tokens. With max_tokens=16384 reserved for the
# response and ~500 tokens of system + wrapper + chat-template overhead,
# total prompt usage is ~56.5K tokens, leaving ~9K tokens of headroom in
# Ollama's 65,536-token context. If you target a smaller-context model,
# lower this constant further.
MAX_TRANSCRIPT_CHARS = 80_000

PROMPT_TEMPLATE_VERSION = "v1"

# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ContinuityPacketResult:
    """Outcome of one continuity packet generation run."""

    conversation_stable_id: str
    artifacts: list[ContinuityArtifact]
    error: str | None = None


# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = (
    "You are a continuity extraction engine. Given a conversation transcript, "
    "produce a structured JSON object with exactly four keys:\n"
    "\n"
    '  "summary": a concise paragraph capturing the core discussion,\n'
    '  "decisions": a list of strings — concrete decisions or conclusions reached,\n'
    '  "open_loops": a list of strings — unresolved questions, deferred items, or threads left open,\n'
    '  "entity_map": a list of strings — key people, projects, tools, or concepts referenced.\n'
    "\n"
    "Rules:\n"
    "- Be factual and grounded. Do not invent information not present in the transcript.\n"
    "- If a section has no entries, return an empty list.\n"
    "- Return ONLY the JSON object. No markdown, no commentary.\n"
)


def _render_message_for_transcript(message) -> str:
    return f"[{message.role}]: {message.content}"


def _truncate_messages_to_budget(messages: list, max_chars: int) -> tuple[list, int]:
    """Drop oldest messages until rendered total fits within max_chars.

    Returns (kept_messages, dropped_count). Always preserves at least the
    most-recent message. If that message alone exceeds max_chars, replaces it
    with a lightweight stand-in whose content keeps the tail of the original
    and prepends a truncation marker.
    """
    def rendered_size(msgs):
        return len("\n".join(_render_message_for_transcript(m) for m in msgs))

    kept = list(messages)
    dropped = 0

    # Preserve at least the most-recent message so the giant-message
    # truncation path below can run.
    while len(kept) > 1 and rendered_size(kept) > max_chars:
        kept.pop(0)
        dropped += 1

    if kept and rendered_size(kept) > max_chars:
        tail = kept[-1]
        prefix = "[message truncated] "
        line_overhead = len(f"[{tail.role}]: {prefix}")
        keep_chars = max(max_chars - line_overhead, 0)
        truncated_content = prefix + tail.content[-keep_chars:]

        class _TruncatedMsg:
            __slots__ = ("role", "content", "sequence_index")

            def __init__(self, role, content, sequence_index):
                self.role = role
                self.content = content
                self.sequence_index = sequence_index

        kept[-1] = _TruncatedMsg(tail.role, truncated_content, tail.sequence_index)
        logger.warning(
            "continuity transcript: most-recent message exceeded budget, "
            "truncated content to last %d chars",
            keep_chars,
        )

    if dropped > 0:
        logger.warning(
            "continuity transcript: dropped %d oldest messages to fit budget (%d chars)",
            dropped,
            max_chars,
        )

    return kept, dropped


def _build_transcript(conversation) -> str:
    """Format conversation messages into a compact transcript string.

    Caps total rendered size at MAX_TRANSCRIPT_CHARS by dropping oldest
    messages and prepending a truncation marker. See _truncate_messages_to_budget.

    ``conversation`` must expose ``.messages`` (each with ``.role``,
    ``.content``, ``.sequence_index``).
    """
    sorted_messages = sorted(conversation.messages, key=lambda m: m.sequence_index)
    kept, dropped = _truncate_messages_to_budget(sorted_messages, MAX_TRANSCRIPT_CHARS)
    lines = [_render_message_for_transcript(m) for m in kept]
    if dropped > 0:
        marker = f"[{dropped} earlier messages truncated to fit context]"
        return marker + "\n" + "\n".join(lines)
    return "\n".join(lines)


def _parse_provider_response(raw: str) -> dict:
    """Extract the JSON object from the provider response.

    Tolerates leading/trailing whitespace and optional markdown fencing.
    """
    text = raw.strip()
    # Strip markdown code fences if present
    if text.startswith("```"):
        # Remove first line (```json or ```) and last line (```)
        lines = text.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    return json.loads(text)


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------


def generate_continuity_packet(
    conversation,
    provider: LLMProvider | None,
    store_path: str | Path,
    prompt_version: str = PROMPT_TEMPLATE_VERSION,
) -> ContinuityPacketResult:
    """Generate continuity artifacts from one canonical conversation.

    ``conversation`` must expose ``.id``, ``.title``, and ``.messages``
    (each with ``.role``, ``.content``, ``.sequence_index``).

    Returns a ``ContinuityPacketResult`` with either artifacts or an error.
    Artifacts are persisted to ``store_path`` on success.
    """
    stable_id = f"imported_conversation:{conversation.id}"

    if provider is None:
        return ContinuityPacketResult(
            conversation_stable_id=stable_id,
            artifacts=[],
            error="No LLM provider configured. Set SOULPRINT_LLM_PROVIDER to enable continuity generation.",
        )

    transcript = _build_transcript(conversation)
    user_message = f"--- Transcript ---\n{transcript}"

    try:
        # Continuity packets emit a multi-section JSON structure that can run
        # long; override the 4096 default so the response isn't truncated
        # mid-object and fails JSON parsing.
        raw_response = provider.complete(
            _SYSTEM_PROMPT,
            user_message,
            max_tokens=16384,
            response_format={"type": "json_object"},
        )
    except Exception as exc:
        return ContinuityPacketResult(
            conversation_stable_id=stable_id,
            artifacts=[],
            error=f"Provider call failed: {exc}",
        )

    try:
        parsed = _parse_provider_response(raw_response)
    except (json.JSONDecodeError, ValueError) as exc:
        return ContinuityPacketResult(
            conversation_stable_id=stable_id,
            artifacts=[],
            error=f"Failed to parse provider response as JSON: {exc}",
        )

    timestamp = make_timestamp()
    source_ids = [stable_id]
    provider_name = provider.provider_name
    artifacts: list[ContinuityArtifact] = []

    # -- summary --
    summary_text = parsed.get("summary", "")
    if summary_text:
        artifacts.append(ContinuityArtifact(
            artifact_id=make_artifact_id(),
            artifact_type="summary",
            source_conversation_ids=source_ids,
            generation_timestamp=timestamp,
            llm_provider_used=provider_name,
            prompt_template_version=prompt_version,
            content_text=summary_text,
        ))

    # -- decisions --
    decisions = parsed.get("decisions", [])
    if decisions:
        artifacts.append(ContinuityArtifact(
            artifact_id=make_artifact_id(),
            artifact_type="decisions",
            source_conversation_ids=source_ids,
            generation_timestamp=timestamp,
            llm_provider_used=provider_name,
            prompt_template_version=prompt_version,
            content_text="\n".join(f"- {d}" for d in decisions),
            content_json={"decisions": decisions},
        ))

    # -- open_loops --
    open_loops = parsed.get("open_loops", [])
    if open_loops:
        artifacts.append(ContinuityArtifact(
            artifact_id=make_artifact_id(),
            artifact_type="open_loops",
            source_conversation_ids=source_ids,
            generation_timestamp=timestamp,
            llm_provider_used=provider_name,
            prompt_template_version=prompt_version,
            content_text="\n".join(f"- {o}" for o in open_loops),
            content_json={"open_loops": open_loops},
        ))

    # -- entity_map --
    entity_map = parsed.get("entity_map", [])
    if entity_map:
        artifacts.append(ContinuityArtifact(
            artifact_id=make_artifact_id(),
            artifact_type="entity_map",
            source_conversation_ids=source_ids,
            generation_timestamp=timestamp,
            llm_provider_used=provider_name,
            prompt_template_version=prompt_version,
            content_text=", ".join(entity_map),
            content_json={"entity_map": entity_map},
        ))

    # Persist all artifacts
    path = Path(store_path)
    for artifact in artifacts:
        append_artifact(path, artifact)

    return ContinuityPacketResult(
        conversation_stable_id=stable_id,
        artifacts=artifacts,
    )
